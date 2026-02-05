"""
Base error recovery strategy interface.

Recovery strategies allow you to customize how the agent handles errors
during tool execution and LLM communication.
"""

from abc import ABC
from typing import TYPE_CHECKING

from .models import RecoveryAction, RecoveryActionType

if TYPE_CHECKING:
    from ..tool.models import ToolContext
    from ..llm import LlmRequest


class ErrorRecoveryStrategy(ABC):
    """Strategy for handling errors and implementing retry logic.

    Subclass this to create custom error recovery strategies that can:
    - Retry failed operations with backoff
    - Fallback to alternative approaches
    - Log errors to external systems
    - Gracefully degrade functionality

    Example:
        class ExponentialBackoffStrategy(ErrorRecoveryStrategy):
            async def handle_tool_error(
                self, error: Exception, context: ToolContext, attempt: int
            ) -> RecoveryAction:
                if attempt < 3:
                    delay = (2 ** attempt) * 1000  # Exponential backoff
                    return RecoveryAction(
                        action=RecoveryActionType.RETRY,
                        retry_delay_ms=delay,
                        message=f"Retrying after {delay}ms"
                    )
                return RecoveryAction(
                    action=RecoveryActionType.FAIL,
                    message="Max retries exceeded"
                )

        agent = AgentRunner(
            llm_service=...,
            error_recovery_strategy=ExponentialBackoffStrategy()
        )
    """

    async def handle_tool_error(
        self, error: Exception, context: "ToolContext", attempt: int = 1
    ) -> RecoveryAction:
        """Handle errors during tool execution.

        Args:
            error: The exception that occurred
            context: Tool execution context
            attempt: Current attempt number (1-indexed)

        Returns:
            RecoveryAction indicating how to proceed
        """
        # Default: fail immediately
        return RecoveryAction(
            action=RecoveryActionType.FAIL, message=f"Tool error: {str(error)}"
        )

    async def handle_llm_error(
        self, error: Exception, request: "LlmRequest", attempt: int = 1
    ) -> RecoveryAction:
        """Handle errors during LLM communication.

        Args:
            error: The exception that occurred
            request: The LLM request that failed
            attempt: Current attempt number (1-indexed)

        Returns:
            RecoveryAction indicating how to proceed
        """
        # Default: fail immediately
        return RecoveryAction(
            action=RecoveryActionType.FAIL, message=f"LLM error: {str(error)}"
        )
