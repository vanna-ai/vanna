"""
Base LLM middleware interface.

Middleware allows you to intercept and transform LLM requests and responses
for caching, monitoring, content filtering, and more.
"""

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..llm import LlmRequest, LlmResponse


class LlmMiddleware(ABC):
    """Middleware for intercepting LLM requests and responses.

    Subclass this to create custom middleware that can:
    - Cache LLM responses
    - Log requests/responses
    - Filter or modify content
    - Track costs and usage
    - Implement fallback strategies

    Example:
        class CachingMiddleware(LlmMiddleware):
            def __init__(self):
                self.cache = {}

            async def before_llm_request(self, request: LlmRequest) -> LlmRequest:
                # Could check cache here
                return request

            async def after_llm_response(self, request: LlmRequest, response: LlmResponse) -> LlmResponse:
                # Cache the response
                cache_key = self._compute_key(request)
                self.cache[cache_key] = response
                return response

        agent = AgentRunner(
            llm_service=...,
            llm_middlewares=[CachingMiddleware(), LoggingMiddleware()]
        )
    """

    async def before_llm_request(self, request: "LlmRequest") -> "LlmRequest":
        """Called before sending request to LLM.

        Args:
            request: The LLM request about to be sent

        Returns:
            Modified request, or original if no changes
        """
        return request

    async def after_llm_response(
        self, request: "LlmRequest", response: "LlmResponse"
    ) -> "LlmResponse":
        """Called after receiving response from LLM.

        Args:
            request: The original request
            response: The LLM response

        Returns:
            Modified response, or original if no changes
        """
        return response
