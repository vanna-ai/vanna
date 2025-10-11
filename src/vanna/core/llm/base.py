"""
LLM domain interface.

This module contains the abstract base class for LLM services.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, List

from .models import LlmRequest, LlmResponse, LlmStreamChunk


class LlmService(ABC):
    """Service for LLM communication."""

    @abstractmethod
    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Send a request to the LLM."""
        pass

    @abstractmethod
    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        """Stream a request to the LLM.

        Args:
            request: The LLM request to stream

        Yields:
            LlmStreamChunk instances as they arrive
        """
        # This is an async generator method
        if False:  # pragma: no cover
            yield  # type: ignore

    @abstractmethod
    async def validate_tools(self, tools: List[Any]) -> List[str]:
        """Validate tool schemas and return any errors."""
        pass
