"""
Agent memory capability interface for tool usage learning.

This module contains the abstract base class for agent memory operations,
following the same pattern as the FileSystem interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional, Dict, Any

if TYPE_CHECKING:
    from vanna.core.tool import ToolContext
    from .models import ToolMemory, MemorySearchResult


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
    async def get_recent_memories(
        self,
        context: "ToolContext",
        limit: int = 10
    ) -> List[ToolMemory]:
        """Get recently added memories. Returns most recent memories first."""
        pass

    @abstractmethod
    async def delete_by_id(
        self,
        context: "ToolContext",
        memory_id: str
    ) -> bool:
        """Delete a memory by its ID. Returns True if deleted, False if not found."""
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