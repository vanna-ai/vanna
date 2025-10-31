"""
OpenAI Responses API service implementation.

This module provides an implementation of the LlmService interface backed by
OpenAI's Responses API (openai>=1.0.0). The Responses API is a newer, more
stateful API that provides better support for persistent reasoning, hosted tools,
and multimodal workflows compared to Chat Completions.

Key differences from Chat Completions:
- Stateful: Maintains conversation context automatically via response IDs
- Reasoning preservation: Model's reasoning state persists across turns
- Better tool support: Built-in support for MCP servers and hosted tools
- Multimodal: Enhanced support for images, audio, and file inputs
- Output structure: Returns polymorphic items (reasoning, messages, function calls)
"""

from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

from vanna.core.llm import (
    LlmService,
    LlmRequest,
    LlmResponse,
    LlmStreamChunk,
)
from vanna.core.tool import ToolCall, ToolSchema


class OpenAIResponsesService(LlmService):
    """OpenAI Responses API-backed LLM service.

    This service uses the newer Responses API which provides stateful conversation
    management, persistent reasoning, and enhanced tool support.

    Args:
        model: OpenAI model name (e.g., "gpt-5").
        api_key: API key; falls back to env `OPENAI_API_KEY`.
        organization: Optional org; env `OPENAI_ORG` if unset.
        base_url: Optional custom base URL; env `OPENAI_BASE_URL` if unset.
        instructions: Optional default instructions for the assistant.
        enable_web_search: Enable web search tool by default.
        extra_client_kwargs: Extra kwargs forwarded to `openai.OpenAI()`.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        base_url: Optional[str] = None,
        instructions: Optional[str] = None,
        enable_web_search: bool = False,
        **extra_client_kwargs: Any,
    ) -> None:
        try:
            from openai import OpenAI
        except Exception as e:  # pragma: no cover - import-time error surface
            raise ImportError(
                "openai package is required. Install with: pip install 'vanna[openai]'"
            ) from e

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5")
        self.instructions = instructions
        self.enable_web_search = enable_web_search
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        organization = organization or os.getenv("OPENAI_ORG")
        base_url = base_url or os.getenv("OPENAI_BASE_URL")

        client_kwargs: Dict[str, Any] = {**extra_client_kwargs}
        if api_key:
            client_kwargs["api_key"] = api_key
        if organization:
            client_kwargs["organization"] = organization
        if base_url:
            client_kwargs["base_url"] = base_url

        self._client = OpenAI(**client_kwargs)

        # Track previous response ID for stateful conversations
        self._previous_response_id: Optional[str] = None

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Send a non-streaming request to OpenAI Responses API and return the response."""
        payload = self._build_payload(request)

        # Call the Responses API
        resp = self._client.responses.create(**payload)

        # Store response ID for potential follow-up
        self._previous_response_id = resp.id

        # Extract content from response output
        content: Optional[str] = None
        tool_calls: List[ToolCall] = []

        # Process output items
        if hasattr(resp, "output") and resp.output:
            for item in resp.output:
                # Handle message items
                if hasattr(item, "content"):
                    content_items = item.content if isinstance(item.content, list) else [item.content]
                    text_parts = []
                    for content_item in content_items:
                        if hasattr(content_item, "text"):
                            text_parts.append(content_item.text)
                    if text_parts:
                        content = "\n".join(text_parts)

                # Handle function call items
                if hasattr(item, "type") and item.type == "function_call":
                    tool_calls.append(
                        ToolCall(
                            id=getattr(item, "id", "tool_call"),
                            name=getattr(item, "name", "tool"),
                            arguments=json.loads(getattr(item, "arguments", "{}"))
                            if isinstance(getattr(item, "arguments", "{}"), str)
                            else getattr(item, "arguments", {}),
                        )
                    )

        # Extract usage information
        usage: Dict[str, int] = {}
        if hasattr(resp, "usage") and resp.usage:
            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0),
                "total_tokens": getattr(resp.usage, "total_tokens", 0),
            }

        return LlmResponse(
            content=content,
            tool_calls=tool_calls or None,
            finish_reason=getattr(resp, "status", None),
            usage=usage or None,
            metadata={"response_id": resp.id},
        )

    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        """Stream a request to OpenAI Responses API.

        Note: The Responses API provides enhanced streaming with semantic events
        and structured output items.
        """
        payload = self._build_payload(request)

        # Stream from Responses API
        stream = self._client.responses.create(**payload, stream=True)

        accumulated_text = []
        accumulated_tool_calls: List[ToolCall] = []
        last_status: Optional[str] = None
        response_id: Optional[str] = None

        for event in stream:
            # Track response ID
            if hasattr(event, "id") and event.id:
                response_id = event.id

            # Handle different event types
            if hasattr(event, "output") and event.output:
                for item in event.output:
                    # Text content
                    if hasattr(item, "content"):
                        content_items = item.content if isinstance(item.content, list) else [item.content]
                        for content_item in content_items:
                            if hasattr(content_item, "text"):
                                accumulated_text.append(content_item.text)
                                yield LlmStreamChunk(content=content_item.text)

                    # Function calls
                    if hasattr(item, "type") and item.type == "function_call":
                        tc = ToolCall(
                            id=getattr(item, "id", "tool_call"),
                            name=getattr(item, "name", "tool"),
                            arguments=json.loads(getattr(item, "arguments", "{}"))
                            if isinstance(getattr(item, "arguments", "{}"), str)
                            else getattr(item, "arguments", {}),
                        )
                        accumulated_tool_calls.append(tc)

            if hasattr(event, "status"):
                last_status = event.status

        # Store response ID for stateful conversations
        if response_id:
            self._previous_response_id = response_id

        # Emit final chunk with tool calls if any
        if accumulated_tool_calls:
            yield LlmStreamChunk(
                tool_calls=accumulated_tool_calls,
                finish_reason=last_status or "stop",
                metadata={"response_id": response_id} if response_id else {},
            )
        else:
            # Emit terminal chunk
            yield LlmStreamChunk(
                finish_reason=last_status or "stop",
                metadata={"response_id": response_id} if response_id else {},
            )

    async def validate_tools(self, tools: List[ToolSchema]) -> List[str]:
        """Validate tool schemas. Returns a list of error messages."""
        errors: List[str] = []
        # Basic checks; OpenAI will enforce further validation server-side.
        for t in tools:
            if not t.name or len(t.name) > 64:
                errors.append(f"Invalid tool name: {t.name!r}")
        return errors

    def reset_conversation(self) -> None:
        """Reset the conversation state.

        Clears the previous response ID, starting a fresh conversation.
        """
        self._previous_response_id = None

    def get_previous_response_id(self) -> Optional[str]:
        """Get the ID of the previous response for conversation continuation."""
        return self._previous_response_id

    def set_previous_response_id(self, response_id: Optional[str]) -> None:
        """Set the previous response ID for conversation continuation.

        This allows forking conversations from a specific point.
        """
        self._previous_response_id = response_id

    # Internal helpers
    def _build_payload(self, request: LlmRequest) -> Dict[str, Any]:
        """Build the Responses API payload from an LlmRequest."""

        # Build input from messages
        input_messages: List[Dict[str, Any]] = []
        for m in request.messages:
            msg: Dict[str, Any] = {"role": m.role, "content": m.content}
            if m.role == "tool" and m.tool_call_id:
                msg["tool_call_id"] = m.tool_call_id
            elif m.role == "assistant" and m.tool_calls:
                # Convert tool calls to Responses API format
                tool_calls_payload = []
                for tc in m.tool_calls:
                    tool_calls_payload.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments)
                        }
                    })
                msg["tool_calls"] = tool_calls_payload
            input_messages.append(msg)

        # Build tools array
        tools_payload: List[Dict[str, Any]] = []

        # Add web search if enabled
        if self.enable_web_search:
            tools_payload.append({"type": "web_search"})

        # Add custom tools from request
        if request.tools:
            for t in request.tools:
                tools_payload.append({
                    "type": "function",
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                })

        # Build the payload
        payload: Dict[str, Any] = {
            "model": self.model,
            "input": input_messages,
        }

        # Add instructions (combining system prompt and default instructions)
        instructions_parts = []
        if self.instructions:
            instructions_parts.append(self.instructions)
        if request.system_prompt:
            instructions_parts.append(request.system_prompt)
        if instructions_parts:
            payload["instructions"] = "\n\n".join(instructions_parts)

        # Add tools if any
        if tools_payload:
            payload["tools"] = tools_payload

        # Add previous response for stateful conversation
        if self._previous_response_id:
            payload["previous_response_id"] = self._previous_response_id

        # Add other parameters
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        return payload
