"""
Mock quickstart example for the Vanna Agents framework.

This example shows how to create a basic agent with a mock LLM service
and have a simple conversation.

Usage:
  Template: Copy this file and modify for your needs
  Interactive: python -m vanna.examples.mock_quickstart
  REPL: from vanna.examples.mock_quickstart import create_demo_agent
  Server: python -m vanna.servers --example mock_quickstart
"""

import asyncio

from vanna import (
    AgentConfig,
    Agent,
    ToolRegistry,
    MemoryConversationStore,
    MockLlmService,
    User,
)
from vanna.core.user import UserResolver, RequestContext
from vanna.integrations.local.agent_memory.in_memory import DemoAgentMemory


# Configure user authentication
class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        user_email = request_context.get_cookie("vanna_email") or "guest@example.com"
        group = "admin" if user_email == "admin@example.com" else "user"
        return User(id=user_email, email=user_email, group_memberships=[group])


def create_demo_agent() -> Agent:
    """Create a demo agent for REPL and server usage.

    Returns:
        Configured Agent instance
    """
    llm_service = MockLlmService(
        response_content="Hello! I'm a helpful AI assistant created using the Vanna Agents framework."
    )
    # Minimal tool registry (no tools registered) for examples
    tool_registry = ToolRegistry()

    # In-memory demo agent memory (zero-dependency)
    agent_memory = DemoAgentMemory()

    # Use shared SimpleUserResolver (small, reusable resolver for examples)
    user_resolver = SimpleUserResolver()

    return Agent(
        llm_service=llm_service,
        tool_registry=tool_registry,
        user_resolver=user_resolver,
        agent_memory=agent_memory,
        config=AgentConfig(
            stream_responses=True,  # Enable streaming for better server experience
            include_thinking_indicators=True,
        ),
    )


async def main() -> None:
    """Run the mock quickstart example."""

    # Create agent using factory function
    agent = create_demo_agent()

    # Create a test user
    user = User(
        id="user123", username="testuser", email="test@example.com", permissions=[]
    )

    # Build a RequestContext so the Agent's UserResolver can resolve the user
    request_context = RequestContext(metadata={"user": user})

    # Start a conversation
    conversation_id = "conversation123"
    user_message = "Hello! Can you introduce yourself?"

    print(f"User: {user_message}")
    print("Agent: ", end="")

    # Send message and collect response
    async for component in agent.send_message(
        message=user_message,
        conversation_id=conversation_id,
        request_context=request_context,
    ):
        rich = getattr(component, "rich_component", None)
        simple = getattr(component, "simple_component", None)

        # print rich_component.content（RichTextComponent）
        if rich is not None and hasattr(rich, "content") and rich.content:
            print(rich.content, end="")
        # print simple_component.text（SimpleTextComponent）
        elif simple is not None and hasattr(simple, "text") and simple.text:
            print(simple.text, end="")

    print()


def run_interactive() -> None:
    """Entry point for interactive usage."""
    print("Starting Vanna Agents mock quickstart demo...")
    asyncio.run(main())


if __name__ == "__main__":
    run_interactive()
