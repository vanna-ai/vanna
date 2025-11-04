"""
Azure AI Search implementation of AgentMemory.

This implementation uses Azure Cognitive Search for vector storage of tool usage patterns.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        SearchIndex,
        SearchField,
        SearchFieldDataType,
        VectorSearch,
        VectorSearchAlgorithmConfiguration,
    )
    from azure.core.credentials import AzureKeyCredential
    AZURE_SEARCH_AVAILABLE = True
except ImportError:
    AZURE_SEARCH_AVAILABLE = False

from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from vanna.core.tool import ToolContext


class AzureAISearchAgentMemory(AgentMemory):
    """Azure AI Search-based implementation of AgentMemory."""
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        index_name: str = "tool-memories",
        dimension: int = 384
    ):
        if not AZURE_SEARCH_AVAILABLE:
            raise ImportError(
                "Azure Search is required for AzureAISearchAgentMemory. "
                "Install with: pip install azure-search-documents"
            )
        
        self.endpoint = endpoint
        self.api_key = api_key
        self.index_name = index_name
        self.dimension = dimension
        self._credential = AzureKeyCredential(api_key)
        self._search_client = None
        self._index_client = None
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def _get_index_client(self):
        """Get or create index client."""
        if self._index_client is None:
            self._index_client = SearchIndexClient(
                endpoint=self.endpoint,
                credential=self._credential
            )
            self._ensure_index_exists()
        return self._index_client
    
    def _get_search_client(self):
        """Get or create search client."""
        if self._search_client is None:
            self._get_index_client()  # Ensure index exists
            self._search_client = SearchClient(
                endpoint=self.endpoint,
                index_name=self.index_name,
                credential=self._credential
            )
        return self._search_client
    
    def _ensure_index_exists(self):
        """Create index if it doesn't exist."""
        try:
            self._index_client.get_index(self.index_name)
        except:
            # Create index with vector search configuration
            fields = [
                SearchField(name="memory_id", type=SearchFieldDataType.String, key=True),
                SearchField(name="question", type=SearchFieldDataType.String, searchable=True),
                SearchField(name="tool_name", type=SearchFieldDataType.String, filterable=True),
                SearchField(name="args_json", type=SearchFieldDataType.String),
                SearchField(name="timestamp", type=SearchFieldDataType.String, sortable=True, filterable=True),
                SearchField(name="success", type=SearchFieldDataType.Boolean, filterable=True),
                SearchField(name="metadata_json", type=SearchFieldDataType.String),
                SearchField(
                    name="embedding",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=self.dimension,
                    vector_search_configuration="vector-config"
                ),
            ]
            
            vector_search = VectorSearch(
                algorithm_configurations=[
                    VectorSearchAlgorithmConfiguration(name="vector-config")
                ]
            )
            
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search
            )
            
            self._index_client.create_index(index)
    
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
            client = self._get_search_client()
            
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            embedding = self._create_embedding(question)
            
            document = {
                "memory_id": memory_id,
                "question": question,
                "tool_name": tool_name,
                "args_json": json.dumps(args),
                "timestamp": timestamp,
                "success": success,
                "metadata_json": json.dumps(metadata or {}),
                "embedding": embedding
            }
            
            client.upload_documents(documents=[document])
        
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
            client = self._get_search_client()
            
            embedding = self._create_embedding(question)
            
            # Build filter
            filter_expr = "success eq true"
            if tool_name_filter:
                filter_expr += f" and tool_name eq '{tool_name_filter}'"
            
            results = client.search(
                search_text=None,
                vector=embedding,
                top_k=limit,
                filter=filter_expr
            )
            
            search_results = []
            for i, doc in enumerate(results):
                # Azure returns similarity score in @search.score
                similarity_score = doc.get("@search.score", 0)
                
                if similarity_score >= similarity_threshold:
                    args = json.loads(doc.get("args_json", "{}"))
                    metadata_dict = json.loads(doc.get("metadata_json", "{}"))
                    
                    memory = ToolMemory(
                        memory_id=doc["memory_id"],
                        question=doc["question"],
                        tool_name=doc["tool_name"],
                        args=args,
                        timestamp=doc.get("timestamp"),
                        success=doc.get("success", True),
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
            client = self._get_search_client()
            
            results = client.search(
                search_text="*",
                top=limit,
                order_by=["timestamp desc"]
            )
            
            memories = []
            for doc in results:
                args = json.loads(doc.get("args_json", "{}"))
                metadata_dict = json.loads(doc.get("metadata_json", "{}"))
                
                memory = ToolMemory(
                    memory_id=doc["memory_id"],
                    question=doc["question"],
                    tool_name=doc["tool_name"],
                    args=args,
                    timestamp=doc.get("timestamp"),
                    success=doc.get("success", True),
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
            client = self._get_search_client()
            
            try:
                client.delete_documents(documents=[{"memory_id": memory_id}])
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
            client = self._get_search_client()
            
            # Build filter
            filter_parts = []
            if tool_name:
                filter_parts.append(f"tool_name eq '{tool_name}'")
            if before_date:
                filter_parts.append(f"timestamp lt '{before_date}'")
            
            filter_expr = " and ".join(filter_parts) if filter_parts else None
            
            # Search for documents to delete
            results = client.search(
                search_text="*",
                filter=filter_expr,
                select=["memory_id"]
            )
            
            docs_to_delete = [{"memory_id": doc["memory_id"]} for doc in results]
            
            if docs_to_delete:
                client.delete_documents(documents=docs_to_delete)
            
            return len(docs_to_delete)
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _clear)
