"""
Demo in-memory implementation of AgentMemory.

This implementation provides a zero-dependency, minimal storage solution that
keeps all memories in RAM. It uses simple similarity algorithms (Jaccard and
difflib) instead of vector embeddings. Perfect for demos and testing.
"""

from __future__ import annotations

import asyncio
import difflib
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from vanna.core.tool import ToolContext


class DemoAgentMemory(AgentMemory):
    """
    Minimal, dependency-free in-memory storage for demos and testing.
    - O(n) search over an in-memory list
    - Simple similarity: max(Jaccard(token sets), difflib ratio)
    - Optional FIFO eviction via max_items
    - Async-safe with an asyncio.Lock
    """

    def __init__(self, *, max_items: int = 10_000):
        """
        Initialize the in-memory storage.

        Args:
            max_items: Maximum number of memories to keep. Oldest memories are
                      evicted when this limit is reached (FIFO).
        """
        self._memories: List[ToolMemory] = []
        self._lock = asyncio.Lock()
        self._max_items = max_items

    @staticmethod
    def _now_iso() -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text by lowercasing and collapsing whitespace."""
        return " ".join(text.lower().split())

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Simple tokenizer that splits on whitespace."""
        return set(text.lower().split())

    @classmethod
    def _similarity(cls, a: str, b: str) -> float:
        """
        Calculate similarity between two strings using multiple methods.

        Returns the maximum of Jaccard similarity and difflib ratio.
        """
        a_norm, b_norm = cls._normalize(a), cls._normalize(b)

        # Jaccard over whitespace tokens
        ta, tb = cls._tokenize(a_norm), cls._tokenize(b_norm)
        if not ta and not tb:
            jaccard = 1.0
        elif not ta or not tb:
            jaccard = 0.0
        else:
            jaccard = len(ta & tb) / max(1, len(ta | tb))

        # difflib ratio
        ratio = difflib.SequenceMatcher(None, a_norm, b_norm).ratio()

        # Take the better of the two cheap measures
        return max(jaccard, ratio)

    async def save_tool_usage(
        self,
        question: str,
        tool_name: str,
        args: Dict[str, Any],
        context: ToolContext,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save a tool usage pattern for future reference."""
        tm = ToolMemory(
            memory_id=str(uuid.uuid4()),
            question=question,
            tool_name=tool_name,
            args=args,
            timestamp=self._now_iso(),
            success=success,
            metadata=metadata or {},
        )
        async with self._lock:
            self._memories.append(tm)
            # Optional FIFO eviction
            if len(self._memories) > self._max_items:
                overflow = len(self._memories) - self._max_items
                del self._memories[:overflow]

    async def search_similar_usage(
        self,
        question: str,
        context: ToolContext,
        *,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        tool_name_filter: Optional[str] = None
    ) -> List[MemorySearchResult]:
        """Search for similar tool usage patterns based on a question."""
        q = self._normalize(question)

        async with self._lock:
            # Filter candidates by tool name and success status
            candidates = [
                m for m in self._memories
                if m.success and (tool_name_filter is None or m.tool_name == tool_name_filter)
            ]

            # Score each candidate by question similarity
            results: List[tuple[ToolMemory, float]] = []
            for m in candidates:
                score = self._similarity(q, m.question)
                results.append((m, min(score, 1.0)))

            # Filter by threshold and sort by score
            results = [(m, s) for (m, s) in results if s >= similarity_threshold]
            results.sort(key=lambda x: x[1], reverse=True)

            # Build ranked response
            out: List[MemorySearchResult] = []
            for idx, (m, s) in enumerate(results[:limit], start=1):
                out.append(MemorySearchResult(memory=m, similarity_score=s, rank=idx))
            return out

    async def get_recent_memories(
        self,
        context: ToolContext,
        limit: int = 10
    ) -> List[ToolMemory]:
        """Get recently added memories. Returns most recent memories first."""
        async with self._lock:
            # Return memories in reverse order (most recent first)
            return list(reversed(self._memories[-limit:]))

    async def delete_by_id(
        self,
        context: ToolContext,
        memory_id: str
    ) -> bool:
        """Delete a memory by its ID. Returns True if deleted, False if not found."""
        async with self._lock:
            for i, m in enumerate(self._memories):
                if m.memory_id == memory_id:
                    del self._memories[i]
                    return True
            return False

    async def clear_memories(
        self,
        context: ToolContext,
        tool_name: Optional[str] = None,
        before_date: Optional[str] = None
    ) -> int:
        """Clear stored memories. Returns number of memories deleted."""
        async with self._lock:
            original_count = len(self._memories)

            # Filter memories to keep
            kept_memories = []
            for m in self._memories:
                should_delete = True

                # Check tool name filter
                if tool_name and m.tool_name != tool_name:
                    should_delete = False

                # Check date filter
                if should_delete and before_date and m.timestamp:
                    if m.timestamp >= before_date:
                        should_delete = False

                # If no filters specified, delete all
                if tool_name is None and before_date is None:
                    should_delete = True

                # Keep if should not delete
                if not should_delete:
                    kept_memories.append(m)

            self._memories = kept_memories
            deleted_count = original_count - len(self._memories)
            return deleted_count
