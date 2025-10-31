"""
Simple end-to-end tests for Vanna agents.

Tests use agent.send_message and validate the response components.
"""

import os
import pytest
from vanna.core.user import User
from vanna.core.user.resolver import UserResolver
from vanna.core.user.request_context import RequestContext


class SimpleUserResolver(UserResolver):
    """Simple user resolver for tests - always returns the same test user."""

    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(id="test_user", email="test@example.com", group_memberships=['user'])


def create_agent(llm_service, sql_runner):
    """Helper to create a configured agent."""
    from vanna import Agent, AgentConfig
    from vanna.core.registry import ToolRegistry
    from vanna.tools import RunSqlTool
    from vanna.integrations.local.file_system import LocalFileSystem
    from vanna.integrations.local.agent_memory import DemoAgentMemory
    from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool

    tools = ToolRegistry()

    # Add SQL tool
    db_tool = RunSqlTool(
        sql_runner=sql_runner,
        file_system=LocalFileSystem()
    )
    tools.register_local_tool(db_tool, access_groups=['user'])

    # Add memory tools
    agent_memory = DemoAgentMemory(max_items=1000)
    save_memory_tool = SaveQuestionToolArgsTool(agent_memory)
    search_memory_tool = SearchSavedCorrectToolUsesTool(agent_memory)

    tools.register_local_tool(save_memory_tool, access_groups=['user'])
    tools.register_local_tool(search_memory_tool, access_groups=['user'])

    return Agent(
        llm_service=llm_service,
        tool_registry=tools,
        user_resolver=SimpleUserResolver(),
        config=AgentConfig()
    )


@pytest.mark.anthropic
@pytest.mark.asyncio
async def test_anthropic_top_artist(chinook_db):
    """Test Anthropic agent finding the top artist by sales."""
    from vanna.integrations.anthropic import AnthropicLlmService

    api_key = os.getenv("ANTHROPIC_API_KEY")
    llm = AnthropicLlmService(api_key=api_key, model="claude-sonnet-4-5")

    agent = create_agent(llm, chinook_db)

    # Create a simple request context
    request_context = RequestContext(cookies={}, headers={})

    # Collect all components from the async generator
    components = []
    async for component in agent.send_message(request_context, "Who is the top artist by sales?"):
        components.append(component)

    # Validate we got components
    assert len(components) > 0, "Should receive at least one component"

    # Print all components for debugging
    print(f"\n\n=== Received {len(components)} components ===")
    for i, component in enumerate(components):
        print(f"\nComponent {i+1}:")
        print(f"  Type: {component.type if hasattr(component, 'type') else 'no type'}")
        if hasattr(component, 'text'):
            print(f"  Text: {component.text[:200]}..." if len(component.text) > 200 else f"  Text: {component.text}")
        if hasattr(component, 'content'):
            print(f"  Content: {str(component.content)[:200]}...")
        print(f"  Full: {component}")

    # Look for "Iron Maiden" in any component
    found_iron_maiden = False
    for component in components:
        # Check rich_component.content
        if hasattr(component, 'rich_component') and hasattr(component.rich_component, 'content'):
            if 'Iron Maiden' in component.rich_component.content:
                found_iron_maiden = True
                break
        # Check simple_component.text
        if hasattr(component, 'simple_component') and hasattr(component.simple_component, 'text'):
            if 'Iron Maiden' in component.simple_component.text:
                found_iron_maiden = True
                break

    assert found_iron_maiden, f"Response should mention 'Iron Maiden' as the top artist. Got {len(components)} components."


@pytest.mark.openai
@pytest.mark.asyncio
async def test_openai_top_artist(chinook_db):
    """Test OpenAI agent finding the top artist by sales."""
    from vanna.integrations.openai import OpenAILlmService

    api_key = os.getenv("OPENAI_API_KEY")
    llm = OpenAILlmService(api_key=api_key, model="gpt-5")

    agent = create_agent(llm, chinook_db)

    # Create a simple request context
    request_context = RequestContext(cookies={}, headers={})

    # Collect all components from the async generator
    components = []
    async for component in agent.send_message(request_context, "Who is the top artist by sales?"):
        components.append(component)

    # Validate we got components
    assert len(components) > 0, "Should receive at least one component"

    # Print all components for debugging
    print(f"\n\n=== Received {len(components)} components ===")
    for i, component in enumerate(components):
        print(f"\nComponent {i+1}:")
        print(f"  Type: {component.type if hasattr(component, 'type') else 'no type'}")
        if hasattr(component, 'text'):
            print(f"  Text: {component.text[:200]}..." if len(component.text) > 200 else f"  Text: {component.text}")
        if hasattr(component, 'content'):
            print(f"  Content: {str(component.content)[:200]}...")
        print(f"  Full: {component}")

    # Look for "Iron Maiden" in any component
    found_iron_maiden = False
    for component in components:
        # Check rich_component.content
        if hasattr(component, 'rich_component') and hasattr(component.rich_component, 'content'):
            if 'Iron Maiden' in component.rich_component.content:
                found_iron_maiden = True
                break
        # Check simple_component.text
        if hasattr(component, 'simple_component') and hasattr(component.simple_component, 'text'):
            if 'Iron Maiden' in component.simple_component.text:
                found_iron_maiden = True
                break

    assert found_iron_maiden, f"Response should mention 'Iron Maiden' as the top artist. Got {len(components)} components."
