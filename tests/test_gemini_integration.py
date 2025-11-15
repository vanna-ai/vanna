"""
Google Gemini integration tests.

Basic unit tests for the Gemini LLM service integration.
End-to-end tests are in test_agents.py.

Note: Tests requiring API calls need GOOGLE_API_KEY environment variable.
"""

import os
import pytest
from vanna.core.llm import LlmRequest, LlmMessage
from vanna.core.tool import ToolSchema
from vanna.core.user import User


@pytest.fixture
def test_user():
    """Test user for LLM requests."""
    return User(
        id="test_user",
        username="test",
        email="test@example.com",
        group_memberships=["user"],
    )


@pytest.mark.gemini
@pytest.mark.asyncio
async def test_gemini_import():
    """Test that Gemini integration can be imported."""
    from vanna.integrations.google import GeminiLlmService

    print("✓ GeminiLlmService imported successfully")
    assert GeminiLlmService is not None


@pytest.mark.gemini
@pytest.mark.asyncio
async def test_gemini_initialization_without_key():
    """Test that Gemini service raises error without API key."""
    from vanna.integrations.google import GeminiLlmService

    # Clear both env vars if they exist
    old_google_key = os.environ.pop("GOOGLE_API_KEY", None)
    old_gemini_key = os.environ.pop("GEMINI_API_KEY", None)

    try:
        with pytest.raises(ValueError, match="Google API key is required"):
            llm = GeminiLlmService(model="gemini-2.5-pro")
    finally:
        # Restore the keys if they existed
        if old_google_key:
            os.environ["GOOGLE_API_KEY"] = old_google_key
        if old_gemini_key:
            os.environ["GEMINI_API_KEY"] = old_gemini_key


@pytest.mark.gemini
@pytest.mark.asyncio
async def test_gemini_initialization():
    """Test that Gemini service can be initialized with API key."""
    from vanna.integrations.google import GeminiLlmService

    # This test will be skipped by conftest.py if GOOGLE_API_KEY is not set
    llm = GeminiLlmService(
        model="gemini-2.5-pro",
        temperature=0.7,
    )

    print(f"✓ GeminiLlmService initialized")
    print(f"  Model: {llm.model_name}")
    print(f"  Temperature: {llm.temperature}")

    assert llm.model_name == "gemini-2.5-pro"
    assert llm.temperature == 0.7


@pytest.mark.gemini
@pytest.mark.asyncio
async def test_gemini_basic_request(test_user):
    """Test a basic request without tools."""
    from vanna.integrations.google import GeminiLlmService

    llm = GeminiLlmService(model="gemini-2.5-pro", temperature=0.0)

    request = LlmRequest(
        user=test_user,
        messages=[
            LlmMessage(role="user", content="What is 2+2? Answer with just the number.")
        ],
    )

    print(f"\n=== Basic Request Test ===")
    print(f"Sending request to Gemini...")

    response = await llm.send_request(request)

    print(f"✓ Response received")
    print(f"  Content type: {type(response.content)}")
    print(f"  Content: {response.content}")
    print(f"  Finish reason: {response.finish_reason}")
    print(f"  Tool calls: {response.tool_calls}")
    print(f"  Usage: {response.usage}")

    # Verify response structure
    assert response is not None
    assert response.content is not None
    assert isinstance(response.content, str)
    assert "4" in response.content


@pytest.mark.gemini
@pytest.mark.asyncio
async def test_gemini_streaming_request(test_user):
    """Test streaming request."""
    from vanna.integrations.google import GeminiLlmService

    llm = GeminiLlmService(model="gemini-2.5-pro", temperature=0.0)

    request = LlmRequest(
        user=test_user,
        messages=[
            LlmMessage(role="user", content="Count from 1 to 5, one number per line.")
        ],
        stream=True,
    )

    print(f"\n=== Streaming Request Test ===")
    print(f"Streaming from Gemini...")

    chunks = []
    async for chunk in llm.stream_request(request):
        chunks.append(chunk)
        if chunk.content:
            print(f"  Chunk: {chunk.content}")

    print(f"✓ Streaming completed")
    print(f"  Total chunks: {len(chunks)}")

    # Verify we got chunks
    assert len(chunks) > 0
    # At least one chunk should have content
    assert any(c.content for c in chunks)


@pytest.mark.gemini
@pytest.mark.asyncio
async def test_gemini_validate_tools():
    """Test tool validation (does not require API key for actual calls)."""
    from vanna.integrations.google import GeminiLlmService

    # For validation testing, we need to initialize but won't make API calls
    llm = GeminiLlmService(model="gemini-2.5-pro")

    # Valid tool
    valid_tool = ToolSchema(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object", "properties": {}},
    )

    # Invalid tool (no name)
    invalid_tool = ToolSchema(
        name="",
        description="Invalid tool",
        parameters={"type": "object", "properties": {}},
    )

    # Invalid tool (no description)
    invalid_tool2 = ToolSchema(
        name="test_tool_2",
        description="",
        parameters={"type": "object", "properties": {}},
    )

    errors = await llm.validate_tools([valid_tool])
    assert len(errors) == 0, "Valid tool should have no errors"

    errors = await llm.validate_tools([invalid_tool])
    assert len(errors) > 0, "Tool with empty name should have errors"
    assert any("name" in e.lower() for e in errors)

    errors = await llm.validate_tools([invalid_tool2])
    assert len(errors) > 0, "Tool with empty description should have errors"
    assert any("description" in e.lower() for e in errors)

    print("✓ Tool validation working correctly")
