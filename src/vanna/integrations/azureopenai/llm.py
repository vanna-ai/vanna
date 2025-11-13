"""
Azure OpenAI LLM service implementation.

Provides an `LlmService` backed by Azure OpenAI Chat Completions (openai>=1.0.0)
with support for streaming, deployment-scoped models, and Azure-specific
authentication flows.
"""

from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

from vanna.core.llm import (
    LlmService,
    LlmRequest,
    LlmResponse,
    LlmStreamChunk,
)
from vanna.core.tool import ToolCall, ToolSchema


# Models that don't support temperature and other sampling parameters
REASONING_MODELS: Set[str] = {
    "o1",
    "o1-mini",
    "o1-preview",
    "o3-mini",
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-5-pro",
    "gpt-5-codex",
}


def _is_reasoning_model(model: str) -> bool:
    """Return True when the deployment targets a reasoning-only model."""
    model_lower = model.lower()
    return any(reasoning_model in model_lower for reasoning_model in REASONING_MODELS)


class AzureOpenAILlmService(LlmService):
    """Azure OpenAI Chat Completions-backed LLM service.

    Wraps `openai.AzureOpenAI` so Vanna can talk to deployment-scoped models
    and either API key or Microsoft Entra ID authentication.

    Args:
        model: Deployment name in Azure OpenAI (required).
        api_key: API key; falls back to `AZURE_OPENAI_API_KEY`.
        azure_endpoint: Azure OpenAI endpoint URL; falls back to
            `AZURE_OPENAI_ENDPOINT`.
        api_version: API version; defaults to "2024-10-21" or
            `AZURE_OPENAI_API_VERSION`.
        azure_ad_token_provider: Optional bearer token provider for Entra ID.
        **extra_client_kwargs: Additional keyword arguments forwarded to the
            underlying client.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        azure_ad_token_provider: Optional[Any] = None,
        **extra_client_kwargs: Any,
    ) -> None:
        try:
            from openai import AzureOpenAI
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "openai package is required. Install with: pip install 'vanna[azureopenai]' "
                "or 'pip install openai'"
            ) from e

        # Model/deployment name is required for Azure OpenAI
        self.model = model or os.getenv("AZURE_OPENAI_MODEL")
        if not self.model:
            raise ValueError(
                "model parameter (deployment name) is required for Azure OpenAI. "
                "Provide it as argument or set AZURE_OPENAI_MODEL environment variable."
            )

        # Azure endpoint is required
        azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        if not azure_endpoint:
            raise ValueError(
                "azure_endpoint is required for Azure OpenAI. "
                "Provide it as argument or set AZURE_OPENAI_ENDPOINT environment variable."
            )

        # API version - use latest stable GA version by default
        api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

        # Build client kwargs
        client_kwargs: Dict[str, Any] = {
            "azure_endpoint": azure_endpoint,
            "api_version": api_version,
            **extra_client_kwargs,
        }

        # Authentication: prefer Azure AD token provider, fallback to API key
        if azure_ad_token_provider is not None:
            client_kwargs["azure_ad_token_provider"] = azure_ad_token_provider
        else:
            api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "Authentication required: provide either api_key or azure_ad_token_provider. "
                    "API key can also be set via AZURE_OPENAI_API_KEY environment variable."
                )
            client_kwargs["api_key"] = api_key

        self._client = AzureOpenAI(**client_kwargs)
        self._is_reasoning_model = _is_reasoning_model(self.model)

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Send a non-streaming request to Azure OpenAI and return the response."""
        payload = self._build_payload(request)

        # Call the API synchronously; this function is async but we can block here.
        resp = self._client.chat.completions.create(**payload, stream=False)

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
        """
        Stream a request to Azure OpenAI.

        Emits `LlmStreamChunk` for textual deltas as they arrive. Tool-calls are
        accumulated and emitted in a final chunk when the stream ends.
        """
        payload = self._build_payload(request)

        # Synchronous streaming iterator; iterate within async context.
        stream = self._client.chat.completions.create(**payload, stream=True)

        # Builders for streamed tool-calls (index -> partial)
        tc_builders: Dict[int, Dict[str, Optional[str]]] = {}
        last_finish: Optional[str] = None

        for event in stream:
            if not getattr(event, "choices", None):
                continue

            choice = event.choices[0]
            delta = getattr(choice, "delta", None)
            if delta is None:
                # Some SDK versions use `event.choices[0].message` on the final packet
                last_finish = getattr(choice, "finish_reason", last_finish)
                continue

            # Text content
            content_piece: Optional[str] = getattr(delta, "content", None)
            if content_piece:
                yield LlmStreamChunk(content=content_piece)

            # Tool calls (streamed)
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
                            b["name"] = fn.name
                        if getattr(fn, "arguments", None):
                            b["arguments"] = (b["arguments"] or "") + fn.arguments

            last_finish = getattr(choice, "finish_reason", last_finish)

        # Emit final tool-calls chunk if any
        final_tool_calls: List[ToolCall] = []
        for b in tc_builders.values():
            if not b.get("name"):
                continue
            args_raw = b.get("arguments") or "{}"
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
                    name=b["name"] or "tool",
                    arguments=args_dict,
                )
            )

        if final_tool_calls:
            yield LlmStreamChunk(tool_calls=final_tool_calls, finish_reason=last_finish)
        else:
            # Still emit a terminal chunk to signal completion
            yield LlmStreamChunk(finish_reason=last_finish or "stop")

    async def validate_tools(self, tools: List[ToolSchema]) -> List[str]:
        """Validate tool schemas. Returns a list of error messages."""
        errors: List[str] = []
        # Basic checks; Azure OpenAI will enforce further validation server-side.
        for t in tools:
            if not t.name or len(t.name) > 64:
                errors.append(f"Invalid tool name: {t.name!r}")
        return errors

    # Internal helpers
    def _build_payload(self, request: LlmRequest) -> Dict[str, Any]:
        """Build the API payload from LlmRequest."""
        messages: List[Dict[str, Any]] = []

        # Add system prompt as first message if provided
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        for m in request.messages:
            msg: Dict[str, Any] = {"role": m.role, "content": m.content}
            if m.role == "tool" and m.tool_call_id:
                msg["tool_call_id"] = m.tool_call_id
            elif m.role == "assistant" and m.tool_calls:
                # Convert tool calls to OpenAI format
                tool_calls_payload = []
                for tc in m.tool_calls:
                    tool_calls_payload.append(
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                    )
                msg["tool_calls"] = tool_calls_payload
            messages.append(msg)

        tools_payload: Optional[List[Dict[str, Any]]] = None
        if request.tools:
            tools_payload = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in request.tools
            ]

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        # Add temperature only for non-reasoning models
        # Reasoning models (GPT-5, o1, o3-mini) don't support temperature parameter
        if not self._is_reasoning_model:
            payload["temperature"] = request.temperature

        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        if tools_payload:
            payload["tools"] = tools_payload
            payload["tool_choice"] = "auto"

        return payload

    def _extract_tool_calls_from_message(self, message: Any) -> List[ToolCall]:
        """Extract tool calls from OpenAI message object."""
        tool_calls: List[ToolCall] = []
        raw_tool_calls = getattr(message, "tool_calls", None) or []
        for tc in raw_tool_calls:
            fn = getattr(tc, "function", None)
            if not fn:
                continue
            args_raw = getattr(fn, "arguments", "{}")
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
                    name=getattr(fn, "name", "tool"),
                    arguments=args_dict,
                )
            )
        return tool_calls
