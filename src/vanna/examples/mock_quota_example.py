"""
Mock quota-based agent example using Mock LLM service.

This example demonstrates how to create a custom agent runner that
enforces user-based message quotas. It shows:
- Custom agent runner subclass
- Quota management and enforcement
- Error handling for quota exceeded cases
- Multiple users with different quotas

Run:
  PYTHONPATH=. python vanna/examples/mock_quota_example.py
"""

import asyncio

from vanna import (
    AgentConfig,
    MemoryConversationStore,
    MockLlmService,
    User,
)
from vanna.core.registry import ToolRegistry
from vanna.tools import ListFilesTool
from vanna.examples.quota_agent import QuotaAgentRunner, QuotaExceededError


async def demonstrate_quota_system() -> None:
    """Demonstrate the quota-based agent system."""
    print("🚀 Starting Mock Quota-based Agent Example\n")

    # Create a mock LLM service
    llm_service = MockLlmService(
        response_content="Hello! I'm here to help you with your questions."
    )

    # Create tool registry with list_files tool
    tool_registry = ToolRegistry()
    list_files_tool = ListFilesTool()
    tool_registry.register(list_files_tool)

    # Create conversation store
    conversation_store = MemoryConversationStore()

    # Create the quota-based agent
    agent = QuotaAgentRunner(
        llm_service=llm_service,
        tool_registry=tool_registry,
        conversation_store=conversation_store,
        config=AgentConfig(
            stream_responses=False,
            include_thinking_indicators=False,
        ),
    )

    # Create users with different quota settings
    regular_user = User(
        id="user1", username="alice", email="alice@example.com", permissions=[]
    )

    premium_user = User(
        id="user2", username="bob", email="bob@example.com", permissions=["premium"]
    )

    # Set custom quotas
    agent.set_user_quota(regular_user.id, 3)  # Alice gets 3 messages
    agent.set_user_quota(premium_user.id, 5)  # Bob gets 5 messages (premium)

    print("📋 User Quotas:")
    print(f"  • {regular_user.username}: {agent.get_user_quota(regular_user.id)} messages")
    print(f"  • {premium_user.username}: {agent.get_user_quota(premium_user.id)} messages")
    print()

    # Test regular user within quota
    print("💬 Testing regular user (Alice) within quota:")
    for i in range(1, 4):  # Send 3 messages (within quota)
        print(f"  Message {i}/3:")
        async for component in agent.send_message(
            user=regular_user,
            message=f"Hello, this is message {i}",
            conversation_id="alice-conv"
        ):
            if hasattr(component, "content") and component.content:
                print(f"    Agent: {component.content}")
        print()

    # Test regular user exceeding quota
    print("⚠️  Testing regular user (Alice) exceeding quota:")
    async for component in agent.send_message(
            user=regular_user,
            message="This message should be blocked",
            conversation_id="alice-conv"
        ):
        if hasattr(component, "content") and component.content:
            print(f"    Agent: {component.content}")
    print()

    # Test premium user with higher quota
    print("⭐ Testing premium user (Bob) with higher quota:")
    for i in range(1, 4):  # Send 3 messages
        print(f"  Message {i}/5:")
        async for component in agent.send_message(
            user=premium_user,
            message=f"Premium user message {i}",
            conversation_id="bob-conv"
        ):
            if hasattr(component, "content") and component.content:
                print(f"    Agent: {component.content}")
    print()

    # Demonstrate quota reset
    print("🔄 Resetting Alice's usage:")
    agent.reset_user_usage(regular_user.id)
    print(f"  Alice's remaining messages: {agent.get_user_remaining(regular_user.id)}")
    print()

    print("✅ After reset, Alice can send messages again:")
    async for component in agent.send_message(
            user=regular_user,
            message="This should work after reset",
            conversation_id="alice-conv2"
        ):
        if hasattr(component, "content") and component.content:
            print(f"    Agent: {component.content}")

    print("\n📊 Final Usage Summary:")
    print(f"  • Alice: {agent.get_user_usage(regular_user.id)}/{agent.get_user_quota(regular_user.id)} used")
    print(f"  • Bob: {agent.get_user_usage(premium_user.id)}/{agent.get_user_quota(premium_user.id)} used")


async def main() -> None:
    """Run the mock quota example."""
    await demonstrate_quota_system()


if __name__ == "__main__":
    asyncio.run(main())