"""
Groq LLM service implementation.

This module provides an implementation of the LlmService interface backed by
Groq's Cloud API (groq>=0.4.0). It supports non-streaming responses and
best-effort streaming of text content. Tool/function calling is passed
through when tools are provided.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from vanna.core.llm import (
    LlmService,
    LlmRequest,
    LlmResponse,
    LlmStreamChunk,
)
from vanna.core.tool import ToolCall, ToolSchema


class GroqLlmService(LlmService):
    """Groq API-backed LLM service.

    Args:
        model: Groq model name (e.g., "llama3-70b-8192").
        api_key: API key; falls back to env `GROQ_API_KEY`.
        base_url: Optional custom base URL; env `GROQ_BASE_URL` if unset.
        extra_client_kwargs: Extra kwargs forwarded to `groq.Groq()`.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **extra_client_kwargs: Any,
    ) -> None:
        try:
            from groq import Groq
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "groq package is required. Install with: pip install groq"
            ) from e

        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        api_key = api_key or os.getenv("GROQ_API_KEY")
        base_url = base_url or os.getenv("GROQ_BASE_URL")

        client_kwargs: Dict[str, Any] = {**extra_client_kwargs}
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url

        self._client = Groq(**client_kwargs)

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Send a non-streaming request to Groq and return the response.

        This method executes the underlying SDK call in a worker thread to
        avoid blocking the event loop.
        """
        payload = self._build_payload(request)

        resp = await asyncio.to_thread(
            lambda: self._client.chat.completions.create(**payload, stream=False)
        )

        if not resp.choices:
            return LlmResponse(content=None, tool_calls=None, finish_reason=None)

        choice = resp.choices[0]
        content: Optional[str] = getattr(choice.message, "content", None)
        tool_calls = self._extract_tool_calls_from_message(choice.message)

        usage: Dict[str, int] = {}
        if getattr(resp, "usage", None):
            usage = {
                k: int(v)
                for k, v in {
                    "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(resp.usage, "completion_tokens", 0),
                    "total_tokens": getattr(resp.usage, "total_tokens", 0),
                }.items()
            }

        return LlmResponse(
            content=content,
            tool_calls=tool_calls or None,
            finish_reason=getattr(choice, "finish_reason", None),
            usage=usage or None,
        )

    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        """Stream a request to Groq.

        The Groq SDK stream iterator is synchronous, so each iterator step runs
        in a worker thread and is bridged back into this async generator.
        """
        payload = self._build_payload(request)

        stream: Any = await asyncio.to_thread(
            lambda: self._client.chat.completions.create(**payload, stream=True)
        )

        tc_builders: Dict[int, Dict[str, Optional[str]]] = {}
        last_finish: Optional[str] = None
        sentinel = object()

        def _next_event() -> Any:
            return next(stream, sentinel)

        while True:
            event = await asyncio.to_thread(_next_event)
            if event is sentinel:
                break
            if not getattr(event, "choices", None):
                continue

            choice = event.choices[0]
            delta = getattr(choice, "delta", None)
            if delta is None:
                last_finish = getattr(choice, "finish_reason", last_finish)
                continue

            content_piece: Optional[str] = getattr(delta, "content", None)
            if content_piece:
                yield LlmStreamChunk(content=content_piece)

            streamed_tool_calls = getattr(delta, "tool_calls", None)
            if streamed_tool_calls:
                for tc in streamed_tool_calls:
                    idx = getattr(tc, "index", 0) or 0
                    b = tc_builders.setdefault(
                        idx, {"id": None, "name": None, "arguments": ""}
                    )
                    if getattr(tc, "id", None):
                        b["id"] = tc.id
                    fn = getattr(tc, "function", None)
                    if fn is not None:
                        if getattr(fn, "name", None):
                            b["name"] = (b.get("name") or "") + fn.name
                        if getattr(fn, "arguments", None):
                            b["arguments"] = (b.get("arguments") or "") + fn.arguments

            last_finish = getattr(choice, "finish_reason", last_finish)

        final_tool_calls: List[ToolCall] = []
        for b in tc_builders.values():
            raw_name = b.get("name")
            if not raw_name:
                continue

            name, args_raw = self._normalize_tool_name_and_args(
                raw_name, b.get("arguments") or ""
            )

            try:
                loaded = json.loads(args_raw)
                if isinstance(loaded, dict):
                    args_dict: Dict[str, Any] = loaded
                else:
                    args_dict = {"args": loaded}
            except Exception:
                args_dict = {"_raw": args_raw}
            final_tool_calls.append(
                ToolCall(
                    id=b.get("id") or "tool_call",
                    name=name or "tool",
                    arguments=args_dict,
                )
            )

        if final_tool_calls:
            yield LlmStreamChunk(tool_calls=final_tool_calls, finish_reason=last_finish)
        else:
            yield LlmStreamChunk(finish_reason=last_finish or "stop")

    async def validate_tools(self, tools: List[ToolSchema]) -> List[str]:
        """Validate tool schemas. Returns a list of error messages."""
        errors: List[str] = []
        for t in tools:
            if not t.name or len(t.name) > 64:
                errors.append(f"Invalid tool name: {t.name!r}")
        return errors

    def _build_payload(self, request: LlmRequest) -> Dict[str, Any]:
        """Convert a generic LLM request into Groq chat-completions payload."""
        messages: List[Dict[str, Any]] = []

        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        for m in request.messages:
            msg: Dict[str, Any] = {"role": m.role, "content": m.content or ""}

            if m.role == "tool" and getattr(m, "tool_call_id", None):
                msg["tool_call_id"] = m.tool_call_id
                # Groq may require tool name to be echoed for tool-role messages.
                msg["name"] = getattr(m, "name", "tool")
            elif m.role == "assistant":
                tool_calls_payload: List[Dict[str, Any]] = []
                for tc in m.tool_calls or []:
                    args_to_dump = tc.arguments
                    # Groq expects JSON-string arguments in tool call payloads.
                    if not isinstance(args_to_dump, str):
                        args_str = json.dumps(args_to_dump)
                    else:
                        args_str = args_to_dump

                    tool_calls_payload.append(
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": args_str,
                            },
                        }
                    )
                if tool_calls_payload:
                    msg["tool_calls"] = tool_calls_payload
            messages.append(msg)

        tools_payload: Optional[List[Dict[str, Any]]] = None
        if request.tools:
            tools_payload = []
            for t in request.tools:
                # Ensure object-type schema when properties are present.
                params = dict(t.parameters) if getattr(t, "parameters", None) else {}
                if "type" not in params and "properties" in params:
                    params["type"] = "object"

                tools_payload.append(
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": params,
                        },
                    }
                )

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            # Keep temperature conservative for reliable tool-calling behavior.
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if tools_payload:
            payload["tools"] = tools_payload
            payload["tool_choice"] = "auto"

        return payload

    def _extract_tool_calls_from_message(self, message: Any) -> List[ToolCall]:
        """Extract tool calls from a non-streaming Groq response message."""
        tool_calls: List[ToolCall] = []
        raw_tool_calls = getattr(message, "tool_calls", None) or []
        for tc in raw_tool_calls:
            fn = getattr(tc, "function", None)
            if not fn:
                continue

            name, args_raw = self._normalize_tool_name_and_args(
                getattr(fn, "name", ""), getattr(fn, "arguments", "")
            )

            try:
                loaded = json.loads(args_raw)
                if isinstance(loaded, dict):
                    args_dict: Dict[str, Any] = loaded
                else:
                    args_dict = {"args": loaded}
            except Exception:
                args_dict = {"_raw": args_raw}
            tool_calls.append(
                ToolCall(
                    id=getattr(tc, "id", "tool_call"),
                    name=name or "tool",
                    arguments=args_dict,
                )
            )
        return tool_calls

    def _normalize_tool_name_and_args(
        self, raw_name: str, raw_args: str
    ) -> Tuple[str, str]:
        """Normalize Groq tool-name quirks and ensure non-empty JSON arguments."""
        name = raw_name
        args_raw = raw_args

        # Some models may append JSON fragments to the function name.
        match = re.match(r"^([a-zA-Z0-9_-]+)([\s\[\{].*)?$", name)
        if match:
            name = match.group(1)
            missing_args = (match.group(2) or "").strip()
            if missing_args:
                args_raw = missing_args + args_raw

        return name, args_raw or "{}"
