"""
File system conversation store implementation.

This module provides a file-based implementation of the ConversationStore
interface that persists conversations to disk as a directory structure.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import time

from vanna.core.storage import ConversationStore, Conversation, Message
from vanna.core.user import User


class FileSystemConversationStore(ConversationStore):
    """File system-based conversation store.

    Stores conversations as directories with individual message files:
    conversations/{conversation_id}/
        metadata.json - conversation metadata (id, user info, timestamps)
        messages/
            {timestamp}_{index}.json - individual message files
    """

    def __init__(self, base_dir: str = "conversations") -> None:
        """Initialize the file system conversation store.

        Args:
            base_dir: Base directory for storing conversations
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_conversation_dir(self, conversation_id: str) -> Path:
        """Get the directory path for a conversation."""
        return self.base_dir / conversation_id

    def _get_metadata_path(self, conversation_id: str) -> Path:
        """Get the metadata file path for a conversation."""
        return self._get_conversation_dir(conversation_id) / "metadata.json"

    def _get_messages_dir(self, conversation_id: str) -> Path:
        """Get the messages directory for a conversation."""
        return self._get_conversation_dir(conversation_id) / "messages"

    def _save_metadata(self, conversation: Conversation) -> None:
        """Save conversation metadata to disk."""
        conv_dir = self._get_conversation_dir(conversation.id)
        conv_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "id": conversation.id,
            "user": conversation.user.model_dump(mode="json"),
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }

        metadata_path = self._get_metadata_path(conversation.id)
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def _load_messages(self, conversation_id: str) -> List[Message]:
        """Load all messages for a conversation."""
        messages_dir = self._get_messages_dir(conversation_id)

        if not messages_dir.exists():
            return []

        messages = []
        # Sort message files by name (timestamp_index ensures correct order)
        message_files = sorted(messages_dir.glob("*.json"))

        for file_path in message_files:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                message = Message.model_validate(data)
                messages.append(message)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to load message from {file_path}: {e}")
                continue

        return messages

    def _append_message(
        self, conversation_id: str, message: Message, index: int
    ) -> None:
        """Append a message to the conversation."""
        messages_dir = self._get_messages_dir(conversation_id)
        messages_dir.mkdir(parents=True, exist_ok=True)

        # Use timestamp + index to ensure unique, ordered filenames
        timestamp = int(time.time() * 1000000)  # microseconds
        filename = f"{timestamp}_{index:06d}.json"
        file_path = messages_dir / filename

        with open(file_path, "w") as f:
            json.dump(message.model_dump(mode="json"), f, indent=2)

    async def create_conversation(
        self, conversation_id: str, user: User, initial_message: str
    ) -> Conversation:
        """Create a new conversation with the specified ID."""
        conversation = Conversation(
            id=conversation_id,
            user=user,
            messages=[Message(role="user", content=initial_message)],
        )

        # Save metadata
        self._save_metadata(conversation)

        # Save initial message
        self._append_message(conversation_id, conversation.messages[0], 0)

        return conversation

    async def get_conversation(
        self, conversation_id: str, user: User
    ) -> Optional[Conversation]:
        """Get conversation by ID, scoped to user."""
        metadata_path = self._get_metadata_path(conversation_id)

        if not metadata_path.exists():
            return None

        try:
            # Load metadata
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            # Verify ownership
            if metadata["user"]["id"] != user.id:
                return None

            # Load all messages
            messages = self._load_messages(conversation_id)

            # Reconstruct conversation
            conversation = Conversation(
                id=metadata["id"],
                user=User.model_validate(metadata["user"]),
                messages=messages,
                created_at=datetime.fromisoformat(metadata["created_at"]),
                updated_at=datetime.fromisoformat(metadata["updated_at"]),
            )

            return conversation
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Failed to load conversation {conversation_id}: {e}")
            return None

    async def update_conversation(self, conversation: Conversation) -> None:
        """Update conversation with new messages."""
        # Update the updated_at timestamp
        conversation.updated_at = datetime.now()

        # Save updated metadata
        self._save_metadata(conversation)

        # Get existing messages count to determine new message indices
        existing_messages = self._load_messages(conversation.id)
        existing_count = len(existing_messages)

        # Only append new messages (ones not already saved)
        for i, message in enumerate(
            conversation.messages[existing_count:], start=existing_count
        ):
            self._append_message(conversation.id, message, i)

    async def delete_conversation(self, conversation_id: str, user: User) -> bool:
        """Delete conversation."""
        conv_dir = self._get_conversation_dir(conversation_id)

        if not conv_dir.exists():
            return False

        # Verify ownership before deleting
        conversation = await self.get_conversation(conversation_id, user)
        if not conversation:
            return False

        try:
            # Delete all message files
            messages_dir = self._get_messages_dir(conversation_id)
            if messages_dir.exists():
                for file_path in messages_dir.glob("*.json"):
                    file_path.unlink()
                messages_dir.rmdir()

            # Delete metadata
            metadata_path = self._get_metadata_path(conversation_id)
            if metadata_path.exists():
                metadata_path.unlink()

            # Delete conversation directory
            conv_dir.rmdir()

            return True
        except OSError as e:
            print(f"Failed to delete conversation {conversation_id}: {e}")
            return False

    async def list_conversations(
        self, user: User, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        """List conversations for user."""
        if not self.base_dir.exists():
            return []

        conversations = []

        # Iterate through all conversation directories
        for conv_dir in self.base_dir.iterdir():
            if not conv_dir.is_dir():
                continue

            metadata_path = conv_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            try:
                # Load metadata
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)

                # Skip conversations not owned by this user
                if metadata["user"]["id"] != user.id:
                    continue

                # Load messages
                messages = self._load_messages(conv_dir.name)

                # Reconstruct conversation
                conversation = Conversation(
                    id=metadata["id"],
                    user=User.model_validate(metadata["user"]),
                    messages=messages,
                    created_at=datetime.fromisoformat(metadata["created_at"]),
                    updated_at=datetime.fromisoformat(metadata["updated_at"]),
                )
                conversations.append(conversation)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"Failed to load conversation from {conv_dir}: {e}")
                continue

        # Sort by updated_at desc
        conversations.sort(key=lambda x: x.updated_at, reverse=True)

        # Apply pagination
        return conversations[offset : offset + limit]
