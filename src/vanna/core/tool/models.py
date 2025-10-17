"""
Tool domain models.

This module contains data models for tool execution.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..components import UiComponent
    from ..user.models import User
    from ..observability import ObservabilityProvider


class ToolCall(BaseModel):
    """Represents a tool call from the LLM."""

    id: str = Field(description="Unique identifier for this tool call")
    name: str = Field(description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(description="Raw arguments from LLM")


class ToolContext(BaseModel):
    """Context passed to all tool executions."""

    user: "User"  # Forward reference to avoid circular import
    conversation_id: str
    request_id: str = Field(description="Unique request identifier for tracing")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    observability_provider: Optional["ObservabilityProvider"] = Field(
        default=None, description="Optional observability provider for metrics and spans"
    )

    class Config:
        arbitrary_types_allowed = True


class ToolResult(BaseModel):
    """Result from tool execution.

    Changes:
    - `result_for_llm`: string that will be sent back to the LLM.
    - `ui_component`: optional UI payload for rendering in clients.
    """

    success: bool = Field(description="Whether execution succeeded")
    result_for_llm: str = Field(description="String content to send back to the LLM")
    ui_component: Optional["UiComponent"] = Field(
        default=None, description="Optional UI component for rendering"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolSchema(BaseModel):
    """Schema describing a tool for LLM consumption."""

    name: str = Field(description="Tool name")
    description: str = Field(description="What this tool does")
    parameters: Dict[str, Any] = Field(description="JSON Schema of parameters")
    access_groups: List[str] = Field(
        default_factory=list, description="Groups permitted to access this tool"
    )
