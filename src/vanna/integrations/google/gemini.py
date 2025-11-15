"""
Google Gemini LLM service implementation.

Implements the LlmService interface using Google's Gen AI SDK
(google-genai). Supports non-streaming and streaming text output,
as well as function calling (tool use).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

logger = logging.getLogger(__name__)

from vanna.core.llm import (
    LlmService,
    LlmRequest,
    LlmResponse,
    LlmStreamChunk,
)
from vanna.core.tool import ToolCall, ToolSchema


class GeminiLlmService(LlmService):
    """Google Gemini-backed LLM service.

    Args:
        model: Gemini model name (e.g., "gemini-2.5-pro", "gemini-2.5-flash").
            Defaults to "gemini-2.5-pro". Can also be set via GEMINI_MODEL env var.
        api_key: API key; falls back to env `GOOGLE_API_KEY` or `GEMINI_API_KEY`.
            GOOGLE_API_KEY takes precedence if both are set.
        temperature: Temperature for generation (0.0-2.0). Default 0.7.
        extra_config: Extra kwargs forwarded to GenerateContentConfig.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        **extra_config: Any,
    ) -> None:
        try:
            from google import genai
            from google.genai import types
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "google-genai package is required. "
                "Install with: pip install 'vanna[gemini]'"
            ) from e

        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
        # Check GOOGLE_API_KEY first (takes precedence), then GEMINI_API_KEY
        api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "Google API key is required. Set GOOGLE_API_KEY or GEMINI_API_KEY "
                "environment variable, or pass api_key parameter."
            )

        # Store modules for use in methods
        self._genai = genai
        self._types = types

        # Create client
        self._client = genai.Client(api_key=api_key)

        # Store generation config
        self.temperature = temperature
        self.extra_config = extra_config

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Send a non-streaming request to Gemini and return the response."""
        contents, config = self._build_payload(request)

        try:
            # Generate content
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            logger.info(f"Gemini response: {response}")

            # Parse response
            text_content, tool_calls = self._parse_response(response)

            # Extract usage information
            usage: Dict[str, int] = {}
            if hasattr(response, "usage_metadata"):
                try:
                    usage = {
                        "prompt_tokens": int(
                            response.usage_metadata.prompt_token_count
                        ),
                        "completion_tokens": int(
                            response.usage_metadata.candidates_token_count
                        ),
                        "total_tokens": int(response.usage_metadata.total_token_count),
                    }
                except Exception:
                    pass

            # Get finish reason
            finish_reason = None
            if response.candidates:
                finish_reason = str(response.candidates[0].finish_reason).lower()

            return LlmResponse(
                content=text_content or None,
                tool_calls=tool_calls or None,
                finish_reason=finish_reason,
                usage=usage or None,
            )

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise

    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        """Stream a request to Gemini.

        Yields text chunks as they arrive. Emits tool calls at the end.
        """
        contents, config = self._build_payload(request)

        logger.info(f"Gemini streaming request with model: {self.model_name}")

        try:
            # Stream content
            stream = self._client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            # Accumulate chunks for tool calls
            accumulated_chunks = []

            for chunk in stream:
                accumulated_chunks.append(chunk)

                # Yield text content as it arrives
                if hasattr(chunk, "text") and chunk.text:
                    yield LlmStreamChunk(content=chunk.text)

            # After stream completes, check for tool calls in accumulated response
            if accumulated_chunks:
                final_chunk = accumulated_chunks[-1]
                _, tool_calls = self._parse_response_chunk(final_chunk)

                finish_reason = None
                if final_chunk.candidates:
                    finish_reason = str(final_chunk.candidates[0].finish_reason).lower()

                if tool_calls:
                    yield LlmStreamChunk(
                        tool_calls=tool_calls,
                        finish_reason=finish_reason,
                    )
                else:
                    yield LlmStreamChunk(finish_reason=finish_reason or "stop")

        except Exception as e:
            logger.error(f"Error streaming from Gemini API: {e}")
            raise

    async def validate_tools(self, tools: List[ToolSchema]) -> List[str]:
        """Basic validation of tool schemas for Gemini."""
        errors: List[str] = []
        for t in tools:
            if not t.name:
                errors.append("Tool name is required")
            if not t.description:
                errors.append(f"Tool {t.name}: description is required")
        return errors

    # Internal helpers
    def _build_payload(self, request: LlmRequest) -> tuple[List[Any], Any]:
        """Build the payload for Gemini API.

        Returns:
            Tuple of (contents, config)
        """
        # Build contents (messages) for Gemini
        contents = []

        # System prompt handling - Gemini supports system instructions in config
        system_instruction = None
        if request.system_prompt:
            system_instruction = request.system_prompt

        for m in request.messages:
            # Map roles: user -> user, assistant -> model, tool -> function
            if m.role == "user":
                contents.append(
                    self._types.Content(
                        role="user", parts=[self._types.Part(text=m.content)]
                    )
                )
            elif m.role == "assistant":
                parts = []

                # Add text content if present
                if m.content and m.content.strip():
                    parts.append(self._types.Part(text=m.content))

                # Add tool calls if present
                if m.tool_calls:
                    for tc in m.tool_calls:
                        parts.append(
                            self._types.Part(
                                function_call=self._types.FunctionCall(
                                    name=tc.name, args=tc.arguments
                                )
                            )
                        )

                if parts:
                    contents.append(self._types.Content(role="model", parts=parts))

            elif m.role == "tool":
                # Tool results in Gemini format
                if m.tool_call_id:
                    # Parse the content as JSON if possible
                    try:
                        response_content = json.loads(m.content)
                    except (json.JSONDecodeError, TypeError):
                        response_content = {"result": m.content}

                    # Extract function name from tool_call_id or use a default
                    function_name = m.tool_call_id.replace("call_", "")

                    contents.append(
                        self._types.Content(
                            role="function",
                            parts=[
                                self._types.Part(
                                    function_response=self._types.FunctionResponse(
                                        name=function_name, response=response_content
                                    )
                                )
                            ],
                        )
                    )

        # Build tools configuration if tools are provided
        tools = None
        if request.tools:
            function_declarations = []
            for tool in request.tools:
                # Clean schema to remove unsupported fields
                cleaned_parameters = self._clean_schema_for_gemini(tool.parameters)

                function_declarations.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": cleaned_parameters,
                    }
                )

            if function_declarations:
                tools = [self._types.Tool(function_declarations=function_declarations)]

        # Build generation config
        config_dict = {
            "temperature": request.temperature,
            **self.extra_config,
        }

        if request.max_tokens is not None:
            config_dict["max_output_tokens"] = request.max_tokens

        if tools:
            config_dict["tools"] = tools

        if system_instruction:
            config_dict["system_instruction"] = system_instruction

        config = self._types.GenerateContentConfig(**config_dict)

        return contents, config

    def _parse_response(self, response: Any) -> tuple[str, List[ToolCall]]:
        """Parse a Gemini response into text and tool calls."""
        text_parts: List[str] = []
        tool_calls: List[ToolCall] = []

        if not response.candidates:
            return "", []

        candidate = response.candidates[0]

        if (
            hasattr(candidate, "content")
            and candidate.content
            and hasattr(candidate.content, "parts")
            and candidate.content.parts
        ):
            for part in candidate.content.parts:
                # Check for text content
                if hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

                # Check for function calls
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    # Convert function call to ToolCall
                    tool_calls.append(
                        ToolCall(
                            id=f"call_{fc.name}",  # Generate an ID
                            name=fc.name,
                            arguments=dict(fc.args) if hasattr(fc, "args") else {},
                        )
                    )

        text_content = "".join(text_parts)
        return text_content, tool_calls

    def _parse_response_chunk(self, chunk: Any) -> tuple[str, List[ToolCall]]:
        """Parse a streaming chunk (same logic as _parse_response)."""
        return self._parse_response(chunk)

    def _clean_schema_for_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Clean JSON Schema to only include fields supported by Gemini.

        Gemini only supports a subset of OpenAPI schema. This removes unsupported
        fields like 'title', 'default', '$schema', etc.

        Supported fields:
        - type, description, enum
        - properties, required, items (for objects/arrays)
        """
        if not isinstance(schema, dict):
            return schema

        # Fields that Gemini supports
        allowed_fields = {
            "type",
            "description",
            "enum",
            "properties",
            "required",
            "items",
            "format",
        }

        cleaned = {}
        for key, value in schema.items():
            if key in allowed_fields:
                # Recursively clean nested schemas
                if key == "properties" and isinstance(value, dict):
                    cleaned[key] = {
                        prop_name: self._clean_schema_for_gemini(prop_schema)
                        for prop_name, prop_schema in value.items()
                    }
                elif key == "items" and isinstance(value, dict):
                    cleaned[key] = self._clean_schema_for_gemini(value)
                else:
                    cleaned[key] = value

        return cleaned
