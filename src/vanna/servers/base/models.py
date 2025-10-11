"""
Request and response models for server endpoints.
"""

import time
import uuid
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from ...components import UiComponent, RichComponent
from ...core.component_manager import ComponentUpdate
from ...core.user.request_context import RequestContext


class ChatRequest(BaseModel):
    """Request model for chat endpoints."""

    message: str = Field(description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")
    request_context: RequestContext = Field(default_factory=RequestContext, description="Request context for user resolution")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ChatStreamChunk(BaseModel):
    """Single chunk in a streaming chat response."""

    rich: Dict[str, Any] = Field(description="Rich component data for advanced UIs")
    simple: Optional[Dict[str, Any]] = Field(default=None, description="Simple component data for basic UIs")

    # Stream metadata
    conversation_id: str = Field(description="Conversation ID")
    request_id: str = Field(description="Request ID")
    timestamp: float = Field(default_factory=time.time, description="Timestamp")

    @classmethod
    def from_component(
        cls,
        component: Union[UiComponent, RichComponent],
        conversation_id: str,
        request_id: str
    ) -> "ChatStreamChunk":
        """Create chunk from UI component or rich component."""

        if isinstance(component, UiComponent):
            # Full UiComponent with both rich and simple
            rich_data = component.rich_component.serialize_for_frontend()
            simple_data = None
            if component.simple_component:
                simple_data = component.simple_component.serialize_for_frontend()

            return cls(
                rich=rich_data,
                simple=simple_data,
                conversation_id=conversation_id,
                request_id=request_id,
            )

        # Rich component only (no simple fallback)
        rich_data = component.serialize_for_frontend()
        return cls(
            rich=rich_data,
            simple=None,
            conversation_id=conversation_id,
            request_id=request_id,
        )

    @classmethod
    def from_component_update(
        cls,
        update: ComponentUpdate,
        conversation_id: str,
        request_id: str
    ) -> "ChatStreamChunk":
        """Create chunk from component update."""
        update_payload = update.serialize_for_frontend()
        return cls(
            rich=update_payload,
            simple=None,  # Component updates don't have simple representations
            conversation_id=conversation_id,
            request_id=request_id,
        )


class ChatResponse(BaseModel):
    """Complete chat response for polling endpoints."""

    chunks: List[ChatStreamChunk] = Field(description="Response chunks")
    conversation_id: str = Field(description="Conversation ID")
    request_id: str = Field(description="Request ID")
    total_chunks: int = Field(description="Total number of chunks")

    @classmethod
    def from_chunks(cls, chunks: List[ChatStreamChunk]) -> "ChatResponse":
        """Create response from chunks."""
        if not chunks:
            return cls(
                chunks=[],
                conversation_id="",
                request_id="",
                total_chunks=0
            )

        return cls(
            chunks=chunks,
            conversation_id=chunks[0].conversation_id,
            request_id=chunks[0].request_id,
            total_chunks=len(chunks)
        )
