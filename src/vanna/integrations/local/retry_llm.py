"""
RetryLlmService — LlmService wrapper with exponential-backoff retry.

Retries transient failures (network timeouts, 429 rate-limits, 5xx errors)
so a single blip doesn't crash the whole agent run.

Usage::

    from vanna.integrations.anthropic import AnthropicLlmService
    from vanna.integrations.local.retry_llm import RetryLlmService

    base_llm = AnthropicLlmService(api_key="...")
    llm = RetryLlmService(base_llm, max_retries=3)
    agent = Agent(llm_service=llm, ...)
"""

import asyncio
import logging
import random
from typing import Any, AsyncGenerator, List, Optional, Tuple, Type

from vanna.core.llm import LlmRequest, LlmResponse, LlmService, LlmStreamChunk

logger = logging.getLogger(__name__)

# httpx is a core dependency of vanna; import lazily so the module can be
# imported even in environments where httpx isn't on sys.path yet.
_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = ()

try:
    import httpx

    _RETRYABLE_EXCEPTIONS = (
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.RemoteProtocolError,
    )
except ImportError:  # pragma: no cover
    pass

# HTTP status codes that are safe to retry
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable(exc: Exception) -> bool:
    """Return True if the exception represents a transient failure."""
    if _RETRYABLE_EXCEPTIONS and isinstance(exc, _RETRYABLE_EXCEPTIONS):
        return True
    # Handle httpx.HTTPStatusError and similar wrappers
    response = getattr(exc, "response", None)
    if response is not None:
        status = getattr(response, "status_code", None)
        if status in _RETRYABLE_STATUS_CODES:
            return True
    return False


class RetryLlmService(LlmService):
    """LlmService decorator that retries transient failures with exponential backoff.

    Args:
        inner: The underlying LlmService to wrap.
        max_retries: Maximum number of retry attempts (default 3).
        base_delay: Initial backoff delay in seconds (default 1.0).
        max_delay: Maximum backoff delay in seconds (default 30.0).
        jitter: Apply ±50 % random jitter to each delay (default True).
    """

    def __init__(
        self,
        inner: LlmService,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        jitter: bool = True,
    ) -> None:
        self.inner = inner
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

    def _delay(self, attempt: int) -> float:
        delay = min(self.base_delay * (2**attempt), self.max_delay)
        if self.jitter:
            delay *= random.uniform(0.5, 1.5)
        return delay

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        for attempt in range(self.max_retries + 1):
            try:
                return await self.inner.send_request(request)
            except Exception as exc:
                if not _is_retryable(exc) or attempt == self.max_retries:
                    raise
                delay = self._delay(attempt)
                logger.warning(
                    "LLM send_request failed (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1,
                    self.max_retries + 1,
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)
        raise RuntimeError("Unreachable")  # pragma: no cover

    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        """Retry stream only if the error occurs before any chunks are yielded.

        Once chunks have started flowing, re-raising is the only safe option
        because the caller may already have accumulated partial content.
        """
        for attempt in range(self.max_retries + 1):
            chunks_yielded = 0
            try:
                async for chunk in self.inner.stream_request(request):
                    chunks_yielded += 1
                    yield chunk
                return  # stream completed successfully
            except Exception as exc:
                # If data already started, propagate immediately — retrying
                # would produce duplicate chunks in the caller's accumulator.
                if chunks_yielded > 0 or not _is_retryable(exc) or attempt == self.max_retries:
                    raise
                delay = self._delay(attempt)
                logger.warning(
                    "LLM stream_request failed before first chunk "
                    "(attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1,
                    self.max_retries + 1,
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)

    async def validate_tools(self, tools: List[Any]) -> List[str]:
        return await self.inner.validate_tools(tools)
