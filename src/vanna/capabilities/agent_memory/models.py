"""
Memory storage models and types.
"""

from typing import Dict, Any, Optional
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


class MemorySearchResult(BaseModel):
    """Represents a search result from memory storage."""
    memory: ToolMemory
    similarity_score: float
    rank: int


class MemoryStats(BaseModel):
    """Memory storage statistics."""
    total_memories: int
    unique_tools: int
    unique_questions: int
    success_rate: float
    most_used_tools: Dict[str, int]