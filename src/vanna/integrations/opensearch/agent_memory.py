"""
OpenSearch vector database implementation of AgentMemory.

This implementation uses OpenSearch for distributed search and storage of tool usage patterns.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from opensearchpy import OpenSearch, helpers
    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False

from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from vanna.core.tool import ToolContext


class OpenSearchAgentMemory(AgentMemory):
    """OpenSearch-based implementation of AgentMemory."""
    
    def __init__(
        self,
        index_name: str = "tool_memories",
        hosts: Optional[List[str]] = None,
        http_auth: Optional[tuple] = None,
        use_ssl: bool = False,
        verify_certs: bool = False,
        dimension: int = 384
    ):
        if not OPENSEARCH_AVAILABLE:
            raise ImportError("OpenSearch is required for OpenSearchAgentMemory. Install with: pip install opensearch-py")
        
        self.index_name = index_name
        self.hosts = hosts or ["localhost:9200"]
        self.http_auth = http_auth
        self.use_ssl = use_ssl
        self.verify_certs = verify_certs
        self.dimension = dimension
        self._client = None
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def _get_client(self):
        """Get or create OpenSearch client."""
        if self._client is None:
            self._client = OpenSearch(
                hosts=self.hosts,
                http_auth=self.http_auth,
                use_ssl=self.use_ssl,
                verify_certs=self.verify_certs,
                ssl_show_warn=False
            )
            
            # Create index if it doesn't exist
            if not self._client.indices.exists(index=self.index_name):
                index_body = {
                    "settings": {
                        "index": {
                            "knn": True,
                            "knn.algo_param.ef_search": 100
                        }
                    },
                    "mappings": {
                        "properties": {
                            "memory_id": {"type": "keyword"},
                            "question": {"type": "text"},
                            "tool_name": {"type": "keyword"},
                            "args": {"type": "object", "enabled": False},
                            "timestamp": {"type": "date"},
                            "success": {"type": "boolean"},
                            "metadata": {"type": "object", "enabled": False},
                            "embedding": {
                                "type": "knn_vector",
                                "dimension": self.dimension,
                                "method": {
                                    "name": "hnsw",
                                    "space_type": "cosinesimil",
                                    "engine": "nmslib"
                                }
                            }
                        }
                    }
                }
                self._client.indices.create(index=self.index_name, body=index_body)
        
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
            
            document = {
                "memory_id": memory_id,
                "question": question,
                "tool_name": tool_name,
                "args": args,
                "timestamp": timestamp,
                "success": success,
                "metadata": metadata or {},
                "embedding": embedding
            }
            
            client.index(
                index=self.index_name,
                body=document,
                id=memory_id,
                refresh=True
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
            
            # Build query
            must_conditions = [{"term": {"success": True}}]
            if tool_name_filter:
                must_conditions.append({"term": {"tool_name": tool_name_filter}})
            
            query = {
                "size": limit,
                "query": {
                    "bool": {
                        "must": must_conditions,
                        "filter": {
                            "knn": {
                                "embedding": {
                                    "vector": embedding,
                                    "k": limit
                                }
                            }
                        }
                    }
                }
            }
            
            response = client.search(index=self.index_name, body=query)
            
            search_results = []
            for i, hit in enumerate(response["hits"]["hits"]):
                source = hit["_source"]
                score = hit["_score"]
                
                # Normalize score to 0-1 range (OpenSearch scores can vary)
                similarity_score = min(score / 10.0, 1.0)
                
                if similarity_score >= similarity_threshold:
                    memory = ToolMemory(
                        memory_id=source["memory_id"],
                        question=source["question"],
                        tool_name=source["tool_name"],
                        args=source["args"],
                        timestamp=source.get("timestamp"),
                        success=source.get("success", True),
                        metadata=source.get("metadata", {})
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
            
            query = {
                "size": limit,
                "query": {"match_all": {}},
                "sort": [{"timestamp": {"order": "desc"}}]
            }
            
            response = client.search(index=self.index_name, body=query)
            
            memories = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                
                memory = ToolMemory(
                    memory_id=source["memory_id"],
                    question=source["question"],
                    tool_name=source["tool_name"],
                    args=source["args"],
                    timestamp=source.get("timestamp"),
                    success=source.get("success", True),
                    metadata=source.get("metadata", {})
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
            
            try:
                client.delete(index=self.index_name, id=memory_id, refresh=True)
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
            
            # Build query
            must_conditions = []
            if tool_name:
                must_conditions.append({"term": {"tool_name": tool_name}})
            if before_date:
                must_conditions.append({"range": {"timestamp": {"lt": before_date}}})
            
            if must_conditions:
                query = {"query": {"bool": {"must": must_conditions}}}
            else:
                query = {"query": {"match_all": {}}}
            
            response = client.delete_by_query(
                index=self.index_name,
                body=query,
                refresh=True
            )
            
            return response.get("deleted", 0)
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _clear)
