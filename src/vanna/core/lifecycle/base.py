"""
Base lifecycle hook interface.

Lifecycle hooks allow you to intercept and customize agent behavior
at key points in the execution flow.
"""

from abc import ABC
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..user.models import User
    from ..tool import Tool
    from ..tool.models import ToolContext, ToolResult


class LifecycleHook(ABC):
    """Hook into agent execution lifecycle.

    Subclass this to create custom hooks that can:
    - Modify messages before processing
    - Add logging or telemetry
    - Enforce quotas or rate limits
    - Transform tool results
    - Add custom validation

    Example:
        class LoggingHook(LifecycleHook):
            async def before_message(self, user: User, message: str) -> Optional[str]:
                print(f"User {user.username} sent: {message}")
                return None  # Don't modify

        agent = AgentRunner(
            llm_service=...,
            lifecycle_hooks=[LoggingHook(), QuotaCheckHook()]
        )
    """

    async def before_message(self, user: "User", message: str) -> Optional[str]:
        """Called before processing a user message.

        Args:
            user: User sending the message
            message: Original message content

        Returns:
            Modified message string, or None to keep original

        Raises:
            AgentError: To halt message processing (e.g., quota exceeded)
        """
        return None

    async def after_message(self, result: Any) -> None:
        """Called after message has been fully processed.

        Args:
            result: Final result from message processing
        """
        pass

    async def before_tool(self, tool: "Tool[Any]", context: "ToolContext") -> None:
        """Called before tool execution.

        Args:
            tool: Tool about to be executed
            context: Tool execution context

        Raises:
            AgentError: To prevent tool execution
        """
        pass

    async def after_tool(self, result: "ToolResult") -> Optional["ToolResult"]:
        """Called after tool execution.

        Args:
            result: Result from tool execution

        Returns:
            Modified ToolResult, or None to keep original
        """
        return None
