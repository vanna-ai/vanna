"""
Integration tests for AgentMemory implementations.

These tests verify actual functionality against running services.
Tests are marked by implementation and skip if dependencies are unavailable.
"""

import pytest
import asyncio
import tempfile
import shutil
import os
from vanna.core.user import User
from vanna.core.tool import ToolContext
from vanna.integrations.local.agent_memory import DemoAgentMemory


@pytest.fixture
def test_user():
    """Test user for context."""
    return User(
        id="test_user",
        username="test",
        email="test@example.com",
        group_memberships=["user"],
    )


def create_test_context(test_user, agent_memory):
    """Helper to create test context with specific agent memory."""
    return ToolContext(
        user=test_user,
        conversation_id="test_conv",
        request_id="test_req",
        agent_memory=agent_memory,
        metadata={},
    )


@pytest.fixture
def chromadb_memory():
    """Create ChromaDB memory instance."""
    try:
        from vanna.integrations.chromadb import ChromaAgentMemory

        temp_dir = tempfile.mkdtemp()
        memory = ChromaAgentMemory(
            persist_directory=temp_dir, collection_name="test_memories"
        )

        yield memory

        shutil.rmtree(temp_dir, ignore_errors=True)
    except ImportError:
        pytest.skip("ChromaDB not installed")


@pytest.fixture
def qdrant_memory():
    """Create Qdrant memory instance."""
    try:
        from vanna.integrations.qdrant import QdrantAgentMemory

        temp_dir = tempfile.mkdtemp()
        memory = QdrantAgentMemory(path=temp_dir)

        yield memory

        shutil.rmtree(temp_dir, ignore_errors=True)
    except ImportError:
        pytest.skip("Qdrant not installed")


@pytest.fixture
def faiss_memory():
    """Create FAISS memory instance."""
    try:
        from vanna.integrations.faiss import FAISSAgentMemory

        temp_dir = tempfile.mkdtemp()
        memory = FAISSAgentMemory(persist_path=temp_dir)

        yield memory

        shutil.rmtree(temp_dir, ignore_errors=True)
    except ImportError:
        pytest.skip("FAISS not installed")


# Parametrized tests for local implementations
@pytest.mark.parametrize(
    "memory_fixture", ["chromadb_memory", "qdrant_memory", "faiss_memory"]
)
class TestLocalAgentMemory:
    """Tests for local AgentMemory implementations (ChromaDB, Qdrant, FAISS)."""

    @pytest.mark.asyncio
    async def test_save_and_search(self, memory_fixture, test_user, request):
        """Test saving and searching tool usage patterns."""
        memory = request.getfixturevalue(memory_fixture)
        test_context = create_test_context(test_user, memory)

        await memory.clear_memories(context=test_context)

        await memory.save_tool_usage(
            question="Show me top customers",
            tool_name="run_sql",
            args={"sql": "SELECT * FROM customers ORDER BY total_spent DESC LIMIT 10"},
            context=test_context,
            success=True,
        )

        results = await memory.search_similar_usage(
            question="Show me best customers",
            context=test_context,
            limit=5,
            similarity_threshold=0.5,
        )

        assert len(results) > 0
        assert results[0].memory.question == "Show me top customers"
        assert results[0].memory.tool_name == "run_sql"
        assert results[0].similarity_score > 0.5

    @pytest.mark.asyncio
    async def test_multiple_memories(self, memory_fixture, test_user, request):
        """Test storing and searching multiple memories."""
        memory = request.getfixturevalue(memory_fixture)
        test_context = create_test_context(test_user, memory)

        await memory.clear_memories(context=test_context)

        patterns = [
            ("Show me sales data", "run_sql", {"sql": "SELECT * FROM sales"}),
            ("Get customer list", "run_sql", {"sql": "SELECT * FROM customers"}),
            (
                "Generate sales report",
                "run_sql",
                {"sql": "SELECT date, SUM(amount) FROM sales GROUP BY date"},
            ),
        ]

        for question, tool_name, args in patterns:
            await memory.save_tool_usage(
                question=question,
                tool_name=tool_name,
                args=args,
                context=test_context,
                success=True,
            )

        results = await memory.search_similar_usage(
            question="Show me sales information",
            context=test_context,
            limit=10,
            similarity_threshold=0.3,
        )

        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_tool_filter(self, memory_fixture, test_user, request):
        """Test filtering by tool name."""
        memory = request.getfixturevalue(memory_fixture)
        test_context = create_test_context(test_user, memory)

        await memory.clear_memories(context=test_context)

        await memory.save_tool_usage(
            question="Query database",
            tool_name="run_sql",
            args={"sql": "SELECT 1"},
            context=test_context,
        )

        await memory.save_tool_usage(
            question="Search files",
            tool_name="search_files",
            args={"pattern": "*.py"},
            context=test_context,
        )

        results = await memory.search_similar_usage(
            question="Query data",
            context=test_context,
            tool_name_filter="run_sql",
            similarity_threshold=0.0,
        )

        assert len(results) > 0
        assert all(r.memory.tool_name == "run_sql" for r in results)

    @pytest.mark.asyncio
    async def test_clear_memories(self, memory_fixture, test_user, request):
        """Test clearing memories."""
        memory = request.getfixturevalue(memory_fixture)
        test_context = create_test_context(test_user, memory)

        await memory.clear_memories(context=test_context)

        await memory.save_tool_usage("Q1", "run_sql", {}, test_context)
        await memory.save_tool_usage("Q2", "run_sql", {}, test_context)
        await memory.save_tool_usage("Q3", "visualize_data", {}, test_context)

        deleted = await memory.clear_memories(context=test_context, tool_name="run_sql")

        assert deleted >= 0

    @pytest.mark.asyncio
    async def test_get_recent_memories(self, memory_fixture, test_user, request):
        """Test getting recent memories."""
        memory = request.getfixturevalue(memory_fixture)
        test_context = create_test_context(test_user, memory)

        await memory.clear_memories(context=test_context)

        await memory.save_tool_usage("Q1", "run_sql", {"sql": "SELECT 1"}, test_context)
        await asyncio.sleep(0.01)
        await memory.save_tool_usage("Q2", "run_sql", {"sql": "SELECT 2"}, test_context)
        await asyncio.sleep(0.01)
        await memory.save_tool_usage(
            "Q3", "visualize_data", {"file": "data.csv"}, test_context
        )
        await asyncio.sleep(0.01)
        await memory.save_tool_usage("Q4", "run_sql", {"sql": "SELECT 3"}, test_context)
        await asyncio.sleep(0.01)
        await memory.save_tool_usage(
            "Q5", "search_files", {"pattern": "*.py"}, test_context
        )

        recent = await memory.get_recent_memories(context=test_context, limit=3)

        assert isinstance(recent, list)
        assert len(recent) <= 3

        if recent:
            assert all(hasattr(m, "memory_id") for m in recent)

    @pytest.mark.asyncio
    async def test_delete_by_id(self, memory_fixture, test_user, request):
        """Test deleting memories by ID."""
        memory = request.getfixturevalue(memory_fixture)
        test_context = create_test_context(test_user, memory)

        await memory.clear_memories(context=test_context)

        await memory.save_tool_usage("Q1", "run_sql", {"sql": "SELECT 1"}, test_context)
        await memory.save_tool_usage("Q2", "run_sql", {"sql": "SELECT 2"}, test_context)
        await memory.save_tool_usage(
            "Q3", "visualize_data", {"file": "data.csv"}, test_context
        )

        recent = await memory.get_recent_memories(context=test_context, limit=10)

        if not recent:
            pytest.skip("Implementation doesn't support get_recent_memories")

        assert all(m.memory_id is not None for m in recent)

        memory_to_delete = recent[0]
        deleted = await memory.delete_by_id(
            context=test_context, memory_id=memory_to_delete.memory_id
        )

        assert deleted is True

        remaining = await memory.get_recent_memories(context=test_context, limit=10)
        assert all(m.memory_id != memory_to_delete.memory_id for m in remaining)

        fake_deleted = await memory.delete_by_id(
            context=test_context, memory_id="fake-id-12345"
        )
        assert fake_deleted is False

    @pytest.mark.asyncio
    async def test_save_and_search_text_memories(
        self, memory_fixture, test_user, request
    ):
        """Test saving and searching text memories."""
        memory = request.getfixturevalue(memory_fixture)
        test_context = create_test_context(test_user, memory)

        await memory.clear_memories(context=test_context)

        # Save a text memory
        text_memory = await memory.save_text_memory(
            content="The status column uses 1 for active, 0 for inactive",
            context=test_context,
        )

        assert text_memory.memory_id is not None
        assert (
            text_memory.content == "The status column uses 1 for active, 0 for inactive"
        )

        # Search for similar text memories
        results = await memory.search_text_memories(
            query="status column meaning",
            context=test_context,
            limit=5,
            similarity_threshold=0.3,
        )

        assert len(results) > 0
        assert (
            results[0].memory.content
            == "The status column uses 1 for active, 0 for inactive"
        )
        assert results[0].similarity_score > 0.3

    @pytest.mark.asyncio
    async def test_multiple_text_memories(self, memory_fixture, test_user, request):
        """Test storing and searching multiple text memories."""
        memory = request.getfixturevalue(memory_fixture)
        test_context = create_test_context(test_user, memory)

        await memory.clear_memories(context=test_context)

        text_contents = [
            "The fiscal year starts in April",
            "MRR means Monthly Recurring Revenue",
            "Always exclude test accounts where email contains 'test'",
        ]

        for content in text_contents:
            await memory.save_text_memory(content=content, context=test_context)

        # Search for fiscal year info
        results = await memory.search_text_memories(
            query="When does the fiscal year start?",
            context=test_context,
            limit=10,
            similarity_threshold=0.2,
        )

        assert len(results) >= 1
        assert any("fiscal year" in r.memory.content.lower() for r in results)

    @pytest.mark.asyncio
    async def test_get_recent_text_memories(self, memory_fixture, test_user, request):
        """Test getting recent text memories."""
        memory = request.getfixturevalue(memory_fixture)
        test_context = create_test_context(test_user, memory)

        await memory.clear_memories(context=test_context)

        await memory.save_text_memory("First text memory", test_context)
        await asyncio.sleep(0.01)
        await memory.save_text_memory("Second text memory", test_context)
        await asyncio.sleep(0.01)
        await memory.save_text_memory("Third text memory", test_context)

        recent = await memory.get_recent_text_memories(context=test_context, limit=2)

        assert isinstance(recent, list)
        assert len(recent) <= 2

        if recent:
            assert all(hasattr(m, "memory_id") for m in recent)
            assert all(hasattr(m, "content") for m in recent)

    @pytest.mark.asyncio
    async def test_delete_text_memory(self, memory_fixture, test_user, request):
        """Test deleting text memories by ID."""
        memory = request.getfixturevalue(memory_fixture)
        test_context = create_test_context(test_user, memory)

        await memory.clear_memories(context=test_context)

        text_memory = await memory.save_text_memory(
            "Test memory to delete", test_context
        )

        assert text_memory.memory_id is not None

        deleted = await memory.delete_text_memory(
            context=test_context, memory_id=text_memory.memory_id
        )

        assert deleted is True

        # Verify it's gone
        recent = await memory.get_recent_text_memories(context=test_context, limit=10)
        assert all(m.memory_id != text_memory.memory_id for m in recent)

        # Try deleting non-existent memory
        fake_deleted = await memory.delete_text_memory(
            context=test_context, memory_id="fake-text-id-12345"
        )
        assert fake_deleted is False

    @pytest.mark.asyncio
    async def test_mixed_tool_and_text_memories(
        self, memory_fixture, test_user, request
    ):
        """Test that tool memories and text memories can coexist without errors."""
        memory = request.getfixturevalue(memory_fixture)
        test_context = create_test_context(test_user, memory)

        await memory.clear_memories(context=test_context)

        # Save some tool memories
        await memory.save_tool_usage(
            question="Show me top customers",
            tool_name="run_sql",
            args={"sql": "SELECT * FROM customers"},
            context=test_context,
        )

        # Save some text memories
        await memory.save_text_memory(
            content="The fiscal year starts in April",
            context=test_context,
        )

        await memory.save_tool_usage(
            question="Get sales data",
            tool_name="run_sql",
            args={"sql": "SELECT * FROM sales"},
            context=test_context,
        )

        await memory.save_text_memory(
            content="MRR means Monthly Recurring Revenue",
            context=test_context,
        )

        # This should only return tool memories, not text memories
        tool_memories = await memory.get_recent_memories(context=test_context, limit=10)

        assert isinstance(tool_memories, list)
        assert len(tool_memories) == 2  # Should only have the 2 tool memories
        assert all(hasattr(m, "question") for m in tool_memories)
        assert all(hasattr(m, "tool_name") for m in tool_memories)

        # This should only return text memories, not tool memories
        text_memories = await memory.get_recent_text_memories(
            context=test_context, limit=10
        )

        assert isinstance(text_memories, list)
        assert len(text_memories) == 2  # Should only have the 2 text memories
        assert all(hasattr(m, "content") for m in text_memories)
        assert all(
            "fiscal year" in m.content or "MRR" in m.content for m in text_memories
        )
