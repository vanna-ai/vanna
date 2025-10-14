"""
LLM domain models.

This module contains data models for LLM communication.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..tool.models import ToolCall
from ..user.models import User


class LlmMessage(BaseModel):
    """Message format for LLM communication."""

    role: str = Field(description="Message role")
    content: str = Field(description="Message content")
    tool_calls: Optional[List[ToolCall]] = Field(default=None)
    tool_call_id: Optional[str] = Field(default=None)


class LlmRequest(BaseModel):
    """Request to LLM service."""

    messages: List[LlmMessage] = Field(description="Messages to send")
    tools: Optional[List[Any]] = Field(
        default=None, description="Available tools"
    )  # Will be ToolSchema but avoiding circular import
    user: User = Field(description="User making the request")
    stream: bool = Field(default=False, description="Whether to stream response")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    system_prompt: Optional[str] = Field(default=None, description="System prompt for the LLM")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LlmResponse(BaseModel):
    """Response from LLM."""

    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_tool_call(self) -> bool:
        """Check if this response contains tool calls."""
        return self.tool_calls is not None and len(self.tool_calls) > 0


class LlmStreamChunk(BaseModel):
    """Streaming chunk from LLM."""

    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
