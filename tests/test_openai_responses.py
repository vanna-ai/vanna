"""
Unit tests for OpenAIResponsesService (integrations/openai/responses.py).

All tests mock the openai client so no real API key is required.
Integration tests that hit the real API are marked @pytest.mark.openai
and only run when OPENAI_API_KEY is set.
"""

import pytest
import openai
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncIterator

from vanna.core.llm import LlmRequest, LlmMessage, LlmResponse
from vanna.core.tool import ToolCall, ToolSchema
from vanna.core.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_service(model: str = "gpt-test"):
    """Return an OpenAIResponsesService with a mocked AsyncOpenAI client."""
    mock_client = MagicMock()
    with patch.object(openai, "AsyncOpenAI", return_value=mock_client):
        from vanna.integrations.openai.responses import OpenAIResponsesService

        svc = OpenAIResponsesService(api_key="test-key", model=model)
    # keep a reference so tests can set up return values
    svc._mock_client = mock_client
    return svc


def make_user() -> User:
    return User(
        id="u1",
        username="tester",
        email="tester@example.com",
        group_memberships=["user"],
    )


def make_request(content: str = "Hello", tools=None) -> LlmRequest:
    return LlmRequest(
        messages=[LlmMessage(role="user", content=content)],
        user=make_user(),
        tools=tools,
        metadata={},
    )


class _FakeStream:
    """Minimal async context manager that behaves like the openai stream object."""

    def __init__(self, events, final_resp):
        self._events = events
        self._final = final_resp

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def __aiter__(self):
        return self._aiter()

    async def _aiter(self):
        for e in self._events:
            yield e

    async def get_final_response(self):
        return self._final


def _fake_resp(
    output_text=None,
    output=None,
    usage=None,
    status="completed",
    resp_id="resp_1",
):
    """Build a MagicMock that looks like an openai Responses API response."""
    resp = MagicMock()
    resp.output_text = output_text
    resp.output = output or []
    resp.usage = usage
    resp.status = status
    resp.id = resp_id
    return resp


# ---------------------------------------------------------------------------
# _serialize_tool
# ---------------------------------------------------------------------------


def test_serialize_tool_from_tool_schema():
    """_serialize_tool must convert ToolSchema → OpenAI function dict."""
    svc = make_service()
    schema = ToolSchema(
        name="run_sql",
        description="Run a SQL query",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}},
    )
    result = svc._serialize_tool(schema)

    assert result["type"] == "function"
    assert result["name"] == "run_sql"
    assert result["description"] == "Run a SQL query"
    assert result["parameters"] == schema.parameters
    assert result["strict"] is False


def test_serialize_tool_from_dict_with_name_description_parameters():
    """_serialize_tool must handle plain dict with name/description/parameters."""
    svc = make_service()
    tool_dict = {
        "name": "my_tool",
        "description": "Does something",
        "parameters": {"type": "object"},
    }
    result = svc._serialize_tool(tool_dict)

    assert result["type"] == "function"
    assert result["name"] == "my_tool"
    assert result["strict"] is False


def test_serialize_tool_from_dict_with_existing_type():
    """_serialize_tool must pass through dicts that already have 'type' key."""
    svc = make_service()
    tool_dict = {"type": "custom_tool", "name": "foo"}
    result = svc._serialize_tool(tool_dict)
    assert result == tool_dict


def test_serialize_tool_raises_for_unknown_type():
    """_serialize_tool must raise TypeError for unsupported inputs."""
    svc = make_service()
    with pytest.raises(TypeError, match="Unsupported tool schema type"):
        svc._serialize_tool(42)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _payload
# ---------------------------------------------------------------------------


def test_payload_basic():
    """_payload must include model and input messages."""
    svc = make_service(model="gpt-test")
    req = make_request("What is 2+2?")
    payload = svc._payload(req)

    assert payload["model"] == "gpt-test"
    assert len(payload["input"]) == 1
    assert payload["input"][0]["role"] == "user"
    assert payload["input"][0]["content"] == "What is 2+2?"
    assert "instructions" not in payload
    assert "tools" not in payload


def test_payload_with_system_prompt():
    """_payload must include instructions when system_prompt is set."""
    svc = make_service()
    req = make_request()
    req.system_prompt = "You are a helpful assistant."
    payload = svc._payload(req)
    assert payload["instructions"] == "You are a helpful assistant."


def test_payload_with_max_tokens():
    """_payload must include max_output_tokens when max_tokens is set."""
    svc = make_service()
    req = make_request()
    req.max_tokens = 512
    payload = svc._payload(req)
    assert payload["max_output_tokens"] == 512


def test_payload_with_tools():
    """_payload must serialize tools when present."""
    svc = make_service()
    schema = ToolSchema(
        name="run_sql",
        description="Run SQL",
        parameters={"type": "object"},
    )
    req = make_request(tools=[schema])
    payload = svc._payload(req)
    assert "tools" in payload
    assert len(payload["tools"]) == 1
    assert payload["tools"][0]["name"] == "run_sql"


# ---------------------------------------------------------------------------
# _extract
# ---------------------------------------------------------------------------


def test_extract_text_response():
    """_extract must return output_text as content."""
    svc = make_service()
    resp = _fake_resp(output_text="Hello!")
    text, tools, status, usage = svc._extract(resp)
    assert text == "Hello!"
    assert tools is None
    assert status == "completed"
    assert usage is None


def test_extract_with_usage():
    """_extract must parse usage tokens."""
    svc = make_service()
    mock_usage = MagicMock()
    mock_usage.input_tokens = 10
    mock_usage.output_tokens = 20
    mock_usage.total_tokens = None  # force computation
    resp = _fake_resp(output_text="Hi", usage=mock_usage)

    _text, _tools, _status, usage = svc._extract(resp)
    assert usage is not None
    assert usage["input_tokens"] == 10
    assert usage["output_tokens"] == 20
    assert usage["total_tokens"] == 30  # computed as input + output


def test_extract_no_tool_calls_in_plain_output():
    """_extract must return no tool_calls when output has no tool_call items."""
    svc = make_service()
    # output item has content but no tool_call type
    item = MagicMock()
    item.type = "text"
    output_item = MagicMock()
    output_item.content = [item]
    resp = _fake_resp(output=[output_item])

    _text, tools, _status, _usage = svc._extract(resp)
    assert tools is None


# ---------------------------------------------------------------------------
# validate_tools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_tools_always_empty():
    """validate_tools must return an empty list (accepts any schema)."""
    svc = make_service()
    schema = ToolSchema(name="t", description="d", parameters={})
    result = await svc.validate_tools([schema])
    assert result == []


# ---------------------------------------------------------------------------
# send_request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_request_text_only():
    """send_request must return LlmResponse with content and no tool_calls."""
    svc = make_service()
    resp = _fake_resp(output_text="42", status="completed", resp_id="r1")
    svc._mock_client.responses.create = AsyncMock(return_value=resp)

    result = await svc.send_request(make_request("What is 6x7?"))

    assert isinstance(result, LlmResponse)
    assert result.content == "42"
    assert result.tool_calls is None
    assert result.finish_reason == "completed"
    assert result.metadata.get("request_id") == "r1"


@pytest.mark.asyncio
async def test_send_request_passes_payload_to_client():
    """send_request must call client.responses.create with the built payload."""
    svc = make_service(model="gpt-foo")
    resp = _fake_resp(output_text="ok")
    svc._mock_client.responses.create = AsyncMock(return_value=resp)

    await svc.send_request(make_request("test"))

    call_kwargs = svc._mock_client.responses.create.call_args[1]
    assert call_kwargs["model"] == "gpt-foo"
    assert call_kwargs["input"][0]["content"] == "test"


# ---------------------------------------------------------------------------
# stream_request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_request_yields_text_chunks():
    """stream_request must yield LlmStreamChunk with content for text deltas."""
    svc = make_service()

    mock_event = MagicMock()
    mock_event.type = "response.output_text.delta"
    mock_event.delta = "Hello"

    final_resp = _fake_resp(output_text="Hello", status="completed")
    svc._mock_client.responses.stream.return_value = _FakeStream(
        events=[mock_event], final_resp=final_resp
    )

    chunks = []
    async for chunk in svc.stream_request(make_request("Hi")):
        chunks.append(chunk)

    text_chunks = [c for c in chunks if c.content]
    assert any(c.content == "Hello" for c in text_chunks)


@pytest.mark.asyncio
async def test_stream_request_ignores_non_delta_events():
    """stream_request must silently skip events that aren't text deltas."""
    svc = make_service()

    irrelevant_event = MagicMock()
    irrelevant_event.type = "response.created"
    irrelevant_event.delta = None

    final_resp = _fake_resp(output_text=None, status="completed")
    svc._mock_client.responses.stream.return_value = _FakeStream(
        events=[irrelevant_event], final_resp=final_resp
    )

    chunks = []
    async for chunk in svc.stream_request(make_request("Hi")):
        chunks.append(chunk)

    # No text content expected — only the final status/tool chunk
    text_chunks = [c for c in chunks if c.content is not None]
    assert len(text_chunks) == 0
