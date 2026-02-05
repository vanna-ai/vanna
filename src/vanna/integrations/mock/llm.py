"""
Mock LLM service implementation for testing.

This module provides a simple mock implementation of the LlmService interface,
useful for testing and development without requiring actual LLM API calls.
"""

import asyncio
from typing import AsyncGenerator, List

from vanna.core.llm import LlmService, LlmRequest, LlmResponse, LlmStreamChunk
from vanna.core.tool import ToolSchema


class MockLlmService(LlmService):
    """Mock LLM service that returns predefined responses."""

    def __init__(self, response_content: str = "Hello! This is a mock response."):
        self.response_content = response_content
        self.call_count = 0

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Send a request to the mock LLM."""
        self.call_count += 1

        # Simulate processing delay
        await asyncio.sleep(0.1)

        # Return a simple response
        return LlmResponse(
            content=f"{self.response_content} (Request #{self.call_count})",
            finish_reason="stop",
            usage={"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
        )

    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        """Stream a request to the mock LLM."""
        self.call_count += 1

        # Split response into chunks
        words = f"{self.response_content} (Streamed #{self.call_count})".split()

        for i, word in enumerate(words):
            await asyncio.sleep(0.05)  # Simulate streaming delay

            chunk_content = word + (" " if i < len(words) - 1 else "")
            yield LlmStreamChunk(
                content=chunk_content,
                finish_reason="stop" if i == len(words) - 1 else None,
            )

    async def validate_tools(self, tools: List[ToolSchema]) -> List[str]:
        """Validate tool schemas and return any errors."""
        # Mock validation - no errors
        return []

    def set_response(self, content: str) -> None:
        """Set the response content for testing."""
        self.response_content = content

    def reset_call_count(self) -> None:
        """Reset the call counter."""
        self.call_count = 0
