"""
Unit tests for Phase-3 local wrappers:

- RetryLlmService  (integrations/local/retry_llm.py)
- CachingLlmService (integrations/local/caching_llm.py)
- LoggingObservabilityProvider (integrations/local/logging_observability.py)

All tests are fully offline — no real LLM API calls are made.
"""

import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from vanna.core.llm import LlmMessage, LlmRequest, LlmResponse
from vanna.core.llm.models import LlmStreamChunk
from vanna.integrations.local.caching_llm import CachingLlmService, _cache_key
from vanna.integrations.local.logging_observability import LoggingObservabilityProvider
from vanna.integrations.local.retry_llm import RetryLlmService, _is_retryable


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_request(content: str = "Hello") -> LlmRequest:
    from vanna.core.user import User

    user = User(
        id="u1",
        username="tester",
        email="t@example.com",
        group_memberships=[],
    )
    return LlmRequest(
        messages=[LlmMessage(role="user", content=content)],
        user=user,
        metadata={},
    )


def _make_response(content: str = "Hi", tool_calls=None) -> LlmResponse:
    return LlmResponse(content=content, tool_calls=tool_calls)


def _make_inner(response: LlmResponse) -> MagicMock:
    """Create a mock LlmService that returns *response* on send_request."""
    inner = MagicMock()
    inner.send_request = AsyncMock(return_value=response)
    inner.validate_tools = AsyncMock(return_value=[])
    return inner


# ---------------------------------------------------------------------------
# RetryLlmService
# ---------------------------------------------------------------------------


class TestRetryLlmService:
    """Tests for RetryLlmService."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        """No retry needed — returns response immediately."""
        resp = _make_response("OK")
        inner = _make_inner(resp)
        svc = RetryLlmService(inner, max_retries=3)
        result = await svc.send_request(_make_request())
        assert result.content == "OK"
        assert inner.send_request.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_retryable_error_then_succeeds(self):
        """Retries after a retryable error and succeeds on the third attempt."""
        try:
            import httpx
        except ImportError:
            pytest.skip("httpx not installed")

        resp = _make_response("Eventually")
        inner = MagicMock()
        inner.send_request = AsyncMock(
            side_effect=[
                httpx.TimeoutException("timeout"),
                httpx.TimeoutException("timeout"),
                resp,
            ]
        )
        svc = RetryLlmService(inner, max_retries=3, base_delay=0, jitter=False)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await svc.send_request(_make_request())
        assert result.content == "Eventually"
        assert inner.send_request.call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries_exhausted(self):
        """Raises the last exception when max_retries is exhausted."""
        try:
            import httpx
        except ImportError:
            pytest.skip("httpx not installed")

        inner = MagicMock()
        inner.send_request = AsyncMock(
            side_effect=httpx.TimeoutException("always fails")
        )
        svc = RetryLlmService(inner, max_retries=2, base_delay=0, jitter=False)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(httpx.TimeoutException):
                await svc.send_request(_make_request())
        # 1 initial + 2 retries = 3 total calls
        assert inner.send_request.call_count == 3

    @pytest.mark.asyncio
    async def test_does_not_retry_non_retryable_error(self):
        """ValueError is not retryable — raises immediately without retrying."""
        inner = MagicMock()
        inner.send_request = AsyncMock(side_effect=ValueError("bad input"))
        svc = RetryLlmService(inner, max_retries=3)
        with pytest.raises(ValueError):
            await svc.send_request(_make_request())
        assert inner.send_request.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_http_429_status_error(self):
        """HTTP 429 rate-limit responses are retryable."""
        resp_mock = MagicMock()
        resp_mock.status_code = 429
        rate_limit_exc = Exception("rate limit")
        rate_limit_exc.response = resp_mock  # type: ignore[attr-defined]

        ok_resp = _make_response("OK after rate limit")
        inner = MagicMock()
        inner.send_request = AsyncMock(side_effect=[rate_limit_exc, ok_resp])
        svc = RetryLlmService(inner, max_retries=3, base_delay=0, jitter=False)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await svc.send_request(_make_request())
        assert result.content == "OK after rate limit"
        assert inner.send_request.call_count == 2

    @pytest.mark.asyncio
    async def test_stream_success_no_retry(self):
        """Successful stream passes chunks through unchanged."""

        async def _gen():
            yield LlmStreamChunk(content="Hello")
            yield LlmStreamChunk(content=" world")

        inner = MagicMock()
        inner.stream_request = MagicMock(return_value=_gen())
        svc = RetryLlmService(inner)
        chunks = [c async for c in svc.stream_request(_make_request())]
        assert [c.content for c in chunks] == ["Hello", " world"]

    @pytest.mark.asyncio
    async def test_stream_does_not_retry_after_chunks_yielded(self):
        """Once chunks have been yielded, errors must NOT be retried."""

        async def _gen_fail_mid():
            yield LlmStreamChunk(content="partial")
            raise RuntimeError("mid-stream failure")

        inner = MagicMock()
        inner.stream_request = MagicMock(return_value=_gen_fail_mid())
        svc = RetryLlmService(inner, max_retries=3)

        with pytest.raises(RuntimeError, match="mid-stream failure"):
            async for _ in svc.stream_request(_make_request()):
                pass
        # Only one stream attempt — no retry after chunks started flowing
        assert inner.stream_request.call_count == 1

    def test_is_retryable_returns_false_for_value_error(self):
        assert _is_retryable(ValueError("nope")) is False

    def test_is_retryable_returns_true_for_http_500(self):
        exc = Exception("server error")
        resp = MagicMock()
        resp.status_code = 500
        exc.response = resp  # type: ignore[attr-defined]
        assert _is_retryable(exc) is True

    @pytest.mark.asyncio
    async def test_validate_tools_delegates_to_inner(self):
        inner = MagicMock()
        inner.validate_tools = AsyncMock(return_value=["unsupported"])
        svc = RetryLlmService(inner)
        result = await svc.validate_tools(["tool1"])
        assert result == ["unsupported"]


# ---------------------------------------------------------------------------
# CachingLlmService
# ---------------------------------------------------------------------------


class TestCachingLlmService:
    """Tests for CachingLlmService."""

    @pytest.mark.asyncio
    async def test_cache_miss_then_hit(self):
        """Second identical request returns cached response (1 upstream call)."""
        resp = _make_response("cached answer")
        inner = _make_inner(resp)
        svc = CachingLlmService(inner, max_size=10)

        req = _make_request("What is 2+2?")
        r1 = await svc.send_request(req)
        r2 = await svc.send_request(req)

        assert r1.content == r2.content == "cached answer"
        assert inner.send_request.call_count == 1
        assert svc.stats == {"hits": 1, "misses": 1, "size": 1}

    @pytest.mark.asyncio
    async def test_different_requests_are_separate_cache_entries(self):
        """Two requests with different content get separate cache entries."""
        inner = MagicMock()
        inner.send_request = AsyncMock(
            side_effect=[_make_response("A"), _make_response("B")]
        )
        svc = CachingLlmService(inner)
        r1 = await svc.send_request(_make_request("Q1"))
        r2 = await svc.send_request(_make_request("Q2"))
        assert r1.content == "A"
        assert r2.content == "B"
        assert svc.stats["size"] == 2

    @pytest.mark.asyncio
    async def test_tool_call_response_not_cached(self):
        """Responses with tool_calls must never be cached."""
        from vanna.core.tool import ToolCall

        tc = ToolCall(id="tc1", name="run_sql", arguments={"query": "SELECT 1"})
        resp = _make_response(tool_calls=[tc])
        inner = _make_inner(resp)
        svc = CachingLlmService(inner)

        req = _make_request("run it")
        await svc.send_request(req)
        await svc.send_request(req)  # second call must hit inner again

        assert inner.send_request.call_count == 2
        assert svc.stats["size"] == 0

    @pytest.mark.asyncio
    async def test_eviction_when_cache_full(self):
        """Oldest entry is evicted when max_size is reached."""
        inner = MagicMock()
        inner.send_request = AsyncMock(
            side_effect=[_make_response(str(i)) for i in range(4)]
        )
        svc = CachingLlmService(inner, max_size=2)

        await svc.send_request(_make_request("Q1"))
        await svc.send_request(_make_request("Q2"))
        assert svc.stats["size"] == 2

        # Q3 causes eviction of Q1
        await svc.send_request(_make_request("Q3"))
        assert svc.stats["size"] == 2

    @pytest.mark.asyncio
    async def test_invalidate_clears_cache(self):
        """invalidate() removes all cached entries."""
        resp = _make_response("hi")
        inner = _make_inner(resp)
        svc = CachingLlmService(inner)

        await svc.send_request(_make_request("hello"))
        assert svc.stats["size"] == 1

        svc.invalidate()
        assert svc.stats["size"] == 0

        # Next call should miss again
        await svc.send_request(_make_request("hello"))
        assert inner.send_request.call_count == 2

    @pytest.mark.asyncio
    async def test_stream_always_passes_through(self):
        """Streaming responses are never cached — always delegated to inner."""

        async def _gen():
            yield LlmStreamChunk(content="stream chunk")

        inner = MagicMock()
        inner.stream_request = MagicMock(return_value=_gen())
        svc = CachingLlmService(inner)
        chunks = [c async for c in svc.stream_request(_make_request())]
        assert chunks[0].content == "stream chunk"

    @pytest.mark.asyncio
    async def test_validate_tools_delegates(self):
        inner = MagicMock()
        inner.validate_tools = AsyncMock(return_value=[])
        svc = CachingLlmService(inner)
        assert await svc.validate_tools([]) == []

    def test_cache_key_excludes_user_and_metadata(self):
        """Two requests differing only in user/metadata share the same key."""
        from vanna.core.user import User

        u1 = User(id="alice", username="a", email="a@x.com", group_memberships=[])
        u2 = User(id="bob", username="b", email="b@x.com", group_memberships=[])

        req1 = LlmRequest(
            messages=[LlmMessage(role="user", content="same")],
            user=u1,
            metadata={"session": "s1"},
        )
        req2 = LlmRequest(
            messages=[LlmMessage(role="user", content="same")],
            user=u2,
            metadata={"session": "s2"},
        )
        assert _cache_key(req1) == _cache_key(req2)

    def test_cache_key_differs_for_different_content(self):
        req1 = _make_request("Hello")
        req2 = _make_request("Goodbye")
        assert _cache_key(req1) != _cache_key(req2)

    def test_stats_initial_values(self):
        inner = MagicMock()
        svc = CachingLlmService(inner)
        assert svc.stats == {"hits": 0, "misses": 0, "size": 0}


# ---------------------------------------------------------------------------
# LoggingObservabilityProvider
# ---------------------------------------------------------------------------


class TestLoggingObservabilityProvider:
    """Tests for LoggingObservabilityProvider."""

    @pytest.mark.asyncio
    async def test_create_span_returns_span_with_correct_name(self):
        obs = LoggingObservabilityProvider()
        span = await obs.create_span("test_operation", {"key": "value"})
        assert span.name == "test_operation"
        assert span.attributes == {"key": "value"}
        assert span.end_time is None  # not yet ended

    @pytest.mark.asyncio
    async def test_end_span_sets_end_time(self):
        obs = LoggingObservabilityProvider()
        span = await obs.create_span("op")
        await obs.end_span(span)
        assert span.end_time is not None
        assert span.duration_ms() is not None
        assert span.duration_ms() >= 0

    @pytest.mark.asyncio
    async def test_create_span_logs_at_configured_level(self, caplog):
        obs = LoggingObservabilityProvider(span_log_level=logging.INFO)
        with caplog.at_level(logging.INFO, logger="vanna.integrations.local.logging_observability"):
            span = await obs.create_span("my_span")
        assert any("SPAN START" in r.message and "my_span" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_end_span_logs_duration(self, caplog):
        obs = LoggingObservabilityProvider(span_log_level=logging.INFO)
        with caplog.at_level(logging.INFO, logger="vanna.integrations.local.logging_observability"):
            span = await obs.create_span("timed_op")
            caplog.clear()
            await obs.end_span(span)
        end_records = [r for r in caplog.records if "SPAN END" in r.message]
        assert len(end_records) == 1
        assert "timed_op" in end_records[0].message
        assert "ms" in end_records[0].message

    @pytest.mark.asyncio
    async def test_record_metric_logs_name_and_value(self, caplog):
        obs = LoggingObservabilityProvider(metric_log_level=logging.INFO)
        with caplog.at_level(logging.INFO, logger="vanna.integrations.local.logging_observability"):
            await obs.record_metric("agent.tokens", 512.0, unit="tokens", tags={"model": "gpt-4"})
        metric_records = [r for r in caplog.records if "METRIC" in r.message]
        assert len(metric_records) == 1
        assert "agent.tokens" in metric_records[0].message
        assert "512.0tokens" in metric_records[0].message
        assert "gpt-4" in metric_records[0].message

    @pytest.mark.asyncio
    async def test_record_metric_no_tags(self, caplog):
        obs = LoggingObservabilityProvider(metric_log_level=logging.INFO)
        with caplog.at_level(logging.INFO, logger="vanna.integrations.local.logging_observability"):
            await obs.record_metric("requests.total", 1.0)
        assert any("requests.total" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_create_span_no_attributes(self):
        obs = LoggingObservabilityProvider()
        span = await obs.create_span("bare_span")
        assert span.attributes == {}

    @pytest.mark.asyncio
    async def test_span_id_in_log(self, caplog):
        obs = LoggingObservabilityProvider(span_log_level=logging.INFO)
        with caplog.at_level(logging.INFO, logger="vanna.integrations.local.logging_observability"):
            span = await obs.create_span("id_check")
        # First 8 chars of the UUID should appear
        assert any(span.id[:8] in r.message for r in caplog.records)
