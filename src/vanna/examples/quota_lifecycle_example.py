"""
Example demonstrating lifecycle hooks for user quota management.

This example shows how to use lifecycle hooks to add custom functionality
like quota management without creating custom agent runner subclasses.
"""

from typing import Any, Dict, Optional
from vanna.core import Agent, LifecycleHook, User
from vanna.core.errors import AgentError


class QuotaExceededError(AgentError):
    """Raised when a user exceeds their message quota."""
    pass


class QuotaCheckHook(LifecycleHook):
    """Lifecycle hook that enforces user-based message quotas."""

    def __init__(self, default_quota: int = 10) -> None:
        """Initialize quota hook.

        Args:
            default_quota: Default quota per user if not specifically set
        """
        self._user_quotas: Dict[str, int] = {}
        self._user_usage: Dict[str, int] = {}
        self._default_quota = default_quota

    def set_user_quota(self, user_id: str, quota: int) -> None:
        """Set a specific quota for a user."""
        self._user_quotas[user_id] = quota

    def get_user_quota(self, user_id: str) -> int:
        """Get the quota for a user."""
        return self._user_quotas.get(user_id, self._default_quota)

    def get_user_usage(self, user_id: str) -> int:
        """Get current usage count for a user."""
        return self._user_usage.get(user_id, 0)

    def get_user_remaining(self, user_id: str) -> int:
        """Get remaining messages for a user."""
        return self.get_user_quota(user_id) - self.get_user_usage(user_id)

    def reset_user_usage(self, user_id: str) -> None:
        """Reset usage count for a user."""
        self._user_usage[user_id] = 0

    async def before_message(self, user: User, message: str) -> Optional[str]:
        """Check quota before processing message.

        Raises:
            QuotaExceededError: If user has exceeded their quota
        """
        usage = self.get_user_usage(user.id)
        quota = self.get_user_quota(user.id)

        if usage >= quota:
            raise QuotaExceededError(
                f"User {user.username} has exceeded their quota of {quota} messages. "
                f"Current usage: {usage}"
            )

        # Increment usage count
        current_usage = self._user_usage.get(user.id, 0)
        self._user_usage[user.id] = current_usage + 1

        # Don't modify the message
        return None


class LoggingHook(LifecycleHook):
    """Example logging hook for demonstration."""

    async def before_message(self, user: User, message: str) -> Optional[str]:
        """Log incoming messages."""
        print(f"[LOG] User {user.username} ({user.id}) sent message: {message[:50]}...")
        return None

    async def after_message(self, result: Any) -> None:
        """Log message completion."""
        print(f"[LOG] Message processing completed")


async def run_example() -> None:
    """
    Example showing how to use lifecycle hooks with Agent.

    Instead of creating a custom subclass, we compose
    the behavior using lifecycle hooks.
    """
    from vanna.core.registry import ToolRegistry
    from vanna.integrations.anthropic import AnthropicLlmService
    from vanna.integrations.local import MemoryConversationStore

    # Create quota hook
    quota_hook = QuotaCheckHook(default_quota=10)
    quota_hook.set_user_quota("user123", 5)  # Set custom quota for specific user

    # Create logging hook
    logging_hook = LoggingHook()

    # Create agent with multiple hooks
    agent = Agent(
        llm_service=AnthropicLlmService(api_key="your-api-key"),
        tool_registry=ToolRegistry(),
        conversation_store=MemoryConversationStore(),
        lifecycle_hooks=[
            logging_hook,    # Logs will happen first
            quota_hook,      # Then quota check
        ]
    )

    # Create a test user
    user = User(
        id="user123",
        username="test_user",
        email="test@example.com",
        permissions=[]
    )

    # Send messages - will track quota
    try:
        async for component in agent.send_message(
            user=user,
            message="Hello, agent!"
        ):
            # Process UI components
            pass

        # Check remaining quota
        remaining = quota_hook.get_user_remaining(user.id)
        print(f"Remaining messages: {remaining}/{quota_hook.get_user_quota(user.id)}")

    except QuotaExceededError as e:
        print(f"Quota exceeded: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_example())
