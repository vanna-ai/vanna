"""
Azure AI Foundry LLM service implementation.

Provides an `LlmService` backed by Azure AI Foundry's inference endpoint
using the azure-ai-inference SDK with support for streaming, tool calling,
and Azure-specific authentication flows.
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


class AzureAIFoundryLlmService(LlmService):
    """Azure AI Foundry Chat Completions-backed LLM service.

    Wraps `azure.ai.inference.ChatCompletionsClient` to enable Vanna to
    communicate with Azure AI Foundry project endpoints using the native
    azure-ai-inference SDK.

    Args:
        endpoint: Azure AI Foundry project endpoint URL; falls back to
            `AZURE_AI_FOUNDRY_ENDPOINT`.
        api_key: API key; falls back to `AZURE_AI_FOUNDRY_API_KEY`.
        model: Optional model name for model routing; falls back to
            `AZURE_AI_FOUNDRY_MODEL`. May be None if using default model.
        credential: Optional Azure credential object (e.g., DefaultAzureCredential)
            for Entra ID authentication. Takes precedence over api_key.
        **extra_client_kwargs: Additional keyword arguments forwarded to the
            underlying client.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        credential: Optional[Any] = None,
        use_entra_id: Optional[bool] = None,
        **extra_client_kwargs: Any,
    ) -> None:
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "azure-ai-inference package is required. Install with: "
                "pip install 'vanna[foundry]' or 'pip install azure-ai-inference'"
            ) from e

        # Endpoint is required for Azure AI Foundry
        self.endpoint = endpoint or os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
        if not self.endpoint:
            raise ValueError(
                "endpoint is required for Azure AI Foundry. "
                "Provide it as argument or set AZURE_AI_FOUNDRY_ENDPOINT environment variable."
            )

        # Model is optional - Foundry can use default model or model routing
        self.model = model or os.getenv("AZURE_AI_FOUNDRY_MODEL")

        # Check if Entra ID auth should be used
        if use_entra_id is None:
            use_entra_id = os.getenv("AZURE_AI_FOUNDRY_USE_ENTRA_ID", "").lower() in ("true", "1", "yes")

        # Build client kwargs
        client_kwargs: Dict[str, Any] = {
            "endpoint": self.endpoint,
            **extra_client_kwargs,
        }

        # Authentication: prefer explicit credential, then Entra ID, then API key
        if credential is not None:
            client_kwargs["credential"] = credential
        elif use_entra_id:
            # Use Azure AD/Entra ID authentication via DefaultAzureCredential
            try:
                from azure.identity import DefaultAzureCredential
                client_kwargs["credential"] = DefaultAzureCredential()
                # Set the correct scope for Azure AI Foundry/Cognitive Services
                client_kwargs["credential_scopes"] = ["https://cognitiveservices.azure.com/.default"]
                print("  Using Entra ID authentication (DefaultAzureCredential)")
            except ImportError:
                raise ImportError(
                    "azure-identity package is required for Entra ID auth. "
                    "Install with: pip install azure-identity"
                )
        else:
            api_key = api_key or os.getenv("AZURE_AI_FOUNDRY_API_KEY")
            if not api_key:
                raise ValueError(
                    "Authentication required: provide either api_key, credential, or set use_entra_id=True. "
                    "API key can also be set via AZURE_AI_FOUNDRY_API_KEY environment variable."
                )
            client_kwargs["credential"] = AzureKeyCredential(api_key)

        self._client = ChatCompletionsClient(**client_kwargs)
        self._is_reasoning_model = _is_reasoning_model(self.model or "")

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Send a non-streaming request to Azure AI Foundry and return the response."""
        messages = self._build_messages(request)
        tools_payload = self._build_tools_payload(request)

        # Build request kwargs
        kwargs: Dict[str, Any] = {
            "messages": messages,
        }

        # Add model if specified
        if self.model:
            kwargs["model"] = self.model

        # Add temperature only for non-reasoning models
        if not self._is_reasoning_model:
            kwargs["temperature"] = request.temperature

        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens

        if tools_payload:
            kwargs["tools"] = tools_payload
            kwargs["tool_choice"] = "auto"

        # Call the API
        resp = self._client.complete(**kwargs)

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
        Stream a request to Azure AI Foundry.

        Emits `LlmStreamChunk` for textual deltas as they arrive. Tool-calls are
        accumulated and emitted in a final chunk when the stream ends.
        """
        messages = self._build_messages(request)
        tools_payload = self._build_tools_payload(request)

        # Build request kwargs
        kwargs: Dict[str, Any] = {
            "messages": messages,
            "stream": True,
        }

        # Add model if specified
        if self.model:
            kwargs["model"] = self.model

        # Add temperature only for non-reasoning models
        if not self._is_reasoning_model:
            kwargs["temperature"] = request.temperature

        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens

        if tools_payload:
            kwargs["tools"] = tools_payload
            kwargs["tool_choice"] = "auto"

        # Call the API with streaming
        stream = self._client.complete(**kwargs)

        # Builders for streamed tool-calls (index -> partial)
        tc_builders: Dict[int, Dict[str, Optional[str]]] = {}
        last_finish: Optional[str] = None

        for event in stream:
            if not getattr(event, "choices", None):
                continue

            choice = event.choices[0]
            delta = getattr(choice, "delta", None)
            if delta is None:
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
        # Basic checks; Azure AI Foundry will enforce further validation server-side.
        for t in tools:
            if not t.name or len(t.name) > 64:
                errors.append(f"Invalid tool name: {t.name!r}")
        return errors

    # Internal helpers
    def _build_messages(self, request: LlmRequest) -> List[Any]:
        """Build the messages list from LlmRequest using Foundry message types."""
        try:
            from azure.ai.inference.models import (
                SystemMessage,
                UserMessage,
                AssistantMessage,
                ToolMessage,
                ChatCompletionsToolCall,
                FunctionCall,
            )
        except ImportError:  # pragma: no cover
            raise ImportError("azure-ai-inference is required for message building")

        messages: List[Any] = []

        # Add system prompt as first message if provided
        if request.system_prompt:
            messages.append(SystemMessage(content=request.system_prompt))

        for m in request.messages:
            if m.role == "system":
                messages.append(SystemMessage(content=m.content))
            elif m.role == "user":
                messages.append(UserMessage(content=m.content))
            elif m.role == "assistant":
                if m.tool_calls:
                    # Convert tool calls to Foundry format
                    tool_calls_list = [
                        ChatCompletionsToolCall(
                            id=tc.id,
                            function=FunctionCall(
                                name=tc.name,
                                arguments=json.dumps(tc.arguments),
                            ),
                        )
                        for tc in m.tool_calls
                    ]
                    messages.append(
                        AssistantMessage(content=m.content, tool_calls=tool_calls_list)
                    )
                else:
                    messages.append(AssistantMessage(content=m.content))
            elif m.role == "tool":
                messages.append(
                    ToolMessage(content=m.content, tool_call_id=m.tool_call_id or "")
                )

        return messages

    def _build_tools_payload(self, request: LlmRequest) -> Optional[List[Any]]:
        """Build the tools payload from LlmRequest."""
        if not request.tools:
            return None

        try:
            from azure.ai.inference.models import (
                ChatCompletionsToolDefinition,
                FunctionDefinition,
            )
        except ImportError:  # pragma: no cover
            raise ImportError("azure-ai-inference is required for tool building")

        return [
            ChatCompletionsToolDefinition(
                function=FunctionDefinition(
                    name=t.name,
                    description=t.description,
                    parameters=t.parameters,
                )
            )
            for t in request.tools
        ]

    def _extract_tool_calls_from_message(self, message: Any) -> List[ToolCall]:
        """Extract tool calls from Foundry message object."""
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
