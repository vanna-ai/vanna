"""
OVH Mistral LLM Integration for Vanna 2.0

This file is the translator between Vanna and OVH's Mistral API.
Why? Vanna speaks "universal LLM", Mistral speaks "Mistral API" - we translate!
"""

from __future__ import annotations

import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from vanna.core.llm import (
    LlmService,      
    LlmRequest,    
    LlmResponse,    
    LlmStreamChunk,  
)
from vanna.core.tool import ToolCall, ToolSchema


class OvhMistralLlmService(LlmService):
    """
    OVH Mistral LLM Service - The Translator Robot 🤖
    
    Job: Make Vanna and OVH Mistral talk to each other
    
    Usage:
        llm = OvhMistralLlmService(
            api_key="your-key",
            model="Mistral-Small-3.2-24B-Instruct-2506",
            base_url="https://oai.endpoints.kepler.ai.cloud.ovh.net"
        )
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **extra_client_kwargs: Any,
    ) -> None:
        """
        Setup the robot - give it the phone number (API key) and address (base_url).
        
        Args:
            model: Which Mistral brain to use (e.g., "Mistral-Small-3.2-24B-Instruct-2506")
            api_key: Your OVH password (or set MISTRAL_API_KEY in .env)
            base_url: OVH's server address (or set MISTRAL_BASE_URL in .env)
        """
        try:
            from mistralai import Mistral
        except ImportError as e:
            raise ImportError(
                "❌ mistralai package missing!\n"
                "Fix: pip install mistralai"
            ) from e

        self.model = model or os.getenv("MISTRAL_MODEL", "Mistral-Small-3.2-24B-Instruct-2506")
        api_key = api_key or os.getenv("MISTRAL_API_KEY")
        base_url = base_url or os.getenv("MISTRAL_API_URL")

        if api_key:
            api_key = api_key.strip()
        if base_url:
            base_url = base_url.strip().replace("/v1/chat/completions", "")

        client_kwargs: Dict[str, Any] = {**extra_client_kwargs}
        
        if not api_key:
            raise ValueError("❌ API key required! Set MISTRAL_API_KEY or pass api_key=")
        
        client_kwargs["api_key"] = api_key
        
        if base_url:
            client_kwargs["server_url"] = base_url
            logger.info(f"🔗 Using custom OVH endpoint: {base_url}")

        self._client = Mistral(**client_kwargs)
        logger.info(f"✅ OVH Mistral ready! Model: {self.model}")

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """
        Send a question to OVH Mistral and wait for the full answer.
        
        This is like sending a text message and waiting for a reply.
        
        Flow:
        1. Translate Vanna's request to Mistral format (_build_payload)
        2. Send to OVH API (self._client.chat.complete)
        3. Parse the response (_parse_response)
        4. Return to Vanna in universal format
        """
        payload = self._build_payload(request)
        
        logger.debug(f"📤 Sending to OVH Mistral: {payload}")

        response = self._client.chat.complete(**payload)
        
        logger.debug(f"📥 Got response from OVH Mistral")

        text_content, tool_calls = self._parse_response(response)

        usage: Dict[str, int] = {}
        if hasattr(response, "usage") and response.usage:
            usage = {
                "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                "output_tokens": getattr(response.usage, "completion_tokens", 0),
            }

        return LlmResponse(
            content=text_content or None,
            tool_calls=tool_calls or None,
            finish_reason=self._get_finish_reason(response),
            usage=usage or None,
        )

    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        """
        Stream a response from OVH Mistral word-by-word.
        
        This is like watching someone type in real-time.
        Why? Users want to see text appearing live, not wait for everything.
        """
        payload = self._build_payload(request)
        
        logger.debug(f"📤 Streaming from OVH Mistral...")

        with self._client.chat.stream(**payload) as stream:
            for chunk in stream:
                # Extract text from this chunk
                if hasattr(chunk, "data") and chunk.data:
                    delta = chunk.data.choices[0].delta if chunk.data.choices else None
                    if delta and hasattr(delta, "content") and delta.content:
                        yield LlmStreamChunk(content=delta.content)

        yield LlmStreamChunk(finish_reason="stop")

    async def validate_tools(self, tools: List[ToolSchema]) -> List[str]:
        """
        Check if tools are valid before sending to OVH.
        
        Why? Catch errors early (before wasting API calls).
        Example: If a tool has no name, we return an error.
        """
        errors: List[str] = []
        for tool in tools:
            if not tool.name:
                errors.append("Tool must have a name")
        return errors


    def _build_payload(self, request: LlmRequest) -> Dict[str, Any]:
        """
        Convert Vanna's request to Mistral's API format.
        
        Why? Like filling out a form - Vanna gives us sticky notes,
        we write it on the official form Mistral requires.
        """
        messages = []
        
       
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        for msg in request.messages:
            message_dict: Dict[str, Any] = {
                "role": msg.role,  # "user", "assistant", or "tool"
                "content": msg.content or ""
            }
            
          
            if msg.role == "tool" and hasattr(msg, "tool_call_id"):
                message_dict["tool_call_id"] = msg.tool_call_id
            
            messages.append(message_dict)

        # ayload dictionary
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": request.max_tokens or 1024,  
        }
        
        if request.temperature is not None:
            payload["temperature"] = request.temperature

            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.parameters or {"type": "object", "properties": {}}
                    }
                }
                for tool in request.tools
            ]

        return payload

    def _parse_response(self, response: Any) -> Tuple[str, List[ToolCall]]:
        """
        Extract text and tool calls from Mistral's response.
        
        Why? Mistral returns nested JSON (like Russian dolls 🪆).
        We dig through to get the actual text.
        
        Mistral's format:
        {
          "choices": [
            {
              "message": {
                "content": "Hello!",
                "tool_calls": [...]
              }
            }
          ]
        }
        """
        text_content = ""
        tool_calls: List[ToolCall] = []

        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]  # Usually only one choice
            message = getattr(choice, "message", None)
            
            if message:
                if hasattr(message, "content") and message.content:
                    text_content = message.content
                
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tc in message.tool_calls:
                        tool_calls.append(
                            ToolCall(
                                id=tc.id,
                                name=tc.function.name,
                                arguments=tc.function.arguments
                            )
                        )

        return text_content, tool_calls

    def _get_finish_reason(self, response: Any) -> Optional[str]:
        """
        Get why the AI stopped talking.
        
        Reasons:
        - "stop" = Finished naturally
        - "length" = Hit max_tokens limit
        - "tool_calls" = Wants to call a function
        
        Why? Vanna needs to know if it should continue (tool call) or stop.
        """
        if hasattr(response, "choices") and response.choices:
            return getattr(response.choices[0], "finish_reason", None)
        return None