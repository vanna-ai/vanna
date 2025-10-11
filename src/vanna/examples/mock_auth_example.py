"""
Mock authentication example to verify user resolution is working.

This example demonstrates the new UserResolver architecture where:
1. UserResolver is a required parameter of Agent
2. Agent.send_message() accepts RequestContext (not User directly)
3. The Agent resolves the user internally using the UserResolver

The agent uses an LLM middleware to inject user info into the response,
so we can verify the authentication is working correctly.

Usage:
    python -m vanna.examples.mock_auth_example
"""

from __future__ import annotations

import asyncio

from vanna import AgentConfig, Agent
from vanna.core.registry import ToolRegistry
from vanna.core.llm import LlmRequest, LlmResponse
from vanna.core.middleware import LlmMiddleware
from vanna.integrations.mock import MockLlmService
from vanna.core.user import CookieEmailUserResolver, RequestContext


class UserEchoMiddleware(LlmMiddleware):
    """Middleware that injects user email into LLM responses."""

    async def after_llm_response(
        self, request: LlmRequest, response: LlmResponse
    ) -> LlmResponse:
        """Inject user email into response."""
        # Extract user email from request user_id (which is set to user.id in the agent)
        user_id = request.user_id

        # Create a new response with user info
        new_content = f"Hello! You are authenticated as: {user_id}"

        return LlmResponse(
            content=new_content,
            finish_reason=response.finish_reason,
            usage=response.usage,
        )


def create_demo_agent() -> Agent:
    """Create a demo agent for server usage.

    Returns:
        Configured Agent instance with cookie-based authentication
    """
    # Create a mock LLM
    llm_service = MockLlmService(
        response_content="Mock response"
    )

    # Empty tool registry
    tool_registry = ToolRegistry()

    # Cookie-based user resolver
    user_resolver = CookieEmailUserResolver(cookie_name='vanna_email')

    # User echo middleware
    middleware = UserEchoMiddleware()

    # Create agent with user resolver and middleware
    agent = Agent(
        llm_service=llm_service,
        tool_registry=tool_registry,
        user_resolver=user_resolver,
        llm_middlewares=[middleware],
        config=AgentConfig(
            stream_responses=True,
            include_thinking_indicators=False,
        ),
    )

    return agent


async def demo_authentication():
    """Demonstrate authentication with different request contexts."""
    agent = create_demo_agent()

    print("=== Mock Authentication Demo ===")
    print("This example verifies that user resolution is working correctly.\n")

    # Test 1: Request with email cookie
    print("🔹 Test 1: Authenticated user (alice@example.com)")
    request_context = RequestContext(
        cookies={'vanna_email': 'alice@example.com'},
        headers={},
        remote_addr='127.0.0.1'
    )

    print("Request context:", {
        'cookies': request_context.cookies,
        'headers': request_context.headers,
        'remote_addr': request_context.remote_addr
    })

    # Send message - Agent will resolve user internally
    agent_response = ""
    async for component in agent.send_message(
        request_context=request_context,
        message="Who am I?",
        conversation_id="test_conv_1"
    ):
        # Extract and display user info from the resolved user
        if hasattr(component, 'rich_component'):
            rich = component.rich_component
            # Check if it's a text component
            if rich.type.value == "text":
                # Access content directly from the component (before serialization)
                if hasattr(rich, 'content'):
                    agent_response = rich.content

    print(f"Agent response: {agent_response}")

    # Verify user was resolved by checking the conversation store
    user_resolver = agent.user_resolver
    resolved_user = await user_resolver.resolve_user(request_context)
    print(f"✅ Resolved user: {resolved_user.email} (username: {resolved_user.username}, id: {resolved_user.id})")
    print(f"   Permissions: {resolved_user.permissions}")
    print(f"   Metadata: {resolved_user.metadata}")

    print("\n" + "="*60 + "\n")

    # Test 2: Request without email cookie (anonymous)
    print("🔹 Test 2: Anonymous user (no cookie)")
    anonymous_context = RequestContext(
        cookies={},
        headers={},
        remote_addr='127.0.0.1'
    )

    print("Request context:", {
        'cookies': anonymous_context.cookies,
        'headers': anonymous_context.headers,
        'remote_addr': anonymous_context.remote_addr
    })

    agent_response = ""
    async for component in agent.send_message(
        request_context=anonymous_context,
        message="Who am I?",
        conversation_id="test_conv_2"
    ):
        if hasattr(component, 'rich_component'):
            rich = component.rich_component
            if rich.type.value == "text" and hasattr(rich, 'content'):
                agent_response = rich.content

    print(f"Agent response: {agent_response}")

    resolved_user = await user_resolver.resolve_user(anonymous_context)
    print(f"✅ Resolved user: {resolved_user.email or 'None'} (username: {resolved_user.username}, id: {resolved_user.id})")
    print(f"   Permissions: {resolved_user.permissions}")
    print(f"   Metadata: {resolved_user.metadata}")

    print("\n" + "="*60 + "\n")

    # Test 3: Different user
    print("🔹 Test 3: Different authenticated user (bob@company.com)")
    bob_context = RequestContext(
        cookies={'vanna_email': 'bob@company.com'},
        headers={'User-Agent': 'Mozilla/5.0'},
        remote_addr='192.168.1.100'
    )

    print("Request context:", {
        'cookies': bob_context.cookies,
        'headers': bob_context.headers,
        'remote_addr': bob_context.remote_addr
    })

    agent_response = ""
    async for component in agent.send_message(
        request_context=bob_context,
        message="Who am I?",
        conversation_id="test_conv_3"
    ):
        if hasattr(component, 'rich_component'):
            rich = component.rich_component
            if rich.type.value == "text" and hasattr(rich, 'content'):
                agent_response = rich.content

    print(f"Agent response: {agent_response}")

    resolved_user = await user_resolver.resolve_user(bob_context)
    print(f"✅ Resolved user: {resolved_user.email} (username: {resolved_user.username}, id: {resolved_user.id})")
    print(f"   Permissions: {resolved_user.permissions}")
    print(f"   Metadata: {resolved_user.metadata}")

    print("\n" + "="*60)
    print("\n✅ Authentication demo complete!")
    print("\nKey Features Verified:")
    print("• UserResolver is part of Agent")
    print("• Agent.send_message() accepts RequestContext")
    print("• User resolution happens internally in Agent")
    print("• CookieEmailUserResolver extracts email from vanna_email cookie")
    print("• Anonymous users are created when no cookie is present")
    print("• Different users can be resolved from different request contexts")


async def main():
    """Run the authentication example."""
    await demo_authentication()


def run_interactive():
    """Entry point for interactive usage."""
    print("Starting mock authentication example...")
    asyncio.run(main())


if __name__ == "__main__":
    run_interactive()
