"""
Default LLM context enhancer implementation using AgentMemory.

This implementation enriches the system prompt with relevant memories
based on the user's initial message.
"""

from typing import TYPE_CHECKING, Optional
from .base import LlmContextEnhancer

if TYPE_CHECKING:
    from ..user.models import User
    from ..llm.models import LlmMessage
    from ...capabilities.agent_memory import AgentMemory


class DefaultLlmContextEnhancer(LlmContextEnhancer):
    """Default enhancer that uses AgentMemory to add relevant context.

    This enhancer searches the agent's memory for relevant examples and
    tool use patterns based on the user's message, and adds them to the
    system prompt.

    Example:
        agent = Agent(
            llm_service=...,
            agent_memory=agent_memory,
            llm_context_enhancer=DefaultLlmContextEnhancer(agent_memory)
        )
    """

    def __init__(self, agent_memory: Optional["AgentMemory"] = None):
        """Initialize with optional agent memory.

        Args:
            agent_memory: Optional AgentMemory instance. If not provided,
                         enhancement will be skipped.
        """
        self.agent_memory = agent_memory

    async def enhance_system_prompt(
        self,
        system_prompt: str,
        user_message: str,
        user: "User"
    ) -> str:
        """Enhance system prompt with relevant memories.

        Searches agent memory for relevant tool use examples based on the
        user's message and adds them to the system prompt.

        Args:
            system_prompt: The original system prompt
            user_message: The initial user message
            user: The user making the request

        Returns:
            Enhanced system prompt with relevant examples from memory
        """
        if not self.agent_memory:
            return system_prompt

        try:
            # Import here to avoid circular dependency
            from ..tool import ToolContext
            import uuid

            # Create a temporary context for memory search
            context = ToolContext(
                user=user,
                conversation_id="temp",
                request_id=str(uuid.uuid4()),
                agent_memory=self.agent_memory
            )

            # Search for relevant memories based on user message
            memories = await self.agent_memory.search_similar_memories(
                context=context,
                question=user_message,
                limit=5
            )

            if not memories:
                return system_prompt

            # Format memories as examples to add to system prompt
            examples_section = "\n\n## Relevant Examples from Previous Interactions\n\n"
            examples_section += "Here are some similar questions and how they were successfully handled:\n\n"

            for i, memory in enumerate(memories, 1):
                examples_section += f"### Example {i}\n"
                examples_section += f"**Question:** {memory.question}\n"
                examples_section += f"**Tool Used:** {memory.tool_name}\n"
                examples_section += f"**Arguments:** {memory.args}\n"
                if memory.success:
                    examples_section += "**Result:** Success ✓\n"
                else:
                    examples_section += "**Result:** Failed (use this as a counter-example)\n"
                examples_section += "\n"

            # Append examples to system prompt
            return system_prompt + examples_section

        except Exception as e:
            # If memory search fails, return original prompt
            # Don't fail the entire request due to memory issues
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to enhance system prompt with memories: {e}")
            return system_prompt

    async def enhance_user_messages(
        self,
        messages: list["LlmMessage"],
        user: "User"
    ) -> list["LlmMessage"]:
        """Enhance user messages.

        The default implementation doesn't modify user messages.
        Override this to add context to user messages if needed.

        Args:
            messages: The list of messages
            user: The user making the request

        Returns:
            Original list of messages (unmodified)
        """
        return messages
