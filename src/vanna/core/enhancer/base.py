"""
LLM context enhancer interface.

LLM context enhancers allow you to add additional context to the system prompt
and user messages before LLM calls.
"""

from abc import ABC
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..user.models import User
    from ..llm.models import LlmMessage


class LlmContextEnhancer(ABC):
    """Enhancer for adding context to LLM prompts and messages.

    Subclass this to create custom enhancers that can:
    - Add relevant context to the system prompt based on the user's initial message
    - Enrich user messages with additional context (e.g., from memory/RAG)
    - Inject relevant examples or documentation
    - Add temporal or environmental context

    Example:
        class MemoryBasedEnhancer(LlmContextEnhancer):
            def __init__(self, agent_memory):
                self.agent_memory = agent_memory

            async def enhance_system_prompt(
                self,
                system_prompt: str,
                user_message: str,
                user: User
            ) -> str:
                # Add relevant examples from memory based on user message
                examples = await self.agent_memory.search_similar(user_message)
                return system_prompt + "\\n\\nRelevant examples:\\n" + examples

            async def enhance_user_messages(
                self,
                messages: list[LlmMessage],
                user: User
            ) -> list[LlmMessage]:
                # Could modify or add to messages
                return messages

        agent = Agent(
            llm_service=...,
            llm_context_enhancer=MemoryBasedEnhancer(agent_memory)
        )
    """

    async def enhance_system_prompt(
        self, system_prompt: str, user_message: str, user: "User"
    ) -> str:
        """Enhance the system prompt with additional context.

        This method is called before the first LLM request with the initial
        user message, allowing you to add relevant context to the system prompt.

        Args:
            system_prompt: The original system prompt
            user_message: The initial user message
            user: The user making the request

        Returns:
            Enhanced system prompt with additional context

        Note:
            This is called once per conversation turn, before any tool calls.
        """
        return system_prompt

    async def enhance_user_messages(
        self, messages: list["LlmMessage"], user: "User"
    ) -> list["LlmMessage"]:
        """Enhance user messages with additional context.

        This method is called to potentially modify or add context to user messages
        before sending them to the LLM.

        Args:
            messages: The list of messages to enhance
            user: The user making the request

        Returns:
            Enhanced list of messages

        Note:
            This is called before each LLM request, including after tool calls.
            Be careful not to add context repeatedly on each iteration.
        """
        return messages
