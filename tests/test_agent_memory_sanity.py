"""
Sanity tests for AgentMemory implementations.

These tests verify that:
1. Each AgentMemory implementation correctly implements the AgentMemory interface
2. Imports are working correctly for all vector store modules
3. Basic class instantiation works (without requiring actual service connections)

Note: These tests do NOT execute actual vector operations against services.
They are lightweight sanity checks for the implementation structure.
"""

import pytest
from inspect import signature, iscoroutinefunction
from abc import ABC


class TestAgentMemoryInterface:
    """Test that the AgentMemory interface is properly defined."""

    def test_agent_memory_import(self):
        """Test that AgentMemory can be imported."""
        from vanna.capabilities.agent_memory import AgentMemory
        assert AgentMemory is not None

    def test_agent_memory_is_abstract(self):
        """Test that AgentMemory is an abstract base class."""
        from vanna.capabilities.agent_memory import AgentMemory

        assert issubclass(AgentMemory, ABC)

    def test_agent_memory_has_required_methods(self):
        """Test that AgentMemory defines all required abstract methods."""
        from vanna.capabilities.agent_memory import AgentMemory

        required_methods = [
            'save_tool_usage',
            'search_similar_usage',
            'get_recent_memories',
            'delete_by_id',
            'clear_memories'
        ]

        for method_name in required_methods:
            assert hasattr(AgentMemory, method_name)
            method = getattr(AgentMemory, method_name)
            assert getattr(method, '__isabstractmethod__', False), f"{method_name} should be abstract"

    def test_all_methods_are_async(self):
        """Test that all AgentMemory methods are async."""
        from vanna.capabilities.agent_memory import AgentMemory

        methods = [
            'save_tool_usage',
            'search_similar_usage',
            'get_recent_memories',
            'delete_by_id',
            'clear_memories'
        ]

        for method_name in methods:
            method = getattr(AgentMemory, method_name)
            assert iscoroutinefunction(method), f"{method_name} should be async"


class TestToolMemoryModel:
    """Test the ToolMemory model."""

    def test_tool_memory_import(self):
        """Test that ToolMemory can be imported."""
        from vanna.capabilities.agent_memory import ToolMemory
        assert ToolMemory is not None

    def test_tool_memory_is_pydantic_model(self):
        """Test that ToolMemory is a Pydantic model."""
        from vanna.capabilities.agent_memory import ToolMemory
        from pydantic import BaseModel

        assert issubclass(ToolMemory, BaseModel)

    def test_tool_memory_has_required_fields(self):
        """Test that ToolMemory has all required fields."""
        from vanna.capabilities.agent_memory import ToolMemory

        required_fields = ['question', 'tool_name', 'args']
        optional_fields = ['memory_id', 'timestamp', 'success', 'metadata']

        model_fields = list(ToolMemory.model_fields.keys())

        for field in required_fields:
            assert field in model_fields, f"Required field '{field}' missing"

        for field in optional_fields:
            assert field in model_fields, f"Optional field '{field}' missing"

    def test_tool_memory_instantiation(self):
        """Test that ToolMemory can be instantiated."""
        from vanna.capabilities.agent_memory import ToolMemory

        memory = ToolMemory(
            memory_id="test-123",
            question="What is the total sales?",
            tool_name="run_sql",
            args={"sql": "SELECT SUM(amount) FROM sales"}
        )

        assert memory.memory_id == "test-123"
        assert memory.question == "What is the total sales?"
        assert memory.tool_name == "run_sql"
        assert memory.args == {"sql": "SELECT SUM(amount) FROM sales"}
        assert memory.success is True  # Default value


class TestMemorySearchResultModel:
    """Test the MemorySearchResult model."""

    def test_memory_search_result_import(self):
        """Test that MemorySearchResult can be imported."""
        from vanna.capabilities.agent_memory import MemorySearchResult
        assert MemorySearchResult is not None

    def test_memory_search_result_instantiation(self):
        """Test that MemorySearchResult can be instantiated."""
        from vanna.capabilities.agent_memory import MemorySearchResult, ToolMemory

        memory = ToolMemory(
            question="test",
            tool_name="test_tool",
            args={}
        )

        result = MemorySearchResult(
            memory=memory,
            similarity_score=0.95,
            rank=1
        )

        assert result.memory == memory
        assert result.similarity_score == 0.95
        assert result.rank == 1


class TestChromaDBAgentMemory:
    """Sanity tests for ChromaDB AgentMemory implementation."""

    def test_chromadb_import(self):
        """Test that ChromaAgentMemory can be imported."""
        try:
            from vanna.integrations.chromadb import ChromaAgentMemory
            assert ChromaAgentMemory is not None
        except ImportError:
            pytest.skip("ChromaDB not installed")

    def test_chromadb_implements_agent_memory(self):
        """Test that ChromaAgentMemory implements AgentMemory."""
        try:
            from vanna.integrations.chromadb import ChromaAgentMemory
            from vanna.capabilities.agent_memory import AgentMemory

            assert issubclass(ChromaAgentMemory, AgentMemory)
        except ImportError:
            pytest.skip("ChromaDB not installed")

    def test_chromadb_has_all_methods(self):
        """Test that ChromaAgentMemory implements all required methods."""
        try:
            from vanna.integrations.chromadb import ChromaAgentMemory

            required_methods = [
                'save_tool_usage',
                'search_similar_usage',
                'get_recent_memories',
                'delete_by_id',
                'clear_memories'
            ]

            for method_name in required_methods:
                assert hasattr(ChromaAgentMemory, method_name)
                method = getattr(ChromaAgentMemory, method_name)
                assert not getattr(method, '__isabstractmethod__', False), \
                    f"{method_name} should be implemented (not abstract)"
        except ImportError:
            pytest.skip("ChromaDB not installed")

    def test_chromadb_instantiation(self):
        """Test that ChromaAgentMemory can be instantiated."""
        try:
            from vanna.integrations.chromadb import ChromaAgentMemory
            import tempfile

            temp_dir = tempfile.mkdtemp()
            memory = ChromaAgentMemory(
                persist_directory=temp_dir,
                collection_name="test"
            )

            assert memory is not None
            assert memory.persist_directory == temp_dir
            assert memory.collection_name == "test"
        except ImportError:
            pytest.skip("ChromaDB not installed")


class TestQdrantAgentMemory:
    """Sanity tests for Qdrant AgentMemory implementation."""

    def test_qdrant_import(self):
        """Test that QdrantAgentMemory can be imported."""
        try:
            from vanna.integrations.qdrant import QdrantAgentMemory
            assert QdrantAgentMemory is not None
        except ImportError:
            pytest.skip("Qdrant not installed")

    def test_qdrant_implements_agent_memory(self):
        """Test that QdrantAgentMemory implements AgentMemory."""
        try:
            from vanna.integrations.qdrant import QdrantAgentMemory
            from vanna.capabilities.agent_memory import AgentMemory

            assert issubclass(QdrantAgentMemory, AgentMemory)
        except ImportError:
            pytest.skip("Qdrant not installed")

    def test_qdrant_has_all_methods(self):
        """Test that QdrantAgentMemory implements all required methods."""
        try:
            from vanna.integrations.qdrant import QdrantAgentMemory

            required_methods = [
                'save_tool_usage',
                'search_similar_usage',
                'get_recent_memories',
                'delete_by_id',
                'clear_memories'
            ]

            for method_name in required_methods:
                assert hasattr(QdrantAgentMemory, method_name)
        except ImportError:
            pytest.skip("Qdrant not installed")

    def test_qdrant_instantiation(self):
        """Test that QdrantAgentMemory can be instantiated."""
        try:
            from vanna.integrations.qdrant import QdrantAgentMemory

            # In-memory mode doesn't require actual service
            memory = QdrantAgentMemory(path=":memory:")

            assert memory is not None
        except ImportError:
            pytest.skip("Qdrant not installed")


class TestPineconeAgentMemory:
    """Sanity tests for Pinecone AgentMemory implementation."""

    def test_pinecone_import(self):
        """Test that PineconeAgentMemory can be imported."""
        try:
            from vanna.integrations.pinecone import PineconeAgentMemory
            assert PineconeAgentMemory is not None
        except ImportError:
            pytest.skip("Pinecone not installed")

    def test_pinecone_implements_agent_memory(self):
        """Test that PineconeAgentMemory implements AgentMemory."""
        try:
            from vanna.integrations.pinecone import PineconeAgentMemory
            from vanna.capabilities.agent_memory import AgentMemory

            assert issubclass(PineconeAgentMemory, AgentMemory)
        except ImportError:
            pytest.skip("Pinecone not installed")

    def test_pinecone_has_all_methods(self):
        """Test that PineconeAgentMemory implements all required methods."""
        try:
            from vanna.integrations.pinecone import PineconeAgentMemory

            required_methods = [
                'save_tool_usage',
                'search_similar_usage',
                'get_recent_memories',
                'delete_by_id',
                'clear_memories'
            ]

            for method_name in required_methods:
                assert hasattr(PineconeAgentMemory, method_name)
        except ImportError:
            pytest.skip("Pinecone not installed")


class TestMilvusAgentMemory:
    """Sanity tests for Milvus AgentMemory implementation."""

    def test_milvus_import(self):
        """Test that MilvusAgentMemory can be imported."""
        try:
            from vanna.integrations.milvus import MilvusAgentMemory
            assert MilvusAgentMemory is not None
        except ImportError:
            pytest.skip("Milvus not installed")

    def test_milvus_implements_agent_memory(self):
        """Test that MilvusAgentMemory implements AgentMemory."""
        try:
            from vanna.integrations.milvus import MilvusAgentMemory
            from vanna.capabilities.agent_memory import AgentMemory

            assert issubclass(MilvusAgentMemory, AgentMemory)
        except ImportError:
            pytest.skip("Milvus not installed")

    def test_milvus_has_all_methods(self):
        """Test that MilvusAgentMemory implements all required methods."""
        try:
            from vanna.integrations.milvus import MilvusAgentMemory

            required_methods = [
                'save_tool_usage',
                'search_similar_usage',
                'get_recent_memories',
                'delete_by_id',
                'clear_memories'
            ]

            for method_name in required_methods:
                assert hasattr(MilvusAgentMemory, method_name)
        except ImportError:
            pytest.skip("Milvus not installed")


class TestWeaviateAgentMemory:
    """Sanity tests for Weaviate AgentMemory implementation."""

    def test_weaviate_import(self):
        """Test that WeaviateAgentMemory can be imported."""
        try:
            from vanna.integrations.weaviate import WeaviateAgentMemory
            assert WeaviateAgentMemory is not None
        except ImportError:
            pytest.skip("Weaviate not installed")

    def test_weaviate_implements_agent_memory(self):
        """Test that WeaviateAgentMemory implements AgentMemory."""
        try:
            from vanna.integrations.weaviate import WeaviateAgentMemory
            from vanna.capabilities.agent_memory import AgentMemory

            assert issubclass(WeaviateAgentMemory, AgentMemory)
        except ImportError:
            pytest.skip("Weaviate not installed")

    def test_weaviate_has_all_methods(self):
        """Test that WeaviateAgentMemory implements all required methods."""
        try:
            from vanna.integrations.weaviate import WeaviateAgentMemory

            required_methods = [
                'save_tool_usage',
                'search_similar_usage',
                'get_recent_memories',
                'delete_by_id',
                'clear_memories'
            ]

            for method_name in required_methods:
                assert hasattr(WeaviateAgentMemory, method_name)
        except ImportError:
            pytest.skip("Weaviate not installed")


class TestFAISSAgentMemory:
    """Sanity tests for FAISS AgentMemory implementation."""

    def test_faiss_import(self):
        """Test that FAISSAgentMemory can be imported."""
        try:
            from vanna.integrations.faiss import FAISSAgentMemory
            assert FAISSAgentMemory is not None
        except ImportError:
            pytest.skip("FAISS not installed")

    def test_faiss_implements_agent_memory(self):
        """Test that FAISSAgentMemory implements AgentMemory."""
        try:
            from vanna.integrations.faiss import FAISSAgentMemory
            from vanna.capabilities.agent_memory import AgentMemory

            assert issubclass(FAISSAgentMemory, AgentMemory)
        except ImportError:
            pytest.skip("FAISS not installed")

    def test_faiss_has_all_methods(self):
        """Test that FAISSAgentMemory implements all required methods."""
        try:
            from vanna.integrations.faiss import FAISSAgentMemory

            required_methods = [
                'save_tool_usage',
                'search_similar_usage',
                'get_recent_memories',
                'delete_by_id',
                'clear_memories'
            ]

            for method_name in required_methods:
                assert hasattr(FAISSAgentMemory, method_name)
        except ImportError:
            pytest.skip("FAISS not installed")

    def test_faiss_instantiation(self):
        """Test that FAISSAgentMemory can be instantiated."""
        try:
            from vanna.integrations.faiss import FAISSAgentMemory
            import tempfile

            temp_dir = tempfile.mkdtemp()
            memory = FAISSAgentMemory(persist_path=temp_dir)

            assert memory is not None
            assert memory.persist_path == temp_dir
        except ImportError:
            pytest.skip("FAISS not installed")


class TestOpenSearchAgentMemory:
    """Sanity tests for OpenSearch AgentMemory implementation."""

    def test_opensearch_import(self):
        """Test that OpenSearchAgentMemory can be imported."""
        try:
            from vanna.integrations.opensearch import OpenSearchAgentMemory
            assert OpenSearchAgentMemory is not None
        except ImportError:
            pytest.skip("OpenSearch not installed")

    def test_opensearch_implements_agent_memory(self):
        """Test that OpenSearchAgentMemory implements AgentMemory."""
        try:
            from vanna.integrations.opensearch import OpenSearchAgentMemory
            from vanna.capabilities.agent_memory import AgentMemory

            assert issubclass(OpenSearchAgentMemory, AgentMemory)
        except ImportError:
            pytest.skip("OpenSearch not installed")

    def test_opensearch_has_all_methods(self):
        """Test that OpenSearchAgentMemory implements all required methods."""
        try:
            from vanna.integrations.opensearch import OpenSearchAgentMemory

            required_methods = [
                'save_tool_usage',
                'search_similar_usage',
                'get_recent_memories',
                'delete_by_id',
                'clear_memories'
            ]

            for method_name in required_methods:
                assert hasattr(OpenSearchAgentMemory, method_name)
        except ImportError:
            pytest.skip("OpenSearch not installed")


class TestAzureAISearchAgentMemory:
    """Sanity tests for Azure AI Search AgentMemory implementation."""

    def test_azuresearch_import(self):
        """Test that AzureAISearchAgentMemory can be imported."""
        try:
            from vanna.integrations.azuresearch import AzureAISearchAgentMemory
            assert AzureAISearchAgentMemory is not None
        except ImportError:
            pytest.skip("Azure Search not installed")

    def test_azuresearch_implements_agent_memory(self):
        """Test that AzureAISearchAgentMemory implements AgentMemory."""
        try:
            from vanna.integrations.azuresearch import AzureAISearchAgentMemory
            from vanna.capabilities.agent_memory import AgentMemory

            assert issubclass(AzureAISearchAgentMemory, AgentMemory)
        except ImportError:
            pytest.skip("Azure Search not installed")

    def test_azuresearch_has_all_methods(self):
        """Test that AzureAISearchAgentMemory implements all required methods."""
        try:
            from vanna.integrations.azuresearch import AzureAISearchAgentMemory

            required_methods = [
                'save_tool_usage',
                'search_similar_usage',
                'get_recent_memories',
                'delete_by_id',
                'clear_memories'
            ]

            for method_name in required_methods:
                assert hasattr(AzureAISearchAgentMemory, method_name)
        except ImportError:
            pytest.skip("Azure Search not installed")


class TestMarqoAgentMemory:
    """Sanity tests for Marqo AgentMemory implementation."""

    def test_marqo_import(self):
        """Test that MarqoAgentMemory can be imported."""
        try:
            from vanna.integrations.marqo import MarqoAgentMemory
            assert MarqoAgentMemory is not None
        except ImportError:
            pytest.skip("Marqo not installed")

    def test_marqo_implements_agent_memory(self):
        """Test that MarqoAgentMemory implements AgentMemory."""
        try:
            from vanna.integrations.marqo import MarqoAgentMemory
            from vanna.capabilities.agent_memory import AgentMemory

            assert issubclass(MarqoAgentMemory, AgentMemory)
        except ImportError:
            pytest.skip("Marqo not installed")

    def test_marqo_has_all_methods(self):
        """Test that MarqoAgentMemory implements all required methods."""
        try:
            from vanna.integrations.marqo import MarqoAgentMemory

            required_methods = [
                'save_tool_usage',
                'search_similar_usage',
                'get_recent_memories',
                'delete_by_id',
                'clear_memories'
            ]

            for method_name in required_methods:
                assert hasattr(MarqoAgentMemory, method_name)
        except ImportError:
            pytest.skip("Marqo not installed")


class TestDemoAgentMemory:
    """Sanity tests for DemoAgentMemory (in-memory) implementation."""

    def test_demo_import(self):
        """Test that DemoAgentMemory can be imported."""
        from vanna.integrations.local.agent_memory import DemoAgentMemory
        assert DemoAgentMemory is not None

    def test_demo_implements_agent_memory(self):
        """Test that DemoAgentMemory implements AgentMemory."""
        from vanna.integrations.local.agent_memory import DemoAgentMemory
        from vanna.capabilities.agent_memory import AgentMemory

        assert issubclass(DemoAgentMemory, AgentMemory)

    def test_demo_has_all_methods(self):
        """Test that DemoAgentMemory implements all required methods."""
        from vanna.integrations.local.agent_memory import DemoAgentMemory

        required_methods = [
            'save_tool_usage',
            'search_similar_usage',
            'get_recent_memories',
            'delete_by_id',
            'clear_memories'
        ]

        for method_name in required_methods:
            assert hasattr(DemoAgentMemory, method_name)

    def test_demo_instantiation(self):
        """Test that DemoAgentMemory can be instantiated."""
        from vanna.integrations.local.agent_memory import DemoAgentMemory

        memory = DemoAgentMemory(max_items=100)

        assert memory is not None
        assert memory._max_items == 100
