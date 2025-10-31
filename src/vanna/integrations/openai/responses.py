from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from vanna.core.llm import LlmService, LlmRequest, LlmResponse, LlmStreamChunk
from vanna.core.tool import ToolCall, ToolSchema


class OpenAIResponsesService(LlmService):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        try:
            from openai import AsyncOpenAI
            from openai.types.responses import Response
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "openai package is required. Install with: pip install 'vanna[openai]'"
            ) from e

        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5")

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        payload = self._payload(request)
        resp: Response = await self.client.responses.create(**payload)
        self._debug_print("response", resp)
        text, tools, status, usage = self._extract(resp)
        return LlmResponse(
            content=text,
            tool_calls=tools or None,
            finish_reason=status,
            usage=usage or None,
            metadata={"request_id": getattr(resp, "id", None)},
        )

    async def stream_request(self, request: LlmRequest) -> AsyncGenerator[LlmStreamChunk, None]:
        payload = self._payload(request)
        async with self.client.responses.stream(**payload) as stream:
            async for event in stream:
                self._debug_print("stream_event", event)
                event_type = getattr(event, "type", None)
                if event_type == "response.output_text.delta":
                    delta = getattr(event, "delta", None)
                    if delta:
                        yield LlmStreamChunk(content=delta)
            final: Response = await stream.get_final_response()
            self._debug_print("final_response", final)

        _text, tools, status, _usage = self._extract(final)
        yield LlmStreamChunk(tool_calls=tools or None, finish_reason=status)

    async def validate_tools(self, tools: List[Any]) -> List[str]:
        return []  # minimal: accept whatever's passed through

    # ---- helpers ----

    def _payload(self, request: LlmRequest) -> Dict[str, Any]:
        msgs = [{"role": m.role, "content": m.content} for m in request.messages]
        p: Dict[str, Any] = {"model": self.model, "input": msgs}
        if request.system_prompt:
            p["instructions"] = request.system_prompt
        if request.max_tokens:
            p["max_output_tokens"] = request.max_tokens
        if request.tools:
            p["tools"] = [self._serialize_tool(t) for t in request.tools]
        return p

    def _debug_print(self, label: str, obj: Any) -> None:
        try:
            payload = obj.model_dump()
        except AttributeError:
            try:
                payload = obj.dict()
            except AttributeError:
                payload = obj
        print(f"[OpenAIResponsesService] {label}: {payload}")

    def _extract(
        self, resp: Response
    ) -> Tuple[Optional[str], Optional[List[ToolCall]], Optional[str], Optional[Dict[str, int]]]:
        text = getattr(resp, "output_text", None)

        tool_calls: List[ToolCall] = []
        for oc in getattr(resp, "output", []) or []:
            for item in getattr(oc, "content", []) or []:
                if getattr(item, "type", None) == "tool_call":
                    tc = getattr(item, "tool_call", None)
                    if tc and getattr(tc, "type", None) == "function":
                        fn = getattr(tc, "function", None)
                        if fn:
                            name = getattr(fn, "name", None)
                            args = getattr(fn, "arguments", None)
                            if not isinstance(args, (dict, list)):
                                try:
                                    args = json.loads(args) if args else {}
                                except Exception:
                                    args = {"_raw": args}
                            tool_calls.append(ToolCall(name=name, arguments=args))

        usage = None
        if getattr(resp, "usage", None):
            usage = {
                "input_tokens": getattr(resp.usage, "input_tokens", 0) or 0,
                "output_tokens": getattr(resp.usage, "output_tokens", 0) or 0,
                "total_tokens": getattr(resp.usage, "total_tokens", None)
                or ((getattr(resp.usage, "input_tokens", 0) or 0) + (getattr(resp.usage, "output_tokens", 0) or 0)),
            }

        status = getattr(resp, "status", None)  # e.g. "completed"
        return text, (tool_calls or None), status, usage

    def _serialize_tool(self, tool: Any) -> Dict[str, Any]:
        """Convert a tool schema into the dict format expected by OpenAI Responses."""

        if isinstance(tool, ToolSchema):
            return {
                "type": "function",
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "strict": False,
            }

        # Support generic pydantic/BaseModel style objects without importing pydantic here.
        if hasattr(tool, "model_dump"):
            data = tool.model_dump()
            if all(key in data for key in ("name", "description", "parameters")):
                return {
                    "type": "function",
                    "name": data["name"],
                    "description": data["description"],
                    "parameters": data["parameters"],
                    "strict": data.get("strict", False),
                }
            return data

        if isinstance(tool, dict):
            if "type" in tool:
                return tool
            if all(k in tool for k in ("name", "description", "parameters")):
                return {
                    "type": "function",
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                    "strict": tool.get("strict", False),
                }
            return tool

        raise TypeError(f"Unsupported tool schema type: {type(tool)!r}")
