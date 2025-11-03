"""
Direct Ollama integration tests to diagnose and verify the integration.

These tests check each aspect of the Ollama integration separately.
"""

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
        group_memberships=['user']
    )


@pytest.mark.ollama
@pytest.mark.asyncio
async def test_ollama_import():
    """Test that Ollama integration can be imported."""
    try:
        from vanna.integrations.ollama import OllamaLlmService
        print("✓ OllamaLlmService imported successfully")
        assert OllamaLlmService is not None
    except ImportError as e:
        pytest.fail(f"Failed to import OllamaLlmService: {e}")


@pytest.mark.ollama
@pytest.mark.asyncio
async def test_ollama_initialization():
    """Test that Ollama service can be initialized."""
    from vanna.integrations.ollama import OllamaLlmService
    
    try:
        llm = OllamaLlmService(
            model="llama3.2",
            host="http://localhost:11434",
            temperature=0.0
        )
        
        print(f"✓ OllamaLlmService initialized")
        print(f"  Model: {llm.model}")
        print(f"  Host: {llm.host}")
        print(f"  Temperature: {llm.temperature}")
        print(f"  Context window: {llm.num_ctx}")
        
        assert llm.model == "llama3.2"
        assert llm.host == "http://localhost:11434"
        
    except Exception as e:
        pytest.fail(f"Failed to initialize OllamaLlmService: {e}")


@pytest.mark.ollama
@pytest.mark.asyncio
async def test_ollama_basic_request(test_user):
    """Test a basic request without tools."""
    from vanna.integrations.ollama import OllamaLlmService
    
    llm = OllamaLlmService(
        model="llama3.2",
        temperature=0.0
    )
    
    request = LlmRequest(
        user=test_user,
        messages=[
            LlmMessage(role="user", content="What is 2+2? Answer with just the number.")
        ]
    )
    
    print(f"\n=== Basic Request Test ===")
    print(f"Sending request to Ollama...")
    
    try:
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
        
    except Exception as e:
        print(f"❌ Error during request: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.ollama
@pytest.mark.asyncio
async def test_ollama_pydantic_response(test_user):
    """Test that the response is a valid Pydantic model."""
    from vanna.integrations.ollama import OllamaLlmService
    from vanna.core.llm import LlmResponse
    
    llm = OllamaLlmService(model="llama3.2", temperature=0.0)
    
    request = LlmRequest(
        user=test_user,
        messages=[
            LlmMessage(role="user", content="Say 'hello'")
        ]
    )
    
    print(f"\n=== Pydantic Validation Test ===")
    
    try:
        response = await llm.send_request(request)
        
        # Verify it's a Pydantic model
        assert isinstance(response, LlmResponse)
        print(f"✓ Response is LlmResponse instance")
        
        # Test model_dump
        dumped = response.model_dump()
        print(f"✓ model_dump() works: {dumped}")
        
        # Test model_dump_json
        json_str = response.model_dump_json()
        print(f"✓ model_dump_json() works: {json_str[:100]}...")
        
        # Test reconstruction
        reconstructed = LlmResponse(**dumped)
        print(f"✓ Reconstruction works")
        assert reconstructed.content == response.content
        
    except Exception as e:
        print(f"❌ Pydantic error: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.ollama
@pytest.mark.asyncio
async def test_ollama_streaming(test_user):
    """Test streaming responses."""
    from vanna.integrations.ollama import OllamaLlmService
    from vanna.core.llm import LlmStreamChunk
    
    llm = OllamaLlmService(model="llama3.2", temperature=0.0)
    
    request = LlmRequest(
        user=test_user,
        messages=[
            LlmMessage(role="user", content="Count from 1 to 3.")
        ]
    )
    
    print(f"\n=== Streaming Test ===")
    
    try:
        chunks = []
        content_parts = []
        
        async for chunk in llm.stream_request(request):
            chunks.append(chunk)
            
            # Verify chunk is correct type
            assert isinstance(chunk, LlmStreamChunk)
            
            if chunk.content:
                content_parts.append(chunk.content)
                print(f"  Chunk {len(chunks)}: {chunk.content!r}")
        
        full_content = "".join(content_parts)
        
        print(f"✓ Streaming completed")
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Full content: {full_content}")
        print(f"  Final finish_reason: {chunks[-1].finish_reason}")
        
        assert len(chunks) > 0
        assert chunks[-1].finish_reason is not None
        
    except Exception as e:
        print(f"❌ Streaming error: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.ollama
@pytest.mark.asyncio
async def test_ollama_tool_calling_attempt(test_user):
    """Test tool calling with Ollama (may not work with all models)."""
    from vanna.integrations.ollama import OllamaLlmService
    
    llm = OllamaLlmService(
        model="llama3.2",
        temperature=0.0
    )
    
    tools = [
        ToolSchema(
            name="get_weather",
            description="Get the current weather for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["location"]
            }
        )
    ]
    
    request = LlmRequest(
        user=test_user,
        system_prompt="You are a helpful assistant. When asked about weather, use the get_weather tool.",
        messages=[
            LlmMessage(role="user", content="What's the weather in San Francisco?")
        ],
        tools=tools
    )
    
    print(f"\n=== Tool Calling Test ===")
    print(f"Model: {llm.model}")
    print(f"Tools provided: {[t.name for t in tools]}")
    
    try:
        response = await llm.send_request(request)
        
        print(f"\nResponse:")
        print(f"  Content: {response.content}")
        print(f"  Tool calls: {response.tool_calls}")
        print(f"  Finish reason: {response.finish_reason}")
        
        if response.tool_calls:
            print(f"\n✓ Tool calling works!")
            print(f"  Number of tool calls: {len(response.tool_calls)}")
            for i, tc in enumerate(response.tool_calls):
                print(f"  Tool call {i+1}:")
                print(f"    ID: {tc.id}")
                print(f"    Name: {tc.name}")
                print(f"    Arguments: {tc.arguments}")
                print(f"    Arguments type: {type(tc.arguments)}")
        else:
            print(f"\n⚠️  Model returned text instead of tool calls")
            print(f"  This is expected for models without tool calling support")
            print(f"  Try using llama3.1:8b or mistral for better tool calling")
        
        # Test passes either way - we're just diagnosing
        assert response is not None
        
    except Exception as e:
        print(f"❌ Tool calling error: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.ollama
@pytest.mark.asyncio
async def test_ollama_payload_building(test_user):
    """Test that the payload is built correctly."""
    from vanna.integrations.ollama import OllamaLlmService
    
    llm = OllamaLlmService(
        model="llama3.2",
        temperature=0.5,
        num_ctx=4096
    )
    
    tools = [
        ToolSchema(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}}
        )
    ]
    
    request = LlmRequest(
        user=test_user,
        system_prompt="You are a test assistant.",
        messages=[
            LlmMessage(role="user", content="Hello")
        ],
        tools=tools
    )
    
    print(f"\n=== Payload Building Test ===")
    
    try:
        # Access the internal method to inspect payload
        payload = llm._build_payload(request)
        
        print(f"Built payload:")
        print(f"  Model: {payload.get('model')}")
        print(f"  Messages count: {len(payload.get('messages', []))}")
        print(f"  First message: {payload.get('messages', [{}])[0]}")
        print(f"  Options: {payload.get('options')}")
        print(f"  Tools: {payload.get('tools')}")
        
        # Verify payload structure
        assert payload['model'] == "llama3.2"
        assert len(payload['messages']) == 2  # system + user
        assert payload['messages'][0]['role'] == 'system'
        assert payload['messages'][1]['role'] == 'user'
        assert payload['options']['temperature'] == 0.5
        assert payload['options']['num_ctx'] == 4096
        assert 'tools' in payload
        assert len(payload['tools']) == 1
        
        print(f"✓ Payload structure is correct")
        
    except Exception as e:
        print(f"❌ Payload building error: {e}")
        import traceback
        traceback.print_exc()
        raise
