"""
Storage domain interface.

This module contains the abstract base class for conversation storage.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import Conversation


class ConversationStore(ABC):
    """Abstract base class for conversation storage."""

    @abstractmethod
    async def create_conversation(
        self, user_id: str, initial_message: str
    ) -> Conversation:
        """Create a new conversation."""
        pass

    @abstractmethod
    async def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Conversation]:
        """Get conversation by ID, scoped to user."""
        pass

    @abstractmethod
    async def update_conversation(self, conversation: Conversation) -> None:
        """Update conversation with new messages."""
        pass

    @abstractmethod
    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete conversation."""
        pass

    @abstractmethod
    async def list_conversations(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        """List conversations for user."""
        pass
