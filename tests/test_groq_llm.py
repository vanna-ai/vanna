"""Unit tests for the Groq LLM integration."""

from __future__ import annotations

import json
import sys
import types
from types import SimpleNamespace
from typing import Any, List

import pytest

from vanna.core.llm import LlmMessage, LlmRequest
from vanna.core.user import User


def _test_user() -> User:
    return User(id="u1", email="u1@example.com", group_memberships=["users"])


def _request(content: str = "hello", stream: bool = False) -> LlmRequest:
    return LlmRequest(
        user=_test_user(),
        messages=[LlmMessage(role="user", content=content)],
        stream=stream,
    )


def _build_groq_service(monkeypatch: pytest.MonkeyPatch, client: Any) -> Any:
    """Instantiate service with a mocked groq.Groq client."""
    module = types.ModuleType("groq")

    class FakeGroq:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        @property
        def chat(self) -> Any:
            return client.chat

    module.__dict__["Groq"] = FakeGroq
    monkeypatch.setitem(sys.modules, "groq", module)

    from vanna.integrations.groq import GroqLlmService

    return GroqLlmService(api_key="test-key", model="llama-3.3-70b-versatile")


class _FakeCompletions:
    def __init__(
        self, non_stream_response: Any = None, stream_events: List[Any] | None = None
    ) -> None:
        self.non_stream_response = non_stream_response
        self.stream_events = stream_events or []
        self.raise_error: Exception | None = None

    def create(self, **kwargs: Any) -> Any:
        if self.raise_error:
            raise self.raise_error
        if kwargs.get("stream"):
            return iter(self.stream_events)
        return self.non_stream_response


class _FakeClient:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.chat = SimpleNamespace(completions=completions)


@pytest.mark.groq
@pytest.mark.asyncio
async def test_send_request_basic_success(monkeypatch: pytest.MonkeyPatch) -> None:
    message = SimpleNamespace(content="Hello from Groq", tool_calls=[])
    choice = SimpleNamespace(message=message, finish_reason="stop")
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    response = SimpleNamespace(choices=[choice], usage=usage)

    client = _FakeClient(_FakeCompletions(non_stream_response=response))
    service = _build_groq_service(monkeypatch, client)

    result = await service.send_request(_request("hi"))

    assert result.content == "Hello from Groq"
    assert result.finish_reason == "stop"
    assert result.usage == {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
    }


@pytest.mark.groq
@pytest.mark.asyncio
async def test_send_request_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    response = SimpleNamespace(choices=[], usage=None)
    client = _FakeClient(_FakeCompletions(non_stream_response=response))
    service = _build_groq_service(monkeypatch, client)

    result = await service.send_request(_request())

    assert result.content is None
    assert result.tool_calls is None
    assert result.finish_reason is None


@pytest.mark.groq
@pytest.mark.asyncio
async def test_send_request_parses_tool_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    tool_fn = SimpleNamespace(name="run_sql", arguments=json.dumps({"sql": "select 1"}))
    tool_call = SimpleNamespace(id="tc_1", function=tool_fn)
    message = SimpleNamespace(content=None, tool_calls=[tool_call])
    choice = SimpleNamespace(message=message, finish_reason="tool_calls")
    response = SimpleNamespace(choices=[choice], usage=None)

    client = _FakeClient(_FakeCompletions(non_stream_response=response))
    service = _build_groq_service(monkeypatch, client)

    result = await service.send_request(_request("call tool"))

    assert result.content is None
    assert result.tool_calls is not None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "run_sql"
    assert result.tool_calls[0].arguments == {"sql": "select 1"}


@pytest.mark.groq
@pytest.mark.asyncio
async def test_send_request_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    completions = _FakeCompletions(non_stream_response=None)
    completions.raise_error = RuntimeError("groq error")
    client = _FakeClient(completions)
    service = _build_groq_service(monkeypatch, client)

    with pytest.raises(RuntimeError, match="groq error"):
        await service.send_request(_request())


@pytest.mark.groq
@pytest.mark.asyncio
async def test_stream_request_success_content_and_finish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_1 = SimpleNamespace(
        choices=[
            SimpleNamespace(delta=SimpleNamespace(content="Hello "), finish_reason=None)
        ]
    )
    event_2 = SimpleNamespace(
        choices=[
            SimpleNamespace(delta=SimpleNamespace(content="world"), finish_reason=None)
        ]
    )
    event_3 = SimpleNamespace(
        choices=[
            SimpleNamespace(delta=SimpleNamespace(content=None), finish_reason="stop")
        ]
    )

    client = _FakeClient(_FakeCompletions(stream_events=[event_1, event_2, event_3]))
    service = _build_groq_service(monkeypatch, client)

    chunks = [chunk async for chunk in service.stream_request(_request(stream=True))]

    assert len(chunks) >= 3
    assert chunks[0].content == "Hello "
    assert chunks[1].content == "world"
    assert chunks[-1].finish_reason == "stop"


@pytest.mark.groq
@pytest.mark.asyncio
async def test_stream_request_parses_tool_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tc_delta = SimpleNamespace(
        index=0,
        id="tc_stream_1",
        function=SimpleNamespace(name="run_sql", arguments='{"sql":"select 1"}'),
    )
    event_1 = SimpleNamespace(
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content=None, tool_calls=[tc_delta]),
                finish_reason=None,
            )
        ]
    )
    event_2 = SimpleNamespace(
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content=None), finish_reason="tool_calls"
            )
        ]
    )

    client = _FakeClient(_FakeCompletions(stream_events=[event_1, event_2]))
    service = _build_groq_service(monkeypatch, client)

    chunks = [chunk async for chunk in service.stream_request(_request(stream=True))]
    last = chunks[-1]

    assert last.tool_calls is not None
    assert len(last.tool_calls) == 1
    assert last.tool_calls[0].id == "tc_stream_1"
    assert last.tool_calls[0].name == "run_sql"
    assert last.tool_calls[0].arguments == {"sql": "select 1"}
    assert last.finish_reason == "tool_calls"


@pytest.mark.groq
@pytest.mark.asyncio
async def test_stream_request_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    completions = _FakeCompletions(stream_events=[])
    completions.raise_error = RuntimeError("stream failed")
    client = _FakeClient(completions)
    service = _build_groq_service(monkeypatch, client)

    with pytest.raises(RuntimeError, match="stream failed"):
        _ = [chunk async for chunk in service.stream_request(_request(stream=True))]
