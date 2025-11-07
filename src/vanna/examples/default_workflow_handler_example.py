"""
Example demonstrating the DefaultWorkflowHandler with setup health checking.

This example shows how the DefaultWorkflowHandler provides intelligent starter UI
that adapts based on available tools and helps users understand their setup status.

Run:
  PYTHONPATH=. python vanna/examples/default_workflow_handler_example.py
"""

import asyncio

from vanna import (
    AgentConfig,
    Agent,
    MemoryConversationStore,
    MockLlmService,
    User,
    DefaultWorkflowHandler,
)
from vanna.core.registry import ToolRegistry
from vanna.core.user.resolver import SimpleUserResolver
from vanna.tools import ListFilesTool


async def demonstrate_setup_scenarios():
    """Demonstrate different setup scenarios with DefaultWorkflowHandler."""
    print("🚀 Starting DefaultWorkflowHandler Setup Health Check Demo\n")

    # Create basic components
    llm_service = MockLlmService(response_content="I'm ready to help!")
    conversation_store = MemoryConversationStore()
    user_resolver = SimpleUserResolver()

    # Create test user
    user = User(
        id="user1",
        username="alice",
        email="alice@example.com",
        group_memberships=["user"],
    )

    print("=" * 60)
    print("SCENARIO 1: Empty Setup (No Tools)")
    print("=" * 60)

    # Empty tool registry
    empty_registry = ToolRegistry()

    agent_empty = Agent(
        llm_service=llm_service,
        tool_registry=empty_registry,
        user_resolver=user_resolver,
        conversation_store=conversation_store,
        config=AgentConfig(stream_responses=False),
        workflow_handler=DefaultWorkflowHandler(),
    )

    print("📋 Starter UI for empty setup:")
    async for component in agent_empty.send_message(
        request_context=user_resolver.create_request_context(
            metadata={"starter_ui_request": True}
        ),
        message="",
        conversation_id="empty-setup",
    ):
        if hasattr(component, "simple_component") and component.simple_component:
            print(f"  📄 {component.simple_component.text[:100]}...")
        elif hasattr(component, "rich_component"):
            comp = component.rich_component
            if hasattr(comp, "title"):
                print(f"  📊 {comp.title}: {comp.status} - {comp.description}")
            elif hasattr(comp, "content"):
                print(f"  📝 {comp.content[:100]}...")

    print("\n" + "=" * 60)
    print("SCENARIO 2: Functional Setup (SQL + Basic Tools)")
    print("=" * 60)

    # Tool registry with SQL tool (simulated)
    functional_registry = ToolRegistry()

    # Register a mock SQL tool (we'll simulate by tool name)
    list_tool = ListFilesTool()
    list_tool.name = "run_sql"  # Simulate SQL tool
    functional_registry.register(list_tool)

    agent_functional = Agent(
        llm_service=llm_service,
        tool_registry=functional_registry,
        user_resolver=user_resolver,
        conversation_store=conversation_store,
        config=AgentConfig(stream_responses=False),
        workflow_handler=DefaultWorkflowHandler(),
    )

    print("📋 Starter UI for functional setup:")
    async for component in agent_functional.send_message(
        request_context=user_resolver.create_request_context(
            metadata={"starter_ui_request": True}
        ),
        message="",
        conversation_id="functional-setup",
    ):
        if hasattr(component, "simple_component") and component.simple_component:
            print(f"  📄 {component.simple_component.text[:100]}...")
        elif hasattr(component, "rich_component"):
            comp = component.rich_component
            if hasattr(comp, "title"):
                print(f"  📊 {comp.title}: {comp.status} - {comp.description}")
            elif hasattr(comp, "content"):
                print(f"  📝 {comp.content[:100]}...")

    print("\n" + "=" * 60)
    print("SCENARIO 3: Complete Setup (SQL + Memory + Visualization)")
    print("=" * 60)

    # Complete tool registry
    complete_registry = ToolRegistry()

    # Mock SQL tool
    sql_tool = ListFilesTool()
    sql_tool.name = "run_sql"
    complete_registry.register(sql_tool)

    # Mock memory tools
    search_tool = ListFilesTool()
    search_tool.name = "search_saved_correct_tool_uses"
    complete_registry.register(search_tool)

    save_tool = ListFilesTool()
    save_tool.name = "save_question_tool_args"
    complete_registry.register(save_tool)

    # Mock visualization tool
    viz_tool = ListFilesTool()
    viz_tool.name = "visualize_data"
    complete_registry.register(viz_tool)

    agent_complete = Agent(
        llm_service=llm_service,
        tool_registry=complete_registry,
        user_resolver=user_resolver,
        conversation_store=conversation_store,
        config=AgentConfig(stream_responses=False),
        workflow_handler=DefaultWorkflowHandler(),
    )

    print("📋 Starter UI for complete setup:")
    async for component in agent_complete.send_message(
        request_context=user_resolver.create_request_context(
            metadata={"starter_ui_request": True}
        ),
        message="",
        conversation_id="complete-setup",
    ):
        if hasattr(component, "simple_component") and component.simple_component:
            print(f"  📄 {component.simple_component.text[:100]}...")
        elif hasattr(component, "rich_component"):
            comp = component.rich_component
            if hasattr(comp, "title"):
                print(f"  📊 {comp.title}: {comp.status} - {comp.description}")
            elif hasattr(comp, "content"):
                print(f"  📝 {comp.content[:100]}...")

    print("\n" + "=" * 60)
    print("SCENARIO 4: Testing Commands")
    print("=" * 60)

    print("📋 Testing /help command:")
    async for component in agent_complete.send_message(
        request_context=user_resolver.create_request_context(),
        message="/help",
        conversation_id="help-test",
    ):
        if hasattr(component, "rich_component") and hasattr(
            component.rich_component, "content"
        ):
            print(f"  📝 Help: {component.rich_component.content[:200]}...")

    print("\n📋 Testing /status command:")
    async for component in agent_complete.send_message(
        request_context=user_resolver.create_request_context(),
        message="/status",
        conversation_id="status-test",
    ):
        if hasattr(component, "rich_component"):
            comp = component.rich_component
            if hasattr(comp, "title"):
                print(f"  📊 {comp.title}: {comp.status}")
            elif hasattr(comp, "content"):
                print(f"  📝 Status: {comp.content[:150]}...")

    print("\n✅ Demo complete! The DefaultWorkflowHandler provides:")
    print("  • Smart setup health checking")
    print("  • Contextual starter UI based on available tools")
    print("  • Helpful error messages and setup guidance")
    print("  • Built-in command handling (/help, /status)")
    print("  • Automatic tool analysis and recommendations")


async def main():
    """Run the DefaultWorkflowHandler demonstration."""
    await demonstrate_setup_scenarios()


if __name__ == "__main__":
    asyncio.run(main())
