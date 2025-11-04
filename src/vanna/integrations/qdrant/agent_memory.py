"""
Qdrant vector database implementation of AgentMemory.

This implementation uses Qdrant for vector storage of tool usage patterns.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from vanna.core.tool import ToolContext


class QdrantAgentMemory(AgentMemory):
    """Qdrant-based implementation of AgentMemory."""
    
    def __init__(
        self,
        collection_name: str = "tool_memories",
        url: Optional[str] = None,
        path: Optional[str] = None,
        api_key: Optional[str] = None,
        dimension: int = 384
    ):
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant is required for QdrantAgentMemory. Install with: pip install qdrant-client")
        
        self.collection_name = collection_name
        self.url = url
        self.path = path
        self.api_key = api_key
        self.dimension = dimension
        self._client = None
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def _get_client(self):
        """Get or create Qdrant client."""
        if self._client is None:
            if self.url:
                self._client = QdrantClient(url=self.url, api_key=self.api_key)
            else:
                self._client = QdrantClient(path=self.path or ":memory:")
            
            # Create collection if it doesn't exist
            collections = self._client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE)
                )
        return self._client
    
    def _create_embedding(self, text: str) -> List[float]:
        """Create a simple embedding from text (placeholder)."""
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
            client = self._get_client()
            
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            embedding = self._create_embedding(question)
            
            payload = {
                "question": question,
                "tool_name": tool_name,
                "args": args,
                "timestamp": timestamp,
                "success": success,
                "metadata": metadata or {}
            }
            
            point = PointStruct(
                id=memory_id,
                vector=embedding,
                payload=payload
            )
            
            client.upsert(
                collection_name=self.collection_name,
                points=[point]
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
            client = self._get_client()
            
            embedding = self._create_embedding(question)
            
            # Build filter
            query_filter = None
            conditions = [FieldCondition(key="success", match=MatchValue(value=True))]
            if tool_name_filter:
                conditions.append(FieldCondition(key="tool_name", match=MatchValue(value=tool_name_filter)))
            
            if conditions:
                query_filter = Filter(must=conditions)
            
            results = client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=limit,
                query_filter=query_filter,
                score_threshold=similarity_threshold
            )
            
            search_results = []
            for i, hit in enumerate(results):
                payload = hit.payload
                
                memory = ToolMemory(
                    memory_id=str(hit.id),
                    question=payload["question"],
                    tool_name=payload["tool_name"],
                    args=payload["args"],
                    timestamp=payload.get("timestamp"),
                    success=payload.get("success", True),
                    metadata=payload.get("metadata", {})
                )
                
                search_results.append(MemorySearchResult(
                    memory=memory,
                    similarity_score=hit.score,
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
            client = self._get_client()
            
            # Scroll through all points and sort by timestamp
            points, _ = client.scroll(
                collection_name=self.collection_name,
                limit=1000,  # Get more than we need to sort
                with_payload=True,
                with_vectors=False
            )
            
            # Sort by timestamp
            sorted_points = sorted(
                points,
                key=lambda p: p.payload.get("timestamp", ""),
                reverse=True
            )
            
            memories = []
            for point in sorted_points[:limit]:
                payload = point.payload
                memory = ToolMemory(
                    memory_id=str(point.id),
                    question=payload["question"],
                    tool_name=payload["tool_name"],
                    args=payload["args"],
                    timestamp=payload.get("timestamp"),
                    success=payload.get("success", True),
                    metadata=payload.get("metadata", {})
                )
                memories.append(memory)
            
            return memories
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _get_recent)
    
    async def delete_by_id(
        self,
        context: ToolContext,
        memory_id: str
    ) -> bool:
        """Delete a memory by its ID. Returns True if deleted, False if not found."""
        def _delete():
            client = self._get_client()

            try:
                # Check if the point exists before attempting to delete
                points = client.retrieve(
                    collection_name=self.collection_name,
                    ids=[memory_id],
                    with_payload=False,
                    with_vectors=False
                )

                if points and len(points) > 0:
                    client.delete(
                        collection_name=self.collection_name,
                        points_selector=[memory_id]
                    )
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
            client = self._get_client()
            
            # Build filter
            conditions = []
            if tool_name:
                conditions.append(FieldCondition(key="tool_name", match=MatchValue(value=tool_name)))
            if before_date:
                conditions.append(FieldCondition(key="timestamp", match=MatchValue(value=before_date)))
            
            if conditions or (tool_name is None and before_date is None):
                # Delete with filter or delete all
                query_filter = Filter(must=conditions) if conditions else None
                
                if query_filter:
                    client.delete(
                        collection_name=self.collection_name,
                        points_selector=query_filter
                    )
                else:
                    # Delete all points
                    client.delete_collection(collection_name=self.collection_name)
                    # Recreate empty collection
                    client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE)
                    )
            
            return 0  # Qdrant doesn't return count
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _clear)
