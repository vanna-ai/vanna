"""
System prompt builder interface.

This module contains the abstract base class for system prompt builders.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ..tool.models import ToolSchema
    from ..user.models import User


class SystemPromptBuilder(ABC):
    """Abstract base class for system prompt builders.

    Subclasses should implement the build_system_prompt method to generate
    system prompts based on user context and available tools.
    """

    @abstractmethod
    async def build_system_prompt(
        self,
        user: "User",
        tools: List["ToolSchema"],
        *,
        require_human_approval_for_memory: bool = False,
    ) -> Optional[str]:
        """
        Build a system prompt based on user context and available tools.

        Args:
            user: The user making the request
            tools: List of tools available to the user
            require_human_approval_for_memory: If True, the LLM must not call
                save_question_tool_args; only the user can save via the Save to memory button.

        Returns:
            System prompt string, or None if no system prompt should be used
        """
        pass
