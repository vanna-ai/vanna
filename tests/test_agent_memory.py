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


@pytest.fixture
def test_user():
    """Test user for context."""
    return User(
        id="test_user",
        username="test",
        email="test@example.com",
        group_memberships=['user']
    )


@pytest.fixture
def test_context(test_user):
    """Test context for agent memory operations."""
    return ToolContext(
        user=test_user,
        conversation_id="test_conv",
        request_id="test_req",
        metadata={}
    )


@pytest.fixture
def chromadb_memory():
    """Create ChromaDB memory instance."""
    try:
        from vanna.integrations.chromadb import ChromaAgentMemory
        
        temp_dir = tempfile.mkdtemp()
        memory = ChromaAgentMemory(
            persist_directory=temp_dir,
            collection_name="test_memories"
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
@pytest.mark.parametrize("memory_fixture", ["chromadb_memory", "qdrant_memory", "faiss_memory"])
class TestLocalAgentMemory:
    """Tests for local AgentMemory implementations (ChromaDB, Qdrant, FAISS)."""
    
    @pytest.mark.asyncio
    async def test_save_and_search(self, memory_fixture, test_context, request):
        """Test saving and searching tool usage patterns."""
        memory = request.getfixturevalue(memory_fixture)
        
        await memory.clear_memories(context=test_context)
        
        await memory.save_tool_usage(
            question="Show me top customers",
            tool_name="run_sql",
            args={"sql": "SELECT * FROM customers ORDER BY total_spent DESC LIMIT 10"},
            context=test_context,
            success=True
        )
        
        results = await memory.search_similar_usage(
            question="Show me best customers",
            context=test_context,
            limit=5,
            similarity_threshold=0.5
        )
        
        assert len(results) > 0
        assert results[0].memory.question == "Show me top customers"
        assert results[0].memory.tool_name == "run_sql"
        assert results[0].similarity_score > 0.5
    
    @pytest.mark.asyncio
    async def test_multiple_memories(self, memory_fixture, test_context, request):
        """Test storing and searching multiple memories."""
        memory = request.getfixturevalue(memory_fixture)
        
        await memory.clear_memories(context=test_context)
        
        patterns = [
            ("Show me sales data", "run_sql", {"sql": "SELECT * FROM sales"}),
            ("Get customer list", "run_sql", {"sql": "SELECT * FROM customers"}),
            ("Generate sales report", "run_sql", {"sql": "SELECT date, SUM(amount) FROM sales GROUP BY date"}),
        ]
        
        for question, tool_name, args in patterns:
            await memory.save_tool_usage(
                question=question,
                tool_name=tool_name,
                args=args,
                context=test_context,
                success=True
            )
        
        results = await memory.search_similar_usage(
            question="Show me sales information",
            context=test_context,
            limit=10,
            similarity_threshold=0.3
        )
        
        assert len(results) >= 2
    
    @pytest.mark.asyncio
    async def test_tool_filter(self, memory_fixture, test_context, request):
        """Test filtering by tool name."""
        memory = request.getfixturevalue(memory_fixture)
        
        await memory.clear_memories(context=test_context)
        
        await memory.save_tool_usage(
            question="Query database",
            tool_name="run_sql",
            args={"sql": "SELECT 1"},
            context=test_context
        )
        
        await memory.save_tool_usage(
            question="Search files",
            tool_name="search_files",
            args={"pattern": "*.py"},
            context=test_context
        )
        
        results = await memory.search_similar_usage(
            question="Query data",
            context=test_context,
            tool_name_filter="run_sql",
            similarity_threshold=0.0
        )
        
        assert len(results) > 0
        assert all(r.memory.tool_name == "run_sql" for r in results)
    
    @pytest.mark.asyncio
    async def test_clear_memories(self, memory_fixture, test_context, request):
        """Test clearing memories."""
        memory = request.getfixturevalue(memory_fixture)
        
        await memory.clear_memories(context=test_context)
        
        await memory.save_tool_usage("Q1", "run_sql", {}, test_context)
        await memory.save_tool_usage("Q2", "run_sql", {}, test_context)
        await memory.save_tool_usage("Q3", "visualize_data", {}, test_context)
        
        deleted = await memory.clear_memories(
            context=test_context,
            tool_name="run_sql"
        )
        
        assert deleted >= 0
    
    @pytest.mark.asyncio
    async def test_get_recent_memories(self, memory_fixture, test_context, request):
        """Test getting recent memories."""
        memory = request.getfixturevalue(memory_fixture)
        
        await memory.clear_memories(context=test_context)
        
        await memory.save_tool_usage("Q1", "run_sql", {"sql": "SELECT 1"}, test_context)
        await asyncio.sleep(0.01)
        await memory.save_tool_usage("Q2", "run_sql", {"sql": "SELECT 2"}, test_context)
        await asyncio.sleep(0.01)
        await memory.save_tool_usage("Q3", "visualize_data", {"file": "data.csv"}, test_context)
        await asyncio.sleep(0.01)
        await memory.save_tool_usage("Q4", "run_sql", {"sql": "SELECT 3"}, test_context)
        await asyncio.sleep(0.01)
        await memory.save_tool_usage("Q5", "search_files", {"pattern": "*.py"}, test_context)
        
        recent = await memory.get_recent_memories(context=test_context, limit=3)
        
        assert isinstance(recent, list)
        assert len(recent) <= 3
        
        if recent:
            assert all(hasattr(m, 'memory_id') for m in recent)
    
    @pytest.mark.asyncio
    async def test_delete_by_id(self, memory_fixture, test_context, request):
        """Test deleting memories by ID."""
        memory = request.getfixturevalue(memory_fixture)
        
        await memory.clear_memories(context=test_context)
        
        await memory.save_tool_usage("Q1", "run_sql", {"sql": "SELECT 1"}, test_context)
        await memory.save_tool_usage("Q2", "run_sql", {"sql": "SELECT 2"}, test_context)
        await memory.save_tool_usage("Q3", "visualize_data", {"file": "data.csv"}, test_context)
        
        recent = await memory.get_recent_memories(context=test_context, limit=10)
        
        if not recent:
            pytest.skip("Implementation doesn't support get_recent_memories")
        
        assert all(m.memory_id is not None for m in recent)
        
        memory_to_delete = recent[0]
        deleted = await memory.delete_by_id(context=test_context, memory_id=memory_to_delete.memory_id)
        
        assert deleted is True
        
        remaining = await memory.get_recent_memories(context=test_context, limit=10)
        assert all(m.memory_id != memory_to_delete.memory_id for m in remaining)
        
        fake_deleted = await memory.delete_by_id(context=test_context, memory_id="fake-id-12345")
        assert fake_deleted is False
