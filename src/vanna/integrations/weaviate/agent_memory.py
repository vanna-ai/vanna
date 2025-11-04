"""
Weaviate vector database implementation of AgentMemory.

This implementation uses Weaviate for semantic search and storage of tool usage patterns.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import weaviate
    from weaviate.classes.config import Configure, Property, DataType as WeaviateDataType
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False

from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from vanna.core.tool import ToolContext


class WeaviateAgentMemory(AgentMemory):
    """Weaviate-based implementation of AgentMemory."""
    
    def __init__(
        self,
        collection_name: str = "ToolMemory",
        url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        dimension: int = 384
    ):
        if not WEAVIATE_AVAILABLE:
            raise ImportError("Weaviate is required for WeaviateAgentMemory. Install with: pip install weaviate-client")
        
        self.collection_name = collection_name
        self.url = url
        self.api_key = api_key
        self.dimension = dimension
        self._client = None
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def _get_client(self):
        """Get or create Weaviate client."""
        if self._client is None:
            if self.api_key:
                self._client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=self.url,
                    auth_credentials=weaviate.auth.AuthApiKey(self.api_key)
                )
            else:
                self._client = weaviate.connect_to_local(host=self.url.replace("http://", "").replace("https://", ""))
            
            # Create collection if it doesn't exist
            if not self._client.collections.exists(self.collection_name):
                self._client.collections.create(
                    name=self.collection_name,
                    vectorizer_config=Configure.Vectorizer.none(),
                    properties=[
                        Property(name="question", data_type=WeaviateDataType.TEXT),
                        Property(name="tool_name", data_type=WeaviateDataType.TEXT),
                        Property(name="args_json", data_type=WeaviateDataType.TEXT),
                        Property(name="timestamp", data_type=WeaviateDataType.TEXT),
                        Property(name="success", data_type=WeaviateDataType.BOOL),
                        Property(name="metadata_json", data_type=WeaviateDataType.TEXT)
                    ]
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
            collection = client.collections.get(self.collection_name)
            
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            embedding = self._create_embedding(question)
            
            properties = {
                "question": question,
                "tool_name": tool_name,
                "args_json": json.dumps(args),
                "timestamp": timestamp,
                "success": success,
                "metadata_json": json.dumps(metadata or {})
            }
            
            collection.data.insert(
                properties=properties,
                vector=embedding,
                uuid=memory_id
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
            collection = client.collections.get(self.collection_name)
            
            embedding = self._create_embedding(question)
            
            # Build filter
            filters = weaviate.classes.query.Filter.by_property("success").equal(True)
            if tool_name_filter:
                filters = filters & weaviate.classes.query.Filter.by_property("tool_name").equal(tool_name_filter)
            
            response = collection.query.near_vector(
                near_vector=embedding,
                limit=limit,
                filters=filters,
                return_metadata=weaviate.classes.query.MetadataQuery(distance=True)
            )
            
            search_results = []
            for i, obj in enumerate(response.objects):
                # Weaviate returns distance, convert to similarity
                distance = obj.metadata.distance if obj.metadata else 1.0
                similarity_score = 1 - distance
                
                if similarity_score >= similarity_threshold:
                    properties = obj.properties
                    args = json.loads(properties.get("args_json", "{}"))
                    metadata_dict = json.loads(properties.get("metadata_json", "{}"))
                    
                    memory = ToolMemory(
                        memory_id=str(obj.uuid),
                        question=properties.get("question"),
                        tool_name=properties.get("tool_name"),
                        args=args,
                        timestamp=properties.get("timestamp"),
                        success=properties.get("success", True),
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
            client = self._get_client()
            collection = client.collections.get(self.collection_name)
            
            # Query and sort by timestamp
            response = collection.query.fetch_objects(limit=1000)
            
            # Convert to list and sort
            objects_list = list(response.objects)
            sorted_objects = sorted(
                objects_list,
                key=lambda o: o.properties.get("timestamp", ""),
                reverse=True
            )
            
            memories = []
            for obj in sorted_objects[:limit]:
                properties = obj.properties
                args = json.loads(properties.get("args_json", "{}"))
                metadata_dict = json.loads(properties.get("metadata_json", "{}"))
                
                memory = ToolMemory(
                    memory_id=str(obj.uuid),
                    question=properties.get("question"),
                    tool_name=properties.get("tool_name"),
                    args=args,
                    timestamp=properties.get("timestamp"),
                    success=properties.get("success", True),
                    metadata=metadata_dict
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
            client = self._get_client()
            collection = client.collections.get(self.collection_name)
            
            try:
                collection.data.delete_by_id(uuid=memory_id)
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
            client = self._get_client()
            collection = client.collections.get(self.collection_name)
            
            # Build filter
            if tool_name and before_date:
                filters = (
                    weaviate.classes.query.Filter.by_property("tool_name").equal(tool_name) &
                    weaviate.classes.query.Filter.by_property("timestamp").less_than(before_date)
                )
            elif tool_name:
                filters = weaviate.classes.query.Filter.by_property("tool_name").equal(tool_name)
            elif before_date:
                filters = weaviate.classes.query.Filter.by_property("timestamp").less_than(before_date)
            else:
                filters = None
            
            if filters:
                collection.data.delete_many(where=filters)
            else:
                # Delete all
                collection.data.delete_many(where=weaviate.classes.query.Filter.by_property("success").contains_any([True, False]))
            
            return 0
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _clear)
