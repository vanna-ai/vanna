"""
Default system prompt builder implementation.

This module provides a default implementation of the SystemPromptBuilder interface
that can be overridden by users of the package.
"""

from typing import Any, List, Optional

from .base import SystemPromptBuilder


class DefaultSystemPromptBuilder(SystemPromptBuilder):
    """Default system prompt builder.

    Generates a simple system prompt that includes information about available tools.
    Users can subclass this or provide their own implementation.
    """

    def __init__(self, base_prompt: Optional[str] = None):
        """Initialize with an optional base prompt.

        Args:
            base_prompt: Optional base system prompt. If not provided, uses a default.
        """
        self.base_prompt = base_prompt

    async def build_system_prompt(
        self, user: Any, tools: Any
    ) -> Optional[str]:
        """Build a system prompt based on user context and available tools.

        Args:
            user: The user making the request
            tools: List of tools available to the user

        Returns:
            System prompt string, or None if no system prompt should be used
        """
        if self.base_prompt is not None:
            return self.base_prompt

        # Default system prompt
        prompt_parts = [
            "You are a helpful AI assistant with access to tools.",
            "Use the available tools to help the user accomplish their goals.",
        ]

        if tools:
            tool_names = [tool.name for tool in tools]
            prompt_parts.append(
                f"\nYou have access to the following tools: {', '.join(tool_names)}"
            )

        return "\n".join(prompt_parts)
