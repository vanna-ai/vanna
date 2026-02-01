"""
Test for ChromaDB persistence fix.

This test verifies that ChromaDB collections can be retrieved without triggering
unnecessary embedding function initialization/model downloads.
"""
import pytest
import tempfile
import shutil
import asyncio
from unittest.mock import MagicMock, patch

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
async def test_chromadb_collection_retrieval_without_embedding_function():
    """
    Test that existing ChromaDB collections can be retrieved without
    initializing the embedding function (avoiding model downloads).
    """
    try:
        import chromadb
        from chromadb.config import Settings
        from vanna.integrations.chromadb import ChromaAgentMemory
    except ImportError:
        pytest.skip("ChromaDB not installed")

    temp_dir = tempfile.mkdtemp()

    try:
        # Setup: Create a collection with some data (simulating previous session)
        client = chromadb.PersistentClient(
            path=temp_dir, settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )

        # Create collection without embedding function
        collection = client.create_collection("test_collection")

        # Add data with explicit embeddings (no embedding function needed)
        collection.add(
            ids=["mem1", "mem2"],
            documents=["memory 1", "memory 2"],
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

        # Clean up client completely to simulate app restart
        # Force clear the shared system cache
        del collection
        client_identifier = temp_dir
        from chromadb.api.shared_system_client import SharedSystemClient
        if client_identifier in SharedSystemClient._identifier_to_system:
            system = SharedSystemClient._identifier_to_system.pop(client_identifier)
            system.stop()
        del client

        # Test: Create ChromaAgentMemory and verify it retrieves the collection
        # WITHOUT calling _get_embedding_function for existing collections
        memory = ChromaAgentMemory(
            persist_directory=temp_dir, collection_name="test_collection"
        )

        # Mock the _get_embedding_function to ensure it's not called for retrieval
        original_get_ef = memory._get_embedding_function

        def mock_get_ef():
            # If this is called, it means we're trying to create a new collection
            # which should NOT happen when the collection already exists
            pytest.fail(
                "_get_embedding_function was called when retrieving existing collection"
            )

        memory._get_embedding_function = mock_get_ef

        # This should retrieve the existing collection without calling _get_embedding_function
        collection = memory._get_collection()

        # Restore original method for cleanup
        memory._get_embedding_function = original_get_ef

        # Verify collection was retrieved
        assert collection is not None
        assert collection.name == "test_collection"
        assert collection.count() == 2

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
