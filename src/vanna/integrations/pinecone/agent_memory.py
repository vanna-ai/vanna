"""
Pinecone vector database implementation of AgentMemory.

This implementation uses Pinecone for cloud-based vector storage of tool usage patterns.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from vanna.core.tool import ToolContext


class PineconeAgentMemory(AgentMemory):
    """Pinecone-based implementation of AgentMemory."""
    
    def __init__(
        self,
        api_key: str,
        index_name: str = "tool-memories",
        environment: str = "us-east-1",
        dimension: int = 384,
        metric: str = "cosine"
    ):
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone is required for PineconeAgentMemory. Install with: pip install pinecone-client")
        
        self.api_key = api_key
        self.index_name = index_name
        self.environment = environment
        self.dimension = dimension
        self.metric = metric
        self._client = None
        self._index = None
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def _get_client(self):
        """Get or create Pinecone client."""
        if self._client is None:
            self._client = Pinecone(api_key=self.api_key)
        return self._client
    
    def _get_index(self):
        """Get or create Pinecone index."""
        if self._index is None:
            client = self._get_client()
            
            # Create index if it doesn't exist
            if self.index_name not in client.list_indexes().names():
                client.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec=ServerlessSpec(cloud="aws", region=self.environment)
                )
            
            self._index = client.Index(self.index_name)
        return self._index
    
    def _create_embedding(self, text: str) -> List[float]:
        """Create a simple embedding from text (placeholder - should use actual embedding model)."""
        # TODO: Replace with actual embedding model
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(hash_val >> i) % 100 / 100.0 for i in range(self.dimension)]
    
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
            index = self._get_index()
            
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            embedding = self._create_embedding(question)
            
            # Pinecone metadata must be simple types
            memory_metadata = {
                "question": question,
                "tool_name": tool_name,
                "args_json": json.dumps(args),
                "timestamp": timestamp,
                "success": success,
                "metadata_json": json.dumps(metadata or {})
            }
            
            index.upsert(vectors=[(memory_id, embedding, memory_metadata)])
        
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
            index = self._get_index()
            
            embedding = self._create_embedding(question)
            
            # Build filter
            filter_dict = {"success": True}
            if tool_name_filter:
                filter_dict["tool_name"] = tool_name_filter
            
            results = index.query(
                vector=embedding,
                top_k=limit,
                filter=filter_dict,
                include_metadata=True
            )
            
            search_results = []
            for i, match in enumerate(results.matches):
                # Pinecone returns similarity score directly
                similarity_score = match.score
                
                if similarity_score >= similarity_threshold:
                    metadata = match.metadata
                    args = json.loads(metadata.get("args_json", "{}"))
                    metadata_dict = json.loads(metadata.get("metadata_json", "{}"))
                    
                    memory = ToolMemory(
                        memory_id=match.id,
                        question=metadata["question"],
                        tool_name=metadata["tool_name"],
                        args=args,
                        timestamp=metadata.get("timestamp"),
                        success=metadata.get("success", True),
                        metadata=metadata_dict
                    )
                    
                    search_results.append(MemorySearchResult(
                        memory=memory,
                        similarity_score=similarity_score,
                        rank=i + 1
                    ))
            
            return search_results
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _search)
    
    async def get_recent_memories(
        self,
        context: ToolContext,
        limit: int = 10
    ) -> List[ToolMemory]:
        """Get recently added memories."""
        def _get_recent():
            index = self._get_index()
            
            # Pinecone doesn't have a native "get all" - we need to query with a dummy vector
            # or use the list operation with metadata filtering
            # This is a limitation - we'll return empty for now
            # In production, you'd maintain a separate timestamp index or use Pinecone's metadata filtering
            return []
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _get_recent)
    
    async def delete_by_id(
        self,
        context: ToolContext,
        memory_id: str
    ) -> bool:
        """Delete a memory by its ID."""
        def _delete():
            index = self._get_index()
            
            try:
                index.delete(ids=[memory_id])
                return True
            except Exception:
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
            index = self._get_index()
            
            # Build filter
            filter_dict = {}
            if tool_name:
                filter_dict["tool_name"] = tool_name
            if before_date:
                filter_dict["timestamp"] = {"$lt": before_date}
            
            if filter_dict:
                # Delete with filter
                index.delete(filter=filter_dict)
            else:
                # Delete all
                index.delete(delete_all=True)
            
            # Pinecone doesn't return count of deleted items
            return 0
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _clear)
