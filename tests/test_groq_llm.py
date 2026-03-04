"""
Tests for Groq LLM service integration.
"""

import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from vanna.core.llm import LlmRequest, LlmMessage
from vanna.integrations.groq import GroqLlmService

@pytest.fixture
def groq_service():
    """Setup a Groq LLM service with a mock API key."""
    # Ensure OPENAI_BASE_URL isn't interfering
    with patch.dict(os.environ, {"GROQ_API_KEY": "test-key-123"}, clear=True):
        return GroqLlmService()

@pytest.mark.asyncio
async def test_groq_service_init_defaults(groq_service):
    """Test that GroqLlmService initializes with correct defaults."""
    assert groq_service.model == "llama3-8b-8192"
    # Wait to inspect the underlying OpenAI client's base_url
    assert str(groq_service._client.base_url) == "https://api.groq.com/openai/v1/"
    assert groq_service._client.api_key == "test-key-123"

@pytest.mark.asyncio
async def test_groq_service_init_custom():
    """Test that GroqLlmService respects custom initialization parameters."""
    service = GroqLlmService(
        model="mixtral-8x7b-32768",
        api_key="custom-key",
        base_url="https://custom.groq.proxy/v1"
    )
    assert service.model == "mixtral-8x7b-32768"
    assert str(service._client.base_url) == "https://custom.groq.proxy/v1/"
    assert service._client.api_key == "custom-key"

@pytest.mark.asyncio
@patch("openai.resources.chat.completions.Completions.create")
async def test_groq_send_request(mock_create, groq_service):
    """Test sending a basic request."""
    # Build a mock response
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a response from Groq."
    mock_choice.finish_reason = "stop"
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 30
    
    mock_create.return_value = mock_response

    request = LlmRequest(
        messages=[
            LlmMessage(role="user", content="Hello Groq")
        ]
    )

    response = await groq_service.send_request(request)

    assert response.content == "This is a response from Groq."
    assert response.finish_reason == "stop"
    assert response.usage["total_tokens"] == 30

    # Ensure the correct url/model was requested
    mock_create.assert_called_once()
    kwargs = mock_create.call_args.kwargs
    assert kwargs["model"] == "llama3-8b-8192"
    assert kwargs["messages"][0]["content"] == "Hello Groq"
    assert kwargs["stream"] is False
