"""
FAISS vector database implementation of AgentMemory.

This implementation uses FAISS for local vector storage of tool usage patterns.
"""

import json
import uuid
import pickle
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from vanna.core.tool import ToolContext


class FAISSAgentMemory(AgentMemory):
    """FAISS-based implementation of AgentMemory."""
    
    def __init__(
        self,
        index_path: Optional[str] = None,
        persist_path: Optional[str] = None,
        dimension: int = 384,
        metric: str = "cosine"
    ):
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS is required for FAISSAgentMemory. Install with: pip install faiss-cpu")

        # Accept either index_path or persist_path for backward compatibility
        self.index_path = persist_path or index_path or "./faiss_index"
        self.dimension = dimension
        self.metric = metric
        self._index = None
        self._metadata = {}
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._load_index()
    
    def _load_index(self):
        """Load or create FAISS index."""
        index_file = os.path.join(self.index_path, "index.faiss")
        metadata_file = os.path.join(self.index_path, "metadata.pkl")
        
        if os.path.exists(index_file) and os.path.exists(metadata_file):
            # Load existing index
            self._index = faiss.read_index(index_file)
            with open(metadata_file, "rb") as f:
                self._metadata = pickle.load(f)
        else:
            # Create new index
            os.makedirs(self.index_path, exist_ok=True)
            if self.metric == "cosine":
                self._index = faiss.IndexFlatIP(self.dimension)
            else:
                self._index = faiss.IndexFlatL2(self.dimension)
            self._metadata = {}
    
    def _save_index(self):
        """Save FAISS index to disk."""
        index_file = os.path.join(self.index_path, "index.faiss")
        metadata_file = os.path.join(self.index_path, "metadata.pkl")
        
        faiss.write_index(self._index, index_file)
        with open(metadata_file, "wb") as f:
            pickle.dump(self._metadata, f)
    
    def _create_embedding(self, text: str) -> np.ndarray:
        """Create a simple embedding from text (placeholder)."""
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        embedding = np.array([(hash_val >> i) % 100 / 100.0 for i in range(self.dimension)], dtype=np.float32)
        
        # Normalize for cosine similarity
        if self.metric == "cosine":
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
        
        return embedding
    
    async def save_tool_usage(
        self,
        question: str,
        tool_name: str,
        args: Dict[str, Any],
        context: ToolContext,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save a tool usage pattern."""
        def _save():
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            embedding = self._create_embedding(question)
            
            # Add to FAISS index
            self._index.add(np.array([embedding]))
            
            # Store metadata
            idx = self._index.ntotal - 1
            self._metadata[idx] = {
                "memory_id": memory_id,
                "question": question,
                "tool_name": tool_name,
                "args": args,
                "timestamp": timestamp,
                "success": success,
                "metadata": metadata or {}
            }
            
            self._save_index()
        
        await asyncio.get_event_loop().run_in_executor(self._executor, _save)
    
    async def search_similar_usage(
        self,
        question: str,
        context: ToolContext,
        *,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        tool_name_filter: Optional[str] = None
    ) -> List[MemorySearchResult]:
        """Search for similar tool usage patterns."""
        def _search():
            embedding = self._create_embedding(question)
            
            # Search in FAISS
            k = min(limit * 3, self._index.ntotal) if self._index.ntotal > 0 else 1
            if k == 0:
                return []
            
            distances, indices = self._index.search(np.array([embedding]), k)
            
            search_results = []
            rank = 1
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1 or idx not in self._metadata:
                    continue
                
                metadata = self._metadata[idx]
                
                # Filter by success
                if not metadata.get("success", True):
                    continue
                
                # Filter by tool name
                if tool_name_filter and metadata.get("tool_name") != tool_name_filter:
                    continue
                
                # Convert distance to similarity score
                if self.metric == "cosine":
                    similarity_score = float(dist)
                else:
                    similarity_score = 1.0 / (1.0 + float(dist))
                
                if similarity_score >= similarity_threshold:
                    memory = ToolMemory(
                        memory_id=metadata["memory_id"],
                        question=metadata["question"],
                        tool_name=metadata["tool_name"],
                        args=metadata["args"],
                        timestamp=metadata.get("timestamp"),
                        success=metadata.get("success", True),
                        metadata=metadata.get("metadata", {})
                    )
                    
                    search_results.append(MemorySearchResult(
                        memory=memory,
                        similarity_score=similarity_score,
                        rank=rank
                    ))
                    rank += 1
                    
                    if len(search_results) >= limit:
                        break
            
            return search_results
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _search)
    
    async def get_recent_memories(
        self,
        context: ToolContext,
        limit: int = 10
    ) -> List[ToolMemory]:
        """Get recently added memories."""
        def _get_recent():
            # Get all metadata entries and sort by timestamp
            all_entries = list(self._metadata.values())
            sorted_entries = sorted(
                all_entries,
                key=lambda m: m.get("timestamp", ""),
                reverse=True
            )
            
            memories = []
            for entry in sorted_entries[:limit]:
                memory = ToolMemory(
                    memory_id=entry["memory_id"],
                    question=entry["question"],
                    tool_name=entry["tool_name"],
                    args=entry["args"],
                    timestamp=entry.get("timestamp"),
                    success=entry.get("success", True),
                    metadata=entry.get("metadata", {})
                )
                memories.append(memory)
            
            return memories
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _get_recent)
    
    async def delete_by_id(
        self,
        context: ToolContext,
        memory_id: str
    ) -> bool:
        """Delete a memory by its ID."""
        def _delete():
            # Find and remove from metadata
            idx_to_remove = None
            for idx, metadata in self._metadata.items():
                if metadata["memory_id"] == memory_id:
                    idx_to_remove = idx
                    break
            
            if idx_to_remove is not None:
                del self._metadata[idx_to_remove]
                self._save_index()
                return True
            
            return False
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _delete)
    
    async def clear_memories(
        self,
        context: ToolContext,
        tool_name: Optional[str] = None,
        before_date: Optional[str] = None
    ) -> int:
        """Clear stored memories."""
        def _clear():
            indices_to_remove = []
            
            for idx, metadata in self._metadata.items():
                should_remove = True
                
                if tool_name and metadata.get("tool_name") != tool_name:
                    should_remove = False
                
                if before_date and metadata.get("timestamp", "") >= before_date:
                    should_remove = False
                
                if should_remove:
                    indices_to_remove.append(idx)
            
            # Remove from metadata
            for idx in indices_to_remove:
                del self._metadata[idx]
            
            # If clearing all, recreate index
            if not tool_name and not before_date:
                if self.metric == "cosine":
                    self._index = faiss.IndexFlatIP(self.dimension)
                else:
                    self._index = faiss.IndexFlatL2(self.dimension)
                self._metadata = {}
            
            self._save_index()
            return len(indices_to_remove)
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _clear)
