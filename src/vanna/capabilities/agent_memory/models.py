"""
Memory storage models and types.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ToolMemory(BaseModel):
    """Represents a stored tool usage memory."""

    memory_id: Optional[str] = None
    question: str
    tool_name: str
    args: Dict[str, Any]
    timestamp: Optional[str] = None
    success: bool = True
    metadata: Optional[Dict[str, Any]] = None


class TextMemory(BaseModel):
    """Represents a stored free-form text memory."""

    memory_id: Optional[str] = None
    content: str
    timestamp: Optional[str] = None


class ToolMemorySearchResult(BaseModel):
    """Represents a search result from tool memory storage."""

    memory: ToolMemory
    similarity_score: float
    rank: int


class TextMemorySearchResult(BaseModel):
    """Represents a search result from text memory storage."""

    memory: TextMemory
    similarity_score: float
    rank: int


class MemoryStats(BaseModel):
    """Memory storage statistics."""

    total_memories: int
    unique_tools: int
    unique_questions: int
    success_rate: float
    most_used_tools: Dict[str, int]
