"""
In-memory conversation store implementation.

This module provides a simple in-memory implementation of the ConversationStore
interface, useful for testing and development.
"""

from typing import Dict, List, Optional

from vanna.core.storage import ConversationStore, Conversation, Message
from vanna.core.user import User


class MemoryConversationStore(ConversationStore):
    """In-memory conversation store."""

    def __init__(self) -> None:
        self._conversations: Dict[str, Conversation] = {}

    async def create_conversation(
        self, conversation_id: str, user: User, initial_message: str
    ) -> Conversation:
        """Create a new conversation with the specified ID."""
        conversation = Conversation(
            id=conversation_id,
            user=user,
            messages=[Message(role="user", content=initial_message)],
        )
        self._conversations[conversation_id] = conversation
        return conversation

    async def get_conversation(
        self, conversation_id: str, user: User
    ) -> Optional[Conversation]:
        """Get conversation by ID, scoped to user."""
        conversation = self._conversations.get(conversation_id)
        if conversation and conversation.user.id == user.id:
            return conversation
        return None

    async def update_conversation(self, conversation: Conversation) -> None:
        """Update conversation with new messages."""
        self._conversations[conversation.id] = conversation

    async def delete_conversation(self, conversation_id: str, user: User) -> bool:
        """Delete conversation."""
        conversation = await self.get_conversation(conversation_id, user)
        if conversation:
            del self._conversations[conversation_id]
            return True
        return False

    async def list_conversations(
        self, user: User, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        """List conversations for user."""
        user_conversations = [
            conv for conv in self._conversations.values() if conv.user.id == user.id
        ]
        # Sort by updated_at desc
        user_conversations.sort(key=lambda x: x.updated_at, reverse=True)
        return user_conversations[offset : offset + limit]
