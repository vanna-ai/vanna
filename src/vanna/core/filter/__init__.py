"""
Conversation filtering system for managing conversation history.

This module provides interfaces for filtering and transforming conversation
history before it's sent to the LLM.
"""

from .base import ConversationFilter

__all__ = ["ConversationFilter"]
