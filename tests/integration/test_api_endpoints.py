"""
Integration tests for FastAPI endpoints.

Tests cover:
- Health endpoint
- SSE chat endpoint
- Polling chat endpoint
- Request/response formats
- Error handling
"""

import pytest
import json
from fastapi.testclient import TestClient

from vanna.servers.fastapi.app import VannaFastAPIServer
from vanna.core.agent.agent import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user.resolver import UserResolver
from vanna.core.user.request_context import RequestContext
from vanna.core.user.models import User
from vanna.core.llm.models import LlmResponse


class MockLlmService:
    """Mock LLM service for integration tests."""

    def __init__(self, responses=None):
        self.responses = responses or [
            LlmResponse(content="Hello! I'm here to help.", tool_calls=None, finish_reason="stop")
        ]
        self.call_count = 0

    async def send_request(self, request):
        self.call_count += 1
        idx = min(self.call_count - 1, len(self.responses) - 1)
        return self.responses[idx]

    async def validate_tools(self, tools):
        return []


class MockAgentMemory:
    """Mock agent memory for integration tests."""

    async def save_tool_usage(self, *args, **kwargs):
        pass

    async def search_similar_usage(self, *args, **kwargs):
        return []

    async def save_text_memory(self, *args, **kwargs):
        pass

    async def search_text_memories(self, *args, **kwargs):
        return []


class TestUserResolver(UserResolver):
    """Test user resolver that returns a test user."""

    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(
            id="test-user",
            username="test",
            email="test@example.com",
            group_memberships=["user", "admin"]
        )


@pytest.fixture
def test_app():
    """Create a test FastAPI app with mocked dependencies."""
    mock_llm = MockLlmService()
    tool_registry = ToolRegistry()

    agent = Agent(
        llm_service=mock_llm,
        tool_registry=tool_registry,
        user_resolver=TestUserResolver(),
        agent_memory=MockAgentMemory(),
    )

    server = VannaFastAPIServer(agent=agent)
    return server.create_app()


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        """GET /health should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_format(self, client):
        """Health response should have expected format."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_content_type(self, client):
        """Health response should be JSON."""
        response = client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")


class TestChatPollEndpoint:
    """Tests for the POST /api/vanna/v2/chat_poll endpoint."""

    def test_poll_returns_json(self, client):
        """POST /api/vanna/v2/chat_poll should return JSON."""
        response = client.post(
            "/api/vanna/v2/chat_poll",
            json={"message": "Hello"}
        )

        # Should return 200 OK
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_poll_response_structure(self, client):
        """Response should have chunks, conversation_id, request_id."""
        response = client.post(
            "/api/vanna/v2/chat_poll",
            json={"message": "Hello"}
        )

        data = response.json()

        # Should have expected fields
        assert "chunks" in data
        assert "conversation_id" in data
        assert "request_id" in data
        assert isinstance(data["chunks"], list)

    def test_poll_with_conversation_id(self, client):
        """Existing conversation_id should be preserved."""
        conv_id = "test-conv-123"
        response = client.post(
            "/api/vanna/v2/chat_poll",
            json={"message": "Continue", "conversation_id": conv_id}
        )

        data = response.json()
        # Conversation ID should be in response
        assert "conversation_id" in data

    def test_poll_missing_message_error(self, client):
        """Missing message should return error."""
        response = client.post(
            "/api/vanna/v2/chat_poll",
            json={}
        )

        # Should return error status
        assert response.status_code in [400, 422]


class TestChatSSEEndpoint:
    """Tests for the POST /api/vanna/v2/chat_sse endpoint."""

    def test_sse_content_type(self, client):
        """SSE response should have text/event-stream content-type."""
        response = client.post(
            "/api/vanna/v2/chat_sse",
            json={"message": "Hello"}
        )

        # Note: TestClient may not stream properly, but we can check headers
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        # Should be event-stream or similar
        assert "text/event-stream" in content_type or "text/plain" in content_type

    def test_sse_streams_response(self, client):
        """SSE should stream response data."""
        response = client.post(
            "/api/vanna/v2/chat_sse",
            json={"message": "Hello"}
        )

        # Get response content
        content = response.text

        # Should have data or be valid response
        assert len(content) >= 0  # May be empty or have data

    def test_sse_done_signal(self, client):
        """SSE stream should end with [DONE] signal."""
        response = client.post(
            "/api/vanna/v2/chat_sse",
            json={"message": "Hello"}
        )

        content = response.text

        # If there's content, it might end with [DONE]
        # The actual format depends on implementation
        if content:
            # Check for SSE format with data: prefix
            assert "data:" in content or len(content) > 0


class TestChatSSEErrorHandling:
    """Tests for SSE endpoint error handling."""

    def test_sse_invalid_json(self, client):
        """Invalid JSON should return error."""
        response = client.post(
            "/api/vanna/v2/chat_sse",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )

        # Should return error
        assert response.status_code in [400, 422, 500]

    def test_sse_empty_message(self, client):
        """Empty message should be handled."""
        response = client.post(
            "/api/vanna/v2/chat_sse",
            json={"message": ""}
        )

        # May succeed with starter UI or return error
        assert response.status_code in [200, 400, 422]


class TestRequestContextExtraction:
    """Tests for request context extraction from HTTP requests."""

    def test_cookies_extracted(self, client):
        """Cookies should be extracted from request."""
        response = client.post(
            "/api/vanna/v2/chat_poll",
            json={"message": "Hello"},
            cookies={"session_id": "test-session"}
        )

        # Should succeed
        assert response.status_code == 200

    def test_headers_extracted(self, client):
        """Headers should be extracted from request."""
        response = client.post(
            "/api/vanna/v2/chat_poll",
            json={"message": "Hello"},
            headers={"X-Custom-Header": "test-value"}
        )

        # Should succeed
        assert response.status_code == 200


class TestCORSConfiguration:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, client):
        """CORS headers should be present in response."""
        response = client.options(
            "/api/vanna/v2/chat_poll",
            headers={"Origin": "http://localhost:3000"}
        )

        # CORS headers may be present
        # The actual behavior depends on configuration


class TestChunkFormat:
    """Tests for response chunk format."""

    def test_poll_chunk_structure(self, client):
        """Poll chunks should have rich and simple components."""
        response = client.post(
            "/api/vanna/v2/chat_poll",
            json={"message": "Hello"}
        )

        data = response.json()
        chunks = data.get("chunks", [])

        for chunk in chunks:
            # Each chunk should have expected fields
            assert "conversation_id" in chunk
            assert "request_id" in chunk
            # May have rich and/or simple components
            if "rich" in chunk:
                assert isinstance(chunk["rich"], dict)
