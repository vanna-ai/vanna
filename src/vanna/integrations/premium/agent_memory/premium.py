"""
Cloud-based implementation of AgentMemory.

This implementation uses Vanna's premium cloud service for storing and searching
tool usage patterns with advanced similarity search and analytics.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx

from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from vanna.core.tool import ToolContext


class CloudAgentMemory(AgentMemory):
    """Cloud-based implementation of AgentMemory."""
    
    def __init__(
        self,
        api_base_url: str = "https://api.vanna.ai",
        api_key: Optional[str] = None,
        organization_id: Optional[str] = None
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.api_key = api_key
        self.organization_id = organization_id
        self._client = httpx.AsyncClient(
            base_url=self.api_base_url,
            timeout=30.0
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.organization_id:
            headers["X-Organization-ID"] = self.organization_id
        return headers
    
    async def save_tool_usage(
        self,
        question: str,
        tool_name: str,
        args: Dict[str, Any],
        context: ToolContext,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save a tool usage pattern to premium cloud storage."""
        payload = {
            "question": question,
            "tool_name": tool_name,
            "args": args,
            "success": success,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        response = await self._client.post(
            "/memory/tool-usage",
            json=payload,
            headers=self._get_headers()
        )
        response.raise_for_status()
    
    async def search_similar_usage(
        self,
        question: str,
        context: ToolContext,
        *,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        tool_name_filter: Optional[str] = None
    ) -> List[MemorySearchResult]:
        """Search for similar tool usage patterns in premium cloud storage."""
        params = {
            "question": question,
            "limit": limit,
            "similarity_threshold": similarity_threshold
        }
        if tool_name_filter:
            params["tool_name_filter"] = tool_name_filter
        
        response = await self._client.get(
            "/memory/search-similar",
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for item in data.get("results", []):
            memory = ToolMemory(**item["memory"])
            result = MemorySearchResult(
                memory=memory,
                similarity_score=item["similarity_score"],
                rank=item["rank"]
            )
            results.append(result)
        
        return results
    
    async def get_tool_usage_stats(
        self,
        context: ToolContext,
        tool_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get usage statistics from premium cloud storage."""
        params = {}
        if tool_name:
            params["tool_name"] = tool_name
        
        response = await self._client.get(
            "/memory/stats",
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        return response.json()
    
    async def clear_memories(
        self,
        context: ToolContext,
        tool_name: Optional[str] = None,
        before_date: Optional[str] = None
    ) -> int:
        """Clear stored memories from premium cloud storage."""
        payload = {}
        if tool_name:
            payload["tool_name"] = tool_name
        if before_date:
            payload["before_date"] = before_date
        
        response = await self._client.delete(
            "/memory/clear",
            json=payload,
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("deleted_count", 0)
    
    async def list_tools_with_memories(
        self,
        context: ToolContext
    ) -> List[str]:
        """List all tool names that have stored memories in premium cloud storage."""
        response = await self._client.get(
            "/memory/tools",
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("tools", [])