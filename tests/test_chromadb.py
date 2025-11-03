"""
Tests for ChromaDB agent memory integration.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

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
def temp_chroma_dir():
    """Temporary directory for ChromaDB storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.chromadb
@pytest.mark.asyncio
async def test_chromadb_import():
    """Test that ChromaDB agent memory can be imported."""
    try:
        from vanna.integrations.chromadb import ChromaAgentMemory
        print("✓ ChromaAgentMemory imported successfully")
        assert ChromaAgentMemory is not None
    except ImportError as e:
        pytest.fail(f"Failed to import ChromaAgentMemory: {e}")


@pytest.mark.chromadb
@pytest.mark.asyncio
async def test_chromadb_initialization(temp_chroma_dir):
    """Test ChromaDB initialization."""
    from vanna.integrations.chromadb import ChromaAgentMemory
    
    print(f"\n=== ChromaDB Initialization Test ===")
    print(f"Temp directory: {temp_chroma_dir}")
    
    try:
        memory = ChromaAgentMemory(
            persist_directory=temp_chroma_dir,
            collection_name="test_memories"
        )
        
        print(f"✓ ChromaAgentMemory initialized")
        print(f"  Persist directory: {memory.persist_directory}")
        print(f"  Collection name: {memory.collection_name}")
        
        assert memory.persist_directory == temp_chroma_dir
        assert memory.collection_name == "test_memories"
        
    except Exception as e:
        pytest.fail(f"Failed to initialize ChromaAgentMemory: {e}")


@pytest.mark.chromadb
@pytest.mark.asyncio
async def test_chromadb_save_and_search(temp_chroma_dir, test_context):
    """Test saving and searching tool usage patterns."""
    from vanna.integrations.chromadb import ChromaAgentMemory
    
    print(f"\n=== ChromaDB Save & Search Test ===")
    
    memory = ChromaAgentMemory(
        persist_directory=temp_chroma_dir,
        collection_name="test_memories"
    )
    
    # Save a tool usage pattern
    await memory.save_tool_usage(
        question="Show me top customers",
        tool_name="run_sql",
        args={"sql": "SELECT * FROM customers ORDER BY total_spent DESC LIMIT 10"},
        context=test_context,
        success=True
    )
    
    print("✓ Saved tool usage pattern")
    
    # Search for similar usage
    results = await memory.search_similar_usage(
        question="Show me best customers",
        context=test_context,
        limit=5,
        similarity_threshold=0.5
    )
    
    print(f"✓ Search completed")
    print(f"  Results found: {len(results)}")
    
    assert len(results) > 0
    assert results[0].memory.question == "Show me top customers"
    assert results[0].memory.tool_name == "run_sql"
    assert results[0].memory.args["sql"] == "SELECT * FROM customers ORDER BY total_spent DESC LIMIT 10"
    assert results[0].similarity_score > 0.5
    
    print(f"  Top result similarity: {results[0].similarity_score:.2f}")


@pytest.mark.chromadb
@pytest.mark.asyncio
async def test_chromadb_multiple_memories(temp_chroma_dir, test_context):
    """Test storing and searching multiple memories."""
    from vanna.integrations.chromadb import ChromaAgentMemory
    
    print(f"\n=== Multiple Memories Test ===")
    
    memory = ChromaAgentMemory(
        persist_directory=temp_chroma_dir,
        collection_name="test_memories"
    )
    
    # Save multiple patterns
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
    
    print(f"✓ Saved {len(patterns)} patterns")
    
    # Search for sales-related queries
    results = await memory.search_similar_usage(
        question="Show me sales information",
        context=test_context,
        limit=10,
        similarity_threshold=0.3
    )
    
    print(f"✓ Search found {len(results)} similar patterns")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result.memory.question} (similarity: {result.similarity_score:.2f})")
    
    assert len(results) >= 2  # Should find at least the sales-related ones


@pytest.mark.chromadb
@pytest.mark.asyncio
async def test_chromadb_tool_filter(temp_chroma_dir, test_context):
    """Test filtering by tool name."""
    from vanna.integrations.chromadb import ChromaAgentMemory
    
    print(f"\n=== Tool Filtering Test ===")
    
    memory = ChromaAgentMemory(
        persist_directory=temp_chroma_dir,
        collection_name="test_memories"
    )
    
    # Save patterns for different tools
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
    
    # Search only for run_sql patterns
    results = await memory.search_similar_usage(
        question="Query data",
        context=test_context,
        tool_name_filter="run_sql",
        similarity_threshold=0.0  # Accept all for testing
    )
    
    print(f"✓ Filtered search found {len(results)} run_sql patterns")
    
    assert len(results) > 0
    assert all(r.memory.tool_name == "run_sql" for r in results)


@pytest.mark.chromadb
@pytest.mark.asyncio
async def test_chromadb_stats(temp_chroma_dir, test_context):
    """Test getting usage statistics."""
    from vanna.integrations.chromadb import ChromaAgentMemory
    
    print(f"\n=== Statistics Test ===")
    
    memory = ChromaAgentMemory(
        persist_directory=temp_chroma_dir,
        collection_name="test_memories"
    )
    
    # Save some patterns
    await memory.save_tool_usage(
        question="Q1",
        tool_name="run_sql",
        args={"sql": "SELECT 1"},
        context=test_context
    )
    
    await memory.save_tool_usage(
        question="Q2",
        tool_name="run_sql",
        args={"sql": "SELECT 2"},
        context=test_context
    )
    
    await memory.save_tool_usage(
        question="Q3",
        tool_name="visualize_data",
        args={"filename": "data.csv"},
        context=test_context
    )
    
    # Get stats
    stats = await memory.get_tool_usage_stats(context=test_context)
    
    print(f"✓ Statistics retrieved")
    print(f"  Total memories: {stats['total_memories']}")
    print(f"  Unique tools: {stats['unique_tools']}")
    print(f"  Unique questions: {stats['unique_questions']}")
    print(f"  Most used tools: {stats['most_used_tools']}")
    
    assert stats['total_memories'] == 3
    assert stats['unique_tools'] == 2
    assert stats['unique_questions'] == 3
    assert stats['most_used_tools']['run_sql'] == 2
    assert stats['most_used_tools']['visualize_data'] == 1


@pytest.mark.chromadb
@pytest.mark.asyncio
async def test_chromadb_list_tools(temp_chroma_dir, test_context):
    """Test listing tools with memories."""
    from vanna.integrations.chromadb import ChromaAgentMemory
    
    print(f"\n=== List Tools Test ===")
    
    memory = ChromaAgentMemory(
        persist_directory=temp_chroma_dir,
        collection_name="test_memories"
    )
    
    # Save patterns for different tools
    await memory.save_tool_usage("Q1", "run_sql", {}, test_context)
    await memory.save_tool_usage("Q2", "visualize_data", {}, test_context)
    await memory.save_tool_usage("Q3", "search_files", {}, test_context)
    
    # List tools
    tools = await memory.list_tools_with_memories(context=test_context)
    
    print(f"✓ Found {len(tools)} tools with memories")
    print(f"  Tools: {tools}")
    
    assert len(tools) == 3
    assert "run_sql" in tools
    assert "visualize_data" in tools
    assert "search_files" in tools
    assert tools == sorted(tools)  # Should be sorted


@pytest.mark.chromadb
@pytest.mark.asyncio
async def test_chromadb_clear_memories(temp_chroma_dir, test_context):
    """Test clearing memories."""
    from vanna.integrations.chromadb import ChromaAgentMemory
    
    print(f"\n=== Clear Memories Test ===")
    
    memory = ChromaAgentMemory(
        persist_directory=temp_chroma_dir,
        collection_name="test_memories"
    )
    
    # Save some patterns
    await memory.save_tool_usage("Q1", "run_sql", {}, test_context)
    await memory.save_tool_usage("Q2", "run_sql", {}, test_context)
    await memory.save_tool_usage("Q3", "visualize_data", {}, test_context)
    
    # Clear run_sql memories
    deleted = await memory.clear_memories(
        context=test_context,
        tool_name="run_sql"
    )
    
    print(f"✓ Cleared {deleted} run_sql memories")
    assert deleted == 2
    
    # Verify only visualize_data remains
    tools = await memory.list_tools_with_memories(context=test_context)
    print(f"  Remaining tools: {tools}")
    
    assert len(tools) == 1
    assert tools[0] == "visualize_data"


@pytest.mark.chromadb
@pytest.mark.asyncio
async def test_chromadb_persistence(temp_chroma_dir, test_context):
    """Test that memories persist across instances."""
    from vanna.integrations.chromadb import ChromaAgentMemory
    
    print(f"\n=== Persistence Test ===")
    
    # Create first instance and save
    memory1 = ChromaAgentMemory(
        persist_directory=temp_chroma_dir,
        collection_name="test_memories"
    )
    
    await memory1.save_tool_usage(
        question="Original question",
        tool_name="run_sql",
        args={"sql": "SELECT * FROM test"},
        context=test_context
    )
    
    print("✓ Saved memory with instance 1")
    
    # Create second instance (simulating restart)
    memory2 = ChromaAgentMemory(
        persist_directory=temp_chroma_dir,
        collection_name="test_memories"
    )
    
    # Search with new instance
    results = await memory2.search_similar_usage(
        question="Original question",
        context=test_context,
        similarity_threshold=0.8
    )
    
    print(f"✓ Instance 2 found {len(results)} persisted memories")
    
    assert len(results) > 0
    assert results[0].memory.question == "Original question"
    print("✓ Memory persisted across instances")
