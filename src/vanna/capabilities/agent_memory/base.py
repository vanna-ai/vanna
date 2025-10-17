"""
Agent memory capability interface for tool usage learning.

This module contains the abstract base class for agent memory operations,
following the same pattern as the FileSystem interface.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional, Dict, Any
from pydantic import BaseModel

if TYPE_CHECKING:
    from vanna.core.tool import ToolContext


class ToolMemory(BaseModel):
    """Represents a stored tool usage memory."""
    question: str
    tool_name: str
    args: Dict[str, Any]
    timestamp: Optional[str] = None
    success: bool = True
    metadata: Optional[Dict[str, Any]] = None


class MemorySearchResult(BaseModel):
    """Represents a search result from memory storage."""
    memory: ToolMemory
    similarity_score: float
    rank: int


class AgentMemory(ABC):
    """Abstract base class for agent memory operations."""

    @abstractmethod
    async def save_tool_usage(
        self, 
        question: str, 
        tool_name: str, 
        args: Dict[str, Any], 
        context: "ToolContext",
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save a tool usage pattern for future reference."""
        pass

    @abstractmethod
    async def search_similar_usage(
        self,
        question: str,
        context: "ToolContext",
        *,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        tool_name_filter: Optional[str] = None
    ) -> List[MemorySearchResult]:
        """Search for similar tool usage patterns based on a question."""
        pass

    @abstractmethod
    async def get_tool_usage_stats(
        self,
        context: "ToolContext",
        tool_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get usage statistics for tools."""
        pass

    @abstractmethod
    async def clear_memories(
        self,
        context: "ToolContext",
        tool_name: Optional[str] = None,
        before_date: Optional[str] = None
    ) -> int:
        """Clear stored memories. Returns number of memories deleted."""
        pass

    @abstractmethod
    async def list_tools_with_memories(
        self,
        context: "ToolContext"
    ) -> List[str]:
        """List all tool names that have stored memories."""
        pass