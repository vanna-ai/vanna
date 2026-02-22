"""
CachingLlmService — LlmService wrapper with in-memory response caching.

Caches deterministic, non-tool-call LlmResponses so repeated identical
queries never hit the upstream LLM API, reducing cost and latency.

Responses that contain tool_calls are intentionally NOT cached because
tool calls may carry provider-specific state (e.g. Gemini thought_signature).
Streaming requests are also never cached.

Usage::

    from vanna.integrations.anthropic import AnthropicLlmService
    from vanna.integrations.local.caching_llm import CachingLlmService

    base_llm = AnthropicLlmService(api_key="...")
    llm = CachingLlmService(base_llm, max_size=256)
    agent = Agent(llm_service=llm, ...)

    # Inspect stats
    print(llm.stats)   # {"hits": 3, "misses": 10, "size": 10}
    llm.invalidate()   # clear all cached entries
"""

import hashlib
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from vanna.core.llm import LlmRequest, LlmResponse, LlmService, LlmStreamChunk

logger = logging.getLogger(__name__)


def _cache_key(request: LlmRequest) -> str:
    """Compute a deterministic SHA-256 key for an LlmRequest.

    Includes system_prompt, messages, tools, temperature, and max_tokens.
    The ``user`` field and ``metadata`` are intentionally excluded so that
    two users sending the same question share cached answers.
    """
    key_data = {
        "system_prompt": request.system_prompt,
        "messages": [
            {"role": m.role, "content": m.content} for m in request.messages
        ],
        "tools": [
            t.model_dump() if hasattr(t, "model_dump") else str(t)
            for t in (request.tools or [])
        ],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }
    serialized = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


class CachingLlmService(LlmService):
    """LlmService decorator with an LRU-style in-memory response cache.

    Args:
        inner: The underlying LlmService to wrap.
        max_size: Maximum number of entries to keep. When the cache is full,
            the oldest entry (insertion order) is evicted. ``None`` means
            unlimited (not recommended for long-running servers).
    """

    def __init__(
        self,
        inner: LlmService,
        max_size: Optional[int] = 512,
    ) -> None:
        self.inner = inner
        self.max_size = max_size
        self._cache: Dict[str, LlmResponse] = {}
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> Dict[str, int]:
        """Return cache hit/miss/size counters."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
        }

    def invalidate(self) -> None:
        """Evict all cached entries."""
        self._cache.clear()
        logger.debug("Cache invalidated")

    def _evict_if_full(self) -> None:
        if self.max_size and len(self._cache) >= self.max_size:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
            logger.debug("Cache evicted oldest entry (max_size=%d)", self.max_size)

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        key = _cache_key(request)

        if key in self._cache:
            self._hits += 1
            logger.debug("Cache HIT  (key=%.8s, hits=%d)", key, self._hits)
            return self._cache[key]

        self._misses += 1
        logger.debug("Cache MISS (key=%.8s, misses=%d)", key, self._misses)

        response = await self.inner.send_request(request)

        # Only cache pure-text responses — tool-call responses carry state.
        if not response.tool_calls:
            self._evict_if_full()
            self._cache[key] = response
            logger.debug(
                "Cached response (key=%.8s, cache_size=%d)", key, len(self._cache)
            )

        return response

    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        # Streaming responses are never cached — pass through unchanged.
        async for chunk in self.inner.stream_request(request):
            yield chunk

    async def validate_tools(self, tools: List[Any]) -> List[str]:
        return await self.inner.validate_tools(tools)
