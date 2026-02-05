"""
Base conversation filter interface.

Conversation filters allow you to transform conversation history before
it's sent to the LLM for processing.
"""

from abc import ABC
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..storage import Message


class ConversationFilter(ABC):
    """Filter for transforming conversation history.

    Subclass this to create custom filters that can:
    - Remove sensitive information
    - Summarize long conversations
    - Manage context window limits
    - Deduplicate similar messages
    - Prioritize recent or relevant messages

    Example:
        class ContextWindowFilter(ConversationFilter):
            def __init__(self, max_tokens: int = 8000):
                self.max_tokens = max_tokens

            async def filter_messages(self, messages: List[Message]) -> List[Message]:
                # Estimate tokens (rough approximation)
                total_tokens = 0
                filtered = []

                # Keep system message and recent messages
                for msg in reversed(messages):
                    msg_tokens = len(msg.content or "") // 4
                    if total_tokens + msg_tokens > self.max_tokens:
                        break
                    filtered.insert(0, msg)
                    total_tokens += msg_tokens

                return filtered

        agent = AgentRunner(
            llm_service=...,
            conversation_filters=[
                SensitiveDataFilter(),
                ContextWindowFilter(max_tokens=8000)
            ]
        )
    """

    async def filter_messages(self, messages: List["Message"]) -> List["Message"]:
        """Filter and transform conversation messages.

        Args:
            messages: List of conversation messages

        Returns:
            Filtered/transformed list of messages

        Note:
            Filters are applied in order, so messages passed to later
            filters may already be modified by earlier filters.
        """
        return messages
