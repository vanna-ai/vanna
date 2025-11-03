"""
Ollama LLM service implementation.

This module provides an implementation of the LlmService interface backed by
Ollama's local LLM API. It supports non-streaming responses and streaming
of text content. Tool calling support depends on the Ollama model being used.
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


class OllamaLlmService(LlmService):
    """Ollama-backed LLM service for local model inference.

    Args:
        model: Ollama model name (e.g., "gpt-oss:20b").
        host: Ollama server URL; defaults to "http://localhost:11434" or env `OLLAMA_HOST`.
        timeout: Request timeout in seconds; defaults to 240.
        num_ctx: Context window size; defaults to 8192.
        temperature: Sampling temperature; defaults to 0.7.
        extra_options: Additional options passed to Ollama (e.g., num_predict, top_k, top_p).
    """

    def __init__(
        self,
        model: str,
        host: Optional[str] = None,
        timeout: float = 240.0,
        num_ctx: int = 8192,
        temperature: float = 0.7,
        **extra_options: Any,
    ) -> None:
        try:
            import ollama
        except ImportError as e:
            raise ImportError(
                "ollama package is required. Install with: pip install 'vanna[ollama]' or pip install ollama"
            ) from e

        if not model:
            raise ValueError("model parameter is required for Ollama")

        self.model = model
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.temperature = temperature
        self.extra_options = extra_options

        # Create Ollama client
        self._client = ollama.Client(host=self.host, timeout=timeout)

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Send a non-streaming request to Ollama and return the response."""
        payload = self._build_payload(request)

        # Call the Ollama API
        try:
            resp = self._client.chat(**payload)
        except Exception as e:
            raise RuntimeError(f"Ollama request failed: {str(e)}") from e

        # Extract message from response
        message = resp.get("message", {})
        content = message.get("content")
        tool_calls = self._extract_tool_calls_from_message(message)

        # Extract usage information if available
        usage: Dict[str, int] = {}
        if "prompt_eval_count" in resp or "eval_count" in resp:
            usage = {
                "prompt_tokens": resp.get("prompt_eval_count", 0),
                "completion_tokens": resp.get("eval_count", 0),
                "total_tokens": resp.get("prompt_eval_count", 0) + resp.get("eval_count", 0),
            }

        return LlmResponse(
            content=content,
            tool_calls=tool_calls or None,
            finish_reason=resp.get("done_reason") or ("stop" if resp.get("done") else None),
            usage=usage or None,
        )

    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        """Stream a request to Ollama.

        Emits `LlmStreamChunk` for textual deltas as they arrive. Tool calls are
        accumulated and emitted in a final chunk when the stream ends.
        """
        payload = self._build_payload(request)

        # Ollama streaming
        try:
            stream = self._client.chat(**payload, stream=True)
        except Exception as e:
            raise RuntimeError(f"Ollama streaming request failed: {str(e)}") from e

        # Accumulate tool calls if present
        accumulated_tool_calls: List[ToolCall] = []
        last_finish: Optional[str] = None

        for chunk in stream:
            message = chunk.get("message", {})
            
            # Yield text content
            content = message.get("content")
            if content:
                yield LlmStreamChunk(content=content)

            # Accumulate tool calls
            tool_calls = self._extract_tool_calls_from_message(message)
            if tool_calls:
                accumulated_tool_calls.extend(tool_calls)

            # Track finish reason
            if chunk.get("done"):
                last_finish = chunk.get("done_reason", "stop")

        # Emit final chunk with tool calls if any
        if accumulated_tool_calls:
            yield LlmStreamChunk(
                tool_calls=accumulated_tool_calls,
                finish_reason=last_finish or "stop"
            )
        else:
            # Emit terminal chunk to signal completion
            yield LlmStreamChunk(finish_reason=last_finish or "stop")

    async def validate_tools(self, tools: List[ToolSchema]) -> List[str]:
        """Validate tool schemas. Returns a list of error messages."""
        errors: List[str] = []
        # Basic validation; Ollama model support for tools varies
        for t in tools:
            if not t.name:
                errors.append(f"Tool must have a name")
            if not t.description:
                errors.append(f"Tool '{t.name}' should have a description")
        return errors

    # Internal helpers
    def _build_payload(self, request: LlmRequest) -> Dict[str, Any]:
        """Build the Ollama chat payload from LlmRequest."""
        messages: List[Dict[str, Any]] = []

        # Add system prompt as first message if provided
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        # Convert messages to Ollama format
        for m in request.messages:
            msg: Dict[str, Any] = {"role": m.role, "content": m.content or ""}
            
            # Handle tool calls in assistant messages
            if m.role == "assistant" and m.tool_calls:
                # Some Ollama models support tool_calls in message
                tool_calls_payload = []
                for tc in m.tool_calls:
                    tool_calls_payload.append({
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments
                        }
                    })
                msg["tool_calls"] = tool_calls_payload
            
            messages.append(msg)

        # Build tools array if tools are provided
        tools_payload: Optional[List[Dict[str, Any]]] = None
        if request.tools:
            tools_payload = []
            for t in request.tools:
                tools_payload.append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    }
                })

        # Build options
        options: Dict[str, Any] = {
            "num_ctx": self.num_ctx,
            "temperature": self.temperature,
            **self.extra_options,
        }

        # Build final payload
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "options": options,
        }

        # Add tools if provided (note: not all Ollama models support tools)
        if tools_payload:
            payload["tools"] = tools_payload

        return payload

    def _extract_tool_calls_from_message(self, message: Dict[str, Any]) -> List[ToolCall]:
        """Extract tool calls from Ollama message."""
        tool_calls: List[ToolCall] = []
        
        # Check for tool_calls in message
        raw_tool_calls = message.get("tool_calls", [])
        if not raw_tool_calls:
            return tool_calls

        for idx, tc in enumerate(raw_tool_calls):
            fn = tc.get("function", {})
            name = fn.get("name")
            if not name:
                continue

            # Parse arguments
            arguments = fn.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except Exception:
                    arguments = {"_raw": arguments}
            
            if not isinstance(arguments, dict):
                arguments = {"args": arguments}

            tool_calls.append(
                ToolCall(
                    id=tc.get("id", f"tool_call_{idx}"),
                    name=name,
                    arguments=arguments,
                )
            )

        return tool_calls
