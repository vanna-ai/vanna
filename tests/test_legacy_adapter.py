"""
Test for LegacyVannaAdapter retrofit functionality.

This test validates that a legacy VannaBase instance can be wrapped
with LegacyVannaAdapter and used with the new Agents framework.
"""

import os
import pytest
from vanna.core.user import User
from vanna.core.user.resolver import UserResolver
from vanna.core.user.request_context import RequestContext


class SimpleUserResolver(UserResolver):
    """Simple user resolver for tests - returns test user or admin."""

    async def resolve_user(self, request_context: RequestContext) -> User:
        user_email = request_context.cookies.get("vanna_email", "test@example.com")

        if user_email == "admin@example.com":
            return User(id="admin_user", email=user_email, group_memberships=["admin"])

        return User(id=user_email, email=user_email, group_memberships=["user"])


@pytest.mark.legacy
@pytest.mark.asyncio
async def test_legacy_adapter_with_anthropic():
    """Test LegacyVannaAdapter wrapping a legacy VannaBase instance with Anthropic LLM."""
    from vanna import Agent, AgentConfig
    from vanna.legacy.adapter import LegacyVannaAdapter
    from vanna.legacy.mock import MockLLM
    from vanna.legacy.chromadb import ChromaDB_VectorStore
    from vanna.integrations.anthropic import AnthropicLlmService

    # Create a legacy VannaBase instance (using multiple inheritance like v0.x)
    class MyVanna(ChromaDB_VectorStore, MockLLM):
        def __init__(self, config=None):
            ChromaDB_VectorStore.__init__(self, config=config)
            MockLLM.__init__(self, config=config)

    vn = MyVanna()

    # Connect to the Chinook database using legacy method
    vn.connect_to_sqlite("https://vanna.ai/Chinook.sqlite")

    # Add some training data
    vn.add_question_sql(
        question="Who is the top artist by sales?",
        sql="SELECT a.Name, SUM(il.UnitPrice * il.Quantity) as total FROM Artist a JOIN Album al ON a.ArtistId = al.ArtistId JOIN Track t ON al.AlbumId = t.AlbumId JOIN InvoiceLine il ON t.TrackId = il.TrackId GROUP BY a.ArtistId ORDER BY total DESC LIMIT 1",
    )

    # Wrap legacy VannaBase with LegacyVannaAdapter
    legacy_adapter = LegacyVannaAdapter(vn)

    # Create agent with new LLM service
    api_key = os.getenv("ANTHROPIC_API_KEY")
    llm = AnthropicLlmService(api_key=api_key, model="claude-haiku-4-5")

    agent = Agent(
        llm_service=llm,
        tool_registry=legacy_adapter,  # LegacyVannaAdapter is a ToolRegistry
        agent_memory=legacy_adapter,  # LegacyVannaAdapter implements AgentMemory
        user_resolver=SimpleUserResolver(),
        config=AgentConfig(),
    )

    # Test that the agent can answer a question
    request_context = RequestContext(cookies={}, headers={})

    components = []
    async for component in agent.send_message(
        request_context, "Who is the top artist by sales?"
    ):
        components.append(component)

    # Validate we got components
    assert len(components) > 0, "Should receive at least one component"

    # Look for a successful response (either table or text mentioning an artist)
    has_response = False
    for component in components:
        if hasattr(component, "rich_component") and component.rich_component:
            has_response = True
            break
        if hasattr(component, "simple_component") and component.simple_component:
            if (
                hasattr(component.simple_component, "text")
                and component.simple_component.text
            ):
                has_response = True
                break

    assert has_response, "Should receive at least one response component"


@pytest.mark.legacy
@pytest.mark.asyncio
async def test_legacy_adapter_memory_operations():
    """Test that LegacyVannaAdapter properly implements AgentMemory interface."""
    from vanna.legacy.adapter import LegacyVannaAdapter
    from vanna.legacy.mock import MockLLM
    from vanna.legacy.chromadb import ChromaDB_VectorStore
    from vanna.core.tool import ToolContext
    from vanna.core.user import User

    # Create a legacy VannaBase instance
    class MyVanna(ChromaDB_VectorStore, MockLLM):
        def __init__(self, config=None):
            ChromaDB_VectorStore.__init__(self, config=config)
            MockLLM.__init__(self, config=config)

    vn = MyVanna()
    adapter = LegacyVannaAdapter(vn)

    # Create a properly constructed tool context
    user = User(id="test_user", email="test@example.com", group_memberships=["user"])
    context = ToolContext(
        user=user,
        conversation_id="test-conversation",
        request_id="test-request",
        agent_memory=adapter,  # Use the adapter itself as the agent_memory
    )

    # Test save_tool_usage
    await adapter.save_tool_usage(
        question="What are the total sales?",
        tool_name="run_sql",
        args={"sql": "SELECT SUM(Total) FROM Invoice"},
        context=context,
        success=True,
    )

    # Test search_similar_usage
    results = await adapter.search_similar_usage(
        question="What are sales?", context=context, limit=5
    )

    # Should find the saved usage
    assert len(results) > 0, "Should find similar tool usage"
    assert results[0].memory.question == "What are the total sales?"
    assert results[0].memory.args["sql"] == "SELECT SUM(Total) FROM Invoice"

    # Test save_text_memory
    text_memory = await adapter.save_text_memory(
        content="The Invoice table contains all sales transactions.", context=context
    )
    assert text_memory.content == "The Invoice table contains all sales transactions."

    # Test search_text_memories
    text_results = await adapter.search_text_memories(
        query="sales", context=context, limit=5
    )
    assert len(text_results) > 0, "Should find similar text memories"

    # Test get_recent_memories (uses blank string retrieval)
    recent = await adapter.get_recent_memories(context=context, limit=5)
    assert isinstance(recent, list), "Should return a list of memories"

    # Test get_recent_text_memories
    recent_text = await adapter.get_recent_text_memories(context=context, limit=5)
    assert isinstance(recent_text, list), "Should return a list of text memories"
