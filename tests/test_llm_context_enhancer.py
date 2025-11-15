"""
Unit tests for LlmContextEnhancer functionality.

These tests validate that the Agent properly calls the LlmContextEnhancer methods
to enhance system prompts and user messages.
"""

import pytest
from typing import List
from vanna.core.enhancer.base import LlmContextEnhancer
from vanna.core.enhancer.default import DefaultLlmContextEnhancer
from vanna.core.user import User
from vanna.core.user.resolver import UserResolver
from vanna.core.user.request_context import RequestContext
from vanna.core.llm.models import LlmMessage
from vanna.core.llm.base import LlmService
from vanna.capabilities.agent_memory import (
    AgentMemory,
    TextMemory,
    TextMemorySearchResult,
)
from vanna.core.tool import ToolContext


class MockAgentMemory(AgentMemory):
    """Mock AgentMemory for testing."""

    def __init__(self):
        self.text_memories: List[TextMemory] = []

    async def save_tool_usage(
        self, question, tool_name, args, context, success=True, metadata=None
    ):
        pass

    async def save_text_memory(self, content, context):
        memory = TextMemory(
            memory_id=f"mem-{len(self.text_memories)}", content=content, timestamp=None
        )
        self.text_memories.append(memory)
        return memory

    async def search_similar_usage(
        self,
        question,
        context,
        *,
        limit=10,
        similarity_threshold=0.7,
        tool_name_filter=None,
    ):
        return []

    async def search_text_memories(
        self, query, context, *, limit=10, similarity_threshold=0.7
    ):
        """Return mock search results based on stored memories."""
        results = []
        for idx, memory in enumerate(self.text_memories[:limit]):
            results.append(
                TextMemorySearchResult(
                    memory=memory, similarity_score=0.9 - (idx * 0.1), rank=idx + 1
                )
            )
        return results

    async def get_recent_memories(self, context, limit=10):
        return []

    async def get_recent_text_memories(self, context, limit=10):
        return self.text_memories[:limit]

    async def delete_by_id(self, context, memory_id):
        return False

    async def delete_text_memory(self, context, memory_id):
        return False

    async def clear_memories(self, context, tool_name=None, before_date=None):
        return 0


class MockLlmService(LlmService):
    """Mock LLM service that records calls."""

    def __init__(self):
        self.requests = []  # Store full request objects
        self.next_response = "Mock response"

    async def send_request(self, request):
        """Record the call and return a mock response."""
        from vanna.core.llm.models import LlmResponse, LlmResponseMessage

        # Store the full request object
        self.requests.append(request)

        # Return a simple text response
        return LlmResponse(
            message=LlmResponseMessage(role="assistant", content=self.next_response),
            finish_reason="end_turn",
        )

    async def stream_request(self, request):
        """Mock streaming - just yield a single chunk."""
        from vanna.core.llm.models import LlmStreamChunk

        # Store the full request object
        self.requests.append(request)

        yield LlmStreamChunk(delta=self.next_response, finish_reason="end_turn")

    async def validate_tools(self, tools):
        """Mock validation - no errors."""
        return []


class SimpleUserResolver(UserResolver):
    """Simple user resolver for tests."""

    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(
            id="test_user", email="test@example.com", group_memberships=["user"]
        )


class TrackingEnhancer(LlmContextEnhancer):
    """Custom enhancer that tracks when methods are called."""

    def __init__(self):
        self.enhance_system_prompt_calls = []
        self.enhance_user_messages_calls = []

    async def enhance_system_prompt(
        self, system_prompt: str, user_message: str, user: User
    ) -> str:
        """Track call and add a marker to the system prompt."""
        self.enhance_system_prompt_calls.append(
            {
                "system_prompt": system_prompt,
                "user_message": user_message,
                "user_id": user.id,
            }
        )
        return system_prompt + "\n\n[ENHANCED_SYSTEM_PROMPT]"

    async def enhance_user_messages(
        self, messages: List[LlmMessage], user: User
    ) -> List[LlmMessage]:
        """Track call and add a marker to messages."""
        self.enhance_user_messages_calls.append(
            {"message_count": len(messages), "user_id": user.id}
        )
        # Add a marker to the last user message
        if messages and messages[-1].role == "user":
            enhanced_messages = messages[:-1] + [
                LlmMessage(
                    role="user",
                    content=messages[-1].content + " [ENHANCED_USER_MESSAGE]",
                )
            ]
            return enhanced_messages
        return messages


@pytest.mark.asyncio
async def test_custom_enhancer_system_prompt_is_called():
    """Test that a custom LlmContextEnhancer.enhance_system_prompt is called by the Agent."""
    from vanna import Agent, AgentConfig
    from vanna.core.registry import ToolRegistry

    # Create mock components
    llm = MockLlmService()
    tools = ToolRegistry()
    enhancer = TrackingEnhancer()
    agent_memory = MockAgentMemory()

    # Create agent with the tracking enhancer
    agent = Agent(
        llm_service=llm,
        tool_registry=tools,
        user_resolver=SimpleUserResolver(),
        agent_memory=agent_memory,
        llm_context_enhancer=enhancer,
        config=AgentConfig(),
    )

    # Send a message
    request_context = RequestContext(cookies={}, headers={})
    components = []
    async for component in agent.send_message(request_context, "Hello, world!"):
        components.append(component)

    # Verify enhance_system_prompt was called
    assert len(enhancer.enhance_system_prompt_calls) == 1, (
        "enhance_system_prompt should be called exactly once"
    )
    call = enhancer.enhance_system_prompt_calls[0]
    assert call["user_message"] == "Hello, world!", (
        "Should pass the user message to enhancer"
    )
    assert call["user_id"] == "test_user", "Should pass the correct user"
    assert "system_prompt" in call, "Should pass the system prompt"

    # Verify the enhanced system prompt was sent to the LLM
    assert len(llm.requests) >= 1, "LLM should be called at least once"
    first_request = llm.requests[0]
    assert first_request.system_prompt is not None, "Should have a system prompt"
    assert "[ENHANCED_SYSTEM_PROMPT]" in first_request.system_prompt, (
        f"System prompt should contain enhancement marker. Got: {first_request.system_prompt}"
    )


@pytest.mark.asyncio
async def test_custom_enhancer_user_messages_is_called():
    """Test that a custom LlmContextEnhancer.enhance_user_messages is called by the Agent."""
    from vanna import Agent, AgentConfig
    from vanna.core.registry import ToolRegistry

    # Create mock components
    llm = MockLlmService()
    tools = ToolRegistry()
    enhancer = TrackingEnhancer()
    agent_memory = MockAgentMemory()

    # Create agent with the tracking enhancer
    agent = Agent(
        llm_service=llm,
        tool_registry=tools,
        user_resolver=SimpleUserResolver(),
        agent_memory=agent_memory,
        llm_context_enhancer=enhancer,
        config=AgentConfig(),
    )

    # Send a message
    request_context = RequestContext(cookies={}, headers={})
    components = []
    async for component in agent.send_message(request_context, "Test message"):
        components.append(component)

    # Verify enhance_user_messages was called
    assert len(enhancer.enhance_user_messages_calls) >= 1
    call = enhancer.enhance_user_messages_calls[0]
    assert call["user_id"] == "test_user"
    assert call["message_count"] > 0

    # Verify the enhanced user message was sent to the LLM
    assert len(llm.requests) >= 1
    first_request = llm.requests[0]
    user_messages = [m for m in first_request.messages if m.role == "user"]
    assert len(user_messages) >= 1, "Should have at least one user message"
    assert "[ENHANCED_USER_MESSAGE]" in user_messages[0].content, (
        f"User message should be enhanced. Got: {user_messages[0].content}"
    )


@pytest.mark.asyncio
async def test_default_enhancer_with_agent_memory():
    """Test that DefaultLlmContextEnhancer properly enhances system prompt with memories."""
    from vanna import Agent, AgentConfig
    from vanna.core.registry import ToolRegistry

    # Create mock components
    llm = MockLlmService()
    tools = ToolRegistry()
    agent_memory = MockAgentMemory()

    # Add some test memories
    user = User(id="test_user", email="test@example.com", group_memberships=["user"])
    context = ToolContext(
        user=user, conversation_id="test", request_id="test", agent_memory=agent_memory
    )

    await agent_memory.save_text_memory(
        "The database has a users table with columns: id, name, email", context
    )
    await agent_memory.save_text_memory(
        "The products table contains: product_id, name, price, category", context
    )

    # Create default enhancer with agent memory
    enhancer = DefaultLlmContextEnhancer(agent_memory=agent_memory)

    # Create agent
    agent = Agent(
        llm_service=llm,
        tool_registry=tools,
        user_resolver=SimpleUserResolver(),
        agent_memory=agent_memory,
        llm_context_enhancer=enhancer,
        config=AgentConfig(),
    )

    # Send a message that should trigger memory retrieval
    request_context = RequestContext(cookies={}, headers={})
    components = []
    async for component in agent.send_message(
        request_context, "Show me the database schema"
    ):
        components.append(component)

    # Verify that the DefaultLlmContextEnhancer added memory context to the system prompt
    assert len(llm.requests) >= 1, "LLM should be called"
    first_request = llm.requests[0]

    # The DefaultLlmContextEnhancer should add "Relevant Context from Memory" to system prompt
    assert first_request.system_prompt is not None, "Should have a system prompt"
    assert "Relevant Context from Memory" in first_request.system_prompt, (
        f"System prompt should include memory context. Got: {first_request.system_prompt}"
    )

    # Should contain one or both of the memories we added
    assert (
        "users table" in first_request.system_prompt
        or "products table" in first_request.system_prompt
    ), (
        f"System prompt should contain our test memories. Got: {first_request.system_prompt}"
    )


@pytest.mark.asyncio
async def test_default_enhancer_without_agent_memory():
    """Test that DefaultLlmContextEnhancer works without agent memory (no enhancement)."""
    from vanna import Agent, AgentConfig
    from vanna.core.registry import ToolRegistry

    # Create mock components
    llm = MockLlmService()
    tools = ToolRegistry()

    # Create default enhancer without agent memory
    enhancer = DefaultLlmContextEnhancer(agent_memory=None)
    agent_memory = MockAgentMemory()

    # Create agent
    agent = Agent(
        llm_service=llm,
        tool_registry=tools,
        user_resolver=SimpleUserResolver(),
        agent_memory=agent_memory,
        llm_context_enhancer=enhancer,
        config=AgentConfig(),
    )

    # Send a message
    request_context = RequestContext(cookies={}, headers={})
    components = []
    async for component in agent.send_message(request_context, "Hello"):
        components.append(component)

    # Verify the system prompt does NOT include memory context (since enhancer has no agent_memory)
    assert len(llm.requests) >= 1, "LLM should be called"
    first_request = llm.requests[0]

    # The system prompt should exist but NOT contain memory context
    if first_request.system_prompt:
        assert "Relevant Context from Memory" not in first_request.system_prompt, (
            "Should not add memory context when enhancer has no agent_memory"
        )


@pytest.mark.asyncio
async def test_no_enhancer_means_no_enhancement():
    """Test that when no enhancer is provided, no enhancement occurs."""
    from vanna import Agent, AgentConfig
    from vanna.core.registry import ToolRegistry

    # Create mock components
    llm = MockLlmService()
    tools = ToolRegistry()
    agent_memory = MockAgentMemory()

    # Create agent WITHOUT an enhancer (should use default no-op behavior)
    agent = Agent(
        llm_service=llm,
        tool_registry=tools,
        user_resolver=SimpleUserResolver(),
        agent_memory=agent_memory,
        config=AgentConfig(),
    )

    # Send a message
    request_context = RequestContext(cookies={}, headers={})
    components = []
    async for component in agent.send_message(request_context, "Hello"):
        components.append(component)

    # Verify basic system prompt exists but has no enhancements
    assert len(llm.requests) >= 1, "LLM should be called"
    first_request = llm.requests[0]

    # Should be the basic system prompt with no enhancements
    if first_request.system_prompt:
        assert "Relevant Context from Memory" not in first_request.system_prompt, (
            "Should not add memory context when no enhancer is provided"
        )
