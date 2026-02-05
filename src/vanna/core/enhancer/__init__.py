"""
LLM context enhancement system for adding context to prompts and messages.

This module provides interfaces for enriching LLM system prompts and messages
with additional context before LLM calls (e.g., from memory, RAG, documentation).
"""

from .base import LlmContextEnhancer
from .default import DefaultLlmContextEnhancer

__all__ = ["LlmContextEnhancer", "DefaultLlmContextEnhancer"]
