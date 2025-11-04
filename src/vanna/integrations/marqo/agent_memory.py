"""
Marqo vector database implementation of AgentMemory.

This implementation uses Marqo for vector storage of tool usage patterns.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import marqo
    MARQO_AVAILABLE = True
except ImportError:
    MARQO_AVAILABLE = False

from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from vanna.core.tool import ToolContext


class MarqoAgentMemory(AgentMemory):
    """Marqo-based implementation of AgentMemory."""
    
    def __init__(
        self,
        url: str = "http://localhost:8882",
        index_name: str = "tool-memories",
        api_key: Optional[str] = None
    ):
        if not MARQO_AVAILABLE:
            raise ImportError("Marqo is required for MarqoAgentMemory. Install with: pip install marqo")
        
        self.url = url
        self.index_name = index_name
        self.api_key = api_key
        self._client = None
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def _get_client(self):
        """Get or create Marqo client."""
        if self._client is None:
            self._client = marqo.Client(url=self.url, api_key=self.api_key)
            
            # Create index if it doesn't exist
            try:
                self._client.get_index(self.index_name)
            except:
                self._client.create_index(self.index_name)
        
        return self._client
    
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
            
            document = {
                "_id": memory_id,
                "question": question,
                "tool_name": tool_name,
                "args": json.dumps(args),
                "timestamp": timestamp,
                "success": success,
                "metadata": json.dumps(metadata or {})
            }
            
            client.index(self.index_name).add_documents([document], tensor_fields=["question"])
        
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
            
            # Build filter
            filter_string = "success:true"
            if tool_name_filter:
                filter_string += f" AND tool_name:{tool_name_filter}"
            
            results = client.index(self.index_name).search(
                q=question,
                limit=limit,
                filter_string=filter_string
            )
            
            search_results = []
            for i, hit in enumerate(results["hits"]):
                # Marqo returns score
                similarity_score = hit.get("_score", 0)
                
                if similarity_score >= similarity_threshold:
                    args = json.loads(hit.get("args", "{}"))
                    metadata_dict = json.loads(hit.get("metadata", "{}"))
                    
                    memory = ToolMemory(
                        memory_id=hit["_id"],
                        question=hit["question"],
                        tool_name=hit["tool_name"],
                        args=args,
                        timestamp=hit.get("timestamp"),
                        success=hit.get("success", True),
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
            
            # Search with wildcard and sort by timestamp
            results = client.index(self.index_name).search(
                q="*",
                limit=limit,
                sort="timestamp:desc"
            )
            
            memories = []
            for hit in results.get("hits", []):
                args = json.loads(hit.get("args", "{}"))
                metadata_dict = json.loads(hit.get("metadata", "{}"))
                
                memory = ToolMemory(
                    memory_id=hit["_id"],
                    question=hit["question"],
                    tool_name=hit["tool_name"],
                    args=args,
                    timestamp=hit.get("timestamp"),
                    success=hit.get("success", True),
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
            
            try:
                client.index(self.index_name).delete_documents(ids=[memory_id])
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
            
            # Build filter for search
            filter_parts = []
            if tool_name:
                filter_parts.append(f"tool_name:{tool_name}")
            if before_date:
                filter_parts.append(f"timestamp:[* TO {before_date}]")
            
            if filter_parts or (tool_name is None and before_date is None):
                filter_string = " AND ".join(filter_parts) if filter_parts else None
                
                if filter_string:
                    # Search for documents to delete
                    results = client.index(self.index_name).search(
                        q="*",
                        limit=1000,  # Max results
                        filter_string=filter_string
                    )
                    
                    ids_to_delete = [hit["_id"] for hit in results.get("hits", [])]
                    
                    if ids_to_delete:
                        client.index(self.index_name).delete_documents(ids=ids_to_delete)
                    
                    return len(ids_to_delete)
                else:
                    # Delete entire index and recreate
                    try:
                        client.delete_index(self.index_name)
                        client.create_index(self.index_name)
                    except:
                        pass
                    return 0
            
            return 0
        
        return await asyncio.get_event_loop().run_in_executor(self._executor, _clear)
