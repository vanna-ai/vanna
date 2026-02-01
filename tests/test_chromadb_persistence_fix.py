"""
Test for ChromaDB persistence fix.

This test verifies that ChromaDB collections can be retrieved without triggering
unnecessary embedding function initialization/model downloads.
"""
import pytest
import tempfile
import shutil
import asyncio

from vanna.integrations.chromadb import ChromaAgentMemory
from vanna.core.user import User
from vanna.core.tool import ToolContext


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
    """Helper to create test context."""
    return ToolContext(
        user=test_user,
        conversation_id="test_conv",
        request_id="test_req",
        agent_memory=agent_memory,
        metadata={},
    )


@pytest.mark.asyncio
async def test_chromadb_collection_retrieval_without_embedding_function(test_user):
    """
    Test that existing ChromaDB collections can be retrieved without
    initializing the embedding function (avoiding model downloads).
    
    This test simulates the real-world scenario where:
    1. A collection is created with an embedding function (first app run)
    2. The app restarts and retrieves the existing collection
    3. The embedding function should NOT be re-initialized on retrieval
    """
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError:
        pytest.skip("ChromaDB not installed")

    temp_dir = tempfile.mkdtemp()

    try:
        # Session 1: Create a collection using ChromaAgentMemory (simulating first app run)
        # This will create the collection with an embedding function
        memory1 = ChromaAgentMemory(
            persist_directory=temp_dir, collection_name="test_collection"
        )
        
        context = create_test_context(test_user, memory1)
        
        # Save some memories (this will create the collection)
        # We need to add explicit embeddings to avoid model download in test environment
        collection = memory1._get_collection()
        collection.add(
            ids=["mem1", "mem2"],
            documents=["test question 1", "test question 2"],
            embeddings=[[0.1] * 384, [0.2] * 384],
            metadatas=[
                {
                    "question": "test question 1",
                    "tool_name": "test_tool",
                    "args_json": "{}",
                    "timestamp": "2024-01-01T00:00:00",
                    "success": True,
                    "metadata_json": "{}",
                },
                {
                    "question": "test question 2",
                    "tool_name": "test_tool",
                    "args_json": "{}",
                    "timestamp": "2024-01-01T00:01:00",
                    "success": True,
                    "metadata_json": "{}",
                },
            ],
        )
        
        # Clean up references to simulate app restart
        del collection
        del memory1

        # Session 2: Create new ChromaAgentMemory instance (simulating app restart)
        # This should retrieve the existing collection WITHOUT calling _get_embedding_function
        memory2 = ChromaAgentMemory(
            persist_directory=temp_dir, collection_name="test_collection"
        )

        # Mock _get_embedding_function to verify it's not called
        original_get_ef = memory2._get_embedding_function

        def mock_get_ef():
            pytest.fail(
                "_get_embedding_function was called when retrieving existing collection"
            )

        memory2._get_embedding_function = mock_get_ef

        # This should retrieve the existing collection without calling _get_embedding_function
        collection2 = memory2._get_collection()

        # Restore original method
        memory2._get_embedding_function = original_get_ef

        # Verify collection was retrieved successfully
        assert collection2 is not None
        assert collection2.name == "test_collection"
        assert collection2.count() == 2
        
        # Test that we can use public API methods on the retrieved collection
        context2 = create_test_context(test_user, memory2)
        recent = await memory2.get_recent_memories(context=context2, limit=10)
        assert len(recent) == 2
        assert recent[0].question in ["test question 1", "test question 2"]

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_chromadb_collection_creation_with_embedding_function():
    """
    Test that NEW ChromaDB collections are created WITH the embedding function.
    """
    try:
        from vanna.integrations.chromadb import ChromaAgentMemory
    except ImportError:
        pytest.skip("ChromaDB not installed")

    temp_dir = tempfile.mkdtemp()

    try:
        # Test: Create ChromaAgentMemory for a non-existent collection
        memory = ChromaAgentMemory(
            persist_directory=temp_dir, collection_name="new_collection"
        )

        # Track if _get_embedding_function was called
        get_ef_called = []
        original_get_ef = memory._get_embedding_function

        def tracking_get_ef():
            get_ef_called.append(True)
            return original_get_ef()

        memory._get_embedding_function = tracking_get_ef

        # This should create a new collection and SHOULD call _get_embedding_function
        collection = memory._get_collection()

        # Restore original
        memory._get_embedding_function = original_get_ef

        # Verify collection was created
        assert collection is not None
        assert collection.name == "new_collection"

        # Verify _get_embedding_function was called
        assert get_ef_called, "_get_embedding_function should be called when creating new collection"

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_chromadb_collection_retrieval_without_embedding_function())
    asyncio.run(test_chromadb_collection_creation_with_embedding_function())
