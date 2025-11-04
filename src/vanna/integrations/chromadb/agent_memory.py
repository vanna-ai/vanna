"""
Local vector database implementation of AgentMemory.

This implementation uses ChromaDB for local vector storage of tool usage patterns.
"""

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from vanna.core.tool import ToolContext


class ChromaAgentMemory(AgentMemory):
    """ChromaDB-based implementation of AgentMemory."""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_memory",
        collection_name: str = "tool_memories",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is required for ChromaAgentMemory. Install with: pip install chromadb")
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self._client = None
        self._collection = None
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def _get_client(self):
        """Get or create ChromaDB client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        return self._client
    
    def _get_collection(self):
        """Get or create ChromaDB collection."""
        if self._collection is None:
            client = self._get_client()
            try:
                self._collection = client.get_collection(name=self.collection_name)
            except Exception:
                self._collection = client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Tool usage memories for learning"}
                )
        return self._collection
    
    def _create_memory_id(self) -> str:
        """Create a unique ID for a memory."""
        import uuid
        return str(uuid.uuid4())
    
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
            collection = self._get_collection()
            
            memory_id = self._create_memory_id()
            timestamp = datetime.now().isoformat()
            
            # ChromaDB only accepts primitive types in metadata
            # Serialize complex objects to JSON strings
            memory_data = {
                "question": question,
                "tool_name": tool_name,
                "args_json": json.dumps(args),  # Serialize to JSON string
                "timestamp": timestamp,
                "success": success,
                "metadata_json": json.dumps(metadata or {})  # Serialize metadata too
            }
            
            # Use question as document text for embedding
            collection.upsert(
                ids=[memory_id],
                documents=[question],
                metadatas=[memory_data]
            )
        
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
            collection = self._get_collection()
            
            # Prepare where filter - ChromaDB requires $and for multiple conditions
            if tool_name_filter:
                where_filter = {
                    "$and": [
                        {"success": True},
                        {"tool_name": tool_name_filter}
                    ]
                }
            else:
                where_filter = {"success": True}
            
            results = collection.query(
                query_texts=[question],
                n_results=limit,
                where=where_filter
            )
            
            search_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i, (id_, distance, metadata) in enumerate(zip(
                    results["ids"][0],
                    results["distances"][0],
                    results["metadatas"][0]
                )):
                    # Convert distance to similarity score (ChromaDB uses L2 distance)
                    similarity_score = max(0, 1 - distance)
                    
                    if similarity_score >= similarity_threshold:
                        # Deserialize JSON fields
                        args = json.loads(metadata.get("args_json", "{}"))
                        metadata_dict = json.loads(metadata.get("metadata_json", "{}"))
                        
                        # Use the ChromaDB document ID as the memory ID
                        memory = ToolMemory(
                            memory_id=id_,
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
        """Get recently added memories. Returns most recent memories first."""
        def _get_recent():
            collection = self._get_collection()
            
            # Get all memories and sort by timestamp
            results = collection.get()
            
            if not results["metadatas"] or not results["ids"]:
                return []
            
            # Parse and sort by timestamp
            memories_with_time = []
            for i, (doc_id, metadata) in enumerate(zip(results["ids"], results["metadatas"])):
                args = json.loads(metadata.get("args_json", "{}"))
                metadata_dict = json.loads(metadata.get("metadata_json", "{}"))
                
                # Use the ChromaDB document ID as the memory ID
                memory = ToolMemory(
                    memory_id=doc_id,
                    question=metadata["question"],
                    tool_name=metadata["tool_name"],
                    args=args,
                    timestamp=metadata.get("timestamp"),
                    success=metadata.get("success", True),
                    metadata=metadata_dict
                )
                memories_with_time.append((memory, metadata.get("timestamp", "")))
            
            # Sort by timestamp descending (most recent first)
            memories_with_time.sort(key=lambda x: x[1], reverse=True)
            
            # Return only the memory objects, limited to the requested amount
            return [m[0] for m in memories_with_time[:limit]]
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _get_recent)
    
    async def delete_by_id(
        self,
        context: ToolContext,
        memory_id: str
    ) -> bool:
        """Delete a memory by its ID. Returns True if deleted, False if not found."""
        def _delete():
            collection = self._get_collection()
            
            # Check if the ID exists
            try:
                results = collection.get(ids=[memory_id])
                if results["ids"] and len(results["ids"]) > 0:
                    collection.delete(ids=[memory_id])
                    return True
                return False
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
            collection = self._get_collection()
            
            # Build where filter
            where_filter = {}
            if tool_name:
                where_filter["tool_name"] = tool_name
            
            # Get memories to delete
            results = collection.get(where=where_filter if where_filter else None)
            
            if not results["ids"]:
                return 0
            
            ids_to_delete = []
            for i, metadata in enumerate(results["metadatas"]):
                if before_date:
                    memory_date = metadata.get("timestamp", "")
                    if memory_date and memory_date < before_date:
                        ids_to_delete.append(results["ids"][i])
                else:
                    ids_to_delete.append(results["ids"][i])
            
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
            
            return len(ids_to_delete)
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _clear)