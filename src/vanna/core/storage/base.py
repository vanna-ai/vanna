"""
Storage domain interface.

This module contains the abstract base class for conversation storage.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import Conversation
from ..user.models import User


class ConversationStore(ABC):
    """Abstract base class for conversation storage."""

    @abstractmethod
    async def create_conversation(
        self, conversation_id: str, user: User, initial_message: str
    ) -> Conversation:
        """Create a new conversation with the specified ID."""
        pass

    @abstractmethod
    async def get_conversation(
        self, conversation_id: str, user: User
    ) -> Optional[Conversation]:
        """Get conversation by ID, scoped to user."""
        pass

    @abstractmethod
    async def update_conversation(self, conversation: Conversation) -> None:
        """Update conversation with new messages."""
        pass

    @abstractmethod
    async def delete_conversation(self, conversation_id: str, user: User) -> bool:
        """Delete conversation."""
        pass

    @abstractmethod
    async def list_conversations(
        self, user: User, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        """List conversations for user."""
        pass
