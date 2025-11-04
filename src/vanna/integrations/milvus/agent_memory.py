"""
Milvus vector database implementation of AgentMemory.

This implementation uses Milvus for distributed vector storage of tool usage patterns.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from pymilvus import (
        connections,
        Collection,
        CollectionSchema,
        FieldSchema,
        DataType,
        utility
    )
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False

from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from vanna.core.tool import ToolContext


class MilvusAgentMemory(AgentMemory):
    """Milvus-based implementation of AgentMemory."""
    
    def __init__(
        self,
        collection_name: str = "tool_memories",
        host: str = "localhost",
        port: int = 19530,
        alias: str = "default",
        dimension: int = 384
    ):
        if not MILVUS_AVAILABLE:
            raise ImportError("Milvus is required for MilvusAgentMemory. Install with: pip install pymilvus")
        
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.alias = alias
        self.dimension = dimension
        self._collection = None
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def _get_collection(self):
        """Get or create Milvus collection."""
        if self._collection is None:
            # Connect to Milvus
            connections.connect(alias=self.alias, host=self.host, port=self.port)
            
            # Create collection if it doesn't exist
            if not utility.has_collection(self.collection_name):
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
                    FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=2000),
                    FieldSchema(name="tool_name", dtype=DataType.VARCHAR, max_length=200),
                    FieldSchema(name="args_json", dtype=DataType.VARCHAR, max_length=5000),
                    FieldSchema(name="timestamp", dtype=DataType.VARCHAR, max_length=50),
                    FieldSchema(name="success", dtype=DataType.BOOL),
                    FieldSchema(name="metadata_json", dtype=DataType.VARCHAR, max_length=5000)
                ]
                
                schema = CollectionSchema(fields=fields, description="Tool usage memories")
                collection = Collection(name=self.collection_name, schema=schema)
                
                # Create index for vector field
                index_params = {
                    "index_type": "IVF_FLAT",
                    "metric_type": "IP",
                    "params": {"nlist": 128}
                }
                collection.create_index(field_name="embedding", index_params=index_params)
            
            self._collection = Collection(self.collection_name)
            self._collection.load()
        
        return self._collection
    
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
            collection = self._get_collection()
            
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            embedding = self._create_embedding(question)
            
            entities = [
                [memory_id],
                [embedding],
                [question],
                [tool_name],
                [json.dumps(args)],
                [timestamp],
                [success],
                [json.dumps(metadata or {})]
            ]
            
            collection.insert(entities)
            collection.flush()
        
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
            
            embedding = self._create_embedding(question)
            
            # Build filter expression
            expr = "success == true"
            if tool_name_filter:
                expr += f' && tool_name == "{tool_name_filter}"'
            
            search_params = {"metric_type": "IP", "params": {"nprobe": 10}}
            
            results = collection.search(
                data=[embedding],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                expr=expr,
                output_fields=["id", "question", "tool_name", "args_json", "timestamp", "success", "metadata_json"]
            )
            
            search_results = []
            for i, hits in enumerate(results):
                for j, hit in enumerate(hits):
                    similarity_score = hit.distance
                    
                    if similarity_score >= similarity_threshold:
                        args = json.loads(hit.entity.get("args_json", "{}"))
                        metadata_dict = json.loads(hit.entity.get("metadata_json", "{}"))
                        
                        memory = ToolMemory(
                            memory_id=hit.entity.get("id"),
                            question=hit.entity.get("question"),
                            tool_name=hit.entity.get("tool_name"),
                            args=args,
                            timestamp=hit.entity.get("timestamp"),
                            success=hit.entity.get("success", True),
                            metadata=metadata_dict
                        )
                        
                        search_results.append(MemorySearchResult(
                            memory=memory,
                            similarity_score=similarity_score,
                            rank=j + 1
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
            collection = self._get_collection()
            
            # Query all entries and sort by timestamp
            results = collection.query(
                expr="id != ''",
                output_fields=["id", "question", "tool_name", "args_json", "timestamp", "success", "metadata_json"],
                limit=1000
            )
            
            # Sort by timestamp
            sorted_results = sorted(
                results,
                key=lambda r: r.get("timestamp", ""),
                reverse=True
            )
            
            memories = []
            for result in sorted_results[:limit]:
                args = json.loads(result.get("args_json", "{}"))
                metadata_dict = json.loads(result.get("metadata_json", "{}"))
                
                memory = ToolMemory(
                    memory_id=result.get("id"),
                    question=result.get("question"),
                    tool_name=result.get("tool_name"),
                    args=args,
                    timestamp=result.get("timestamp"),
                    success=result.get("success", True),
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
            collection = self._get_collection()
            
            try:
                expr = f'id == "{memory_id}"'
                collection.delete(expr)
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
            collection = self._get_collection()
            
            # Build filter expression
            expr_parts = []
            if tool_name:
                expr_parts.append(f'tool_name == "{tool_name}"')
            if before_date:
                expr_parts.append(f'timestamp < "{before_date}"')
            
            if expr_parts:
                expr = " && ".join(expr_parts)
            else:
                expr = "id != ''"
            
            collection.delete(expr)
            return 0
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _clear)
