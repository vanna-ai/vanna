"""
In-memory conversation store implementation.

This module provides a simple in-memory implementation of the ConversationStore
interface, useful for testing and development.
"""

import uuid
from typing import Dict, List, Optional

from vanna.core.errors import ConversationNotFoundError
from vanna.core.storage import ConversationStore, Conversation, Message


class MemoryConversationStore(ConversationStore):
    """In-memory conversation store."""

    def __init__(self) -> None:
        self._conversations: Dict[str, Conversation] = {}

    async def create_conversation(
        self, user_id: str, initial_message: str
    ) -> Conversation:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            messages=[Message(role="user", content=initial_message)],
        )
        self._conversations[conversation_id] = conversation
        return conversation

    async def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Conversation]:
        """Get conversation by ID, scoped to user."""
        conversation = self._conversations.get(conversation_id)
        if conversation and conversation.user_id == user_id:
            return conversation
        return None

    async def update_conversation(self, conversation: Conversation) -> None:
        """Update conversation with new messages."""
        self._conversations[conversation.id] = conversation

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete conversation."""
        conversation = await self.get_conversation(conversation_id, user_id)
        if conversation:
            del self._conversations[conversation_id]
            return True
        return False

    async def list_conversations(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        """List conversations for user."""
        user_conversations = [
            conv for conv in self._conversations.values() if conv.user_id == user_id
        ]
        # Sort by updated_at desc
        user_conversations.sort(key=lambda x: x.updated_at, reverse=True)
        return user_conversations[offset : offset + limit]
