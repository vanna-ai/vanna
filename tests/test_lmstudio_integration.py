import os
import unittest

import pytest


def skip_if_no_lmstudio():
    """Helper to skip tests when LM Studio tests are disabled"""
    return pytest.mark.skipif(
        'SKIP_INTEGRATION_TESTS' in os.environ or not os.environ.get('RUN_LMSTUDIO_TESTS'),
        reason="Integration test skipped. Set RUN_LMSTUDIO_TESTS=1 to enable."
    )

@skip_if_no_lmstudio()
def test_lmstudio_with_chromadb():
    """
    This test demonstrates integrating LMStudio with ChromaDB.
    To run this test:
    1. Make sure LM Studio is running with a model loaded
    2. Set RUN_LMSTUDIO_TESTS=1 environment variable
    """
    try:
        from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
        from vanna.lmstudio.lmstudio import LMStudio

        # Define a combined class
        class MyVanna(ChromaDB_VectorStore, LMStudio):
            def __init__(self, config=None):
                ChromaDB_VectorStore.__init__(self, config=config)
                LMStudio.__init__(self, config=config)

        # Create an instance
        config = {
            'model': 'qwen2.5-coder-14b-instruct',  # Use your currently loaded model
            'options': {
                'temperature': 0.1,
                'max_tokens': 1024
            }
        }

        # Try to instantiate (this will verify the integration works)
        vn = MyVanna(config=config)

        # Test the methods from LMStudio
        system_msg = vn.system_message("I am a system message")
        user_msg = vn.user_message("I am a user message")

        # Verify the methods work as expected
        assert system_msg["role"] == "system"
        assert user_msg["role"] == "user"

        # Print success message
        print("\nLMStudio + ChromaDB integration successful!")
        print(f"Model: {vn.model}")
        print(f"Temperature: {vn.temperature}")

    except Exception as e:
        pytest.fail(f"Integration test failed: {str(e)}")

def test_manual_methods():
    """
    This test verifies the LMStudio methods directly without
    instantiating the class to avoid abstract method errors.
    """
    try:
        from vanna.lmstudio.lmstudio import LMStudio

        # Create instance methods on a dummy class for testing
        class DummyLMStudio(LMStudio):
            def __init__(self):
                pass

            # Add stub implementations for abstract methods
            def add_ddl(self, ddl, **kwargs): pass
            def add_documentation(self, documentation, **kwargs): pass
            def add_question_sql(self, question, sql, **kwargs): pass
            def generate_embedding(self, text, **kwargs): pass
            def get_related_ddl(self, question, **kwargs): pass
            def get_related_documentation(self, question, **kwargs): pass
            def get_similar_question_sql(self, question, **kwargs): pass
            def get_training_data(self, **kwargs): pass
            def remove_training_data(self, id, **kwargs): pass

        # Create instance for testing instance methods
        dummy = DummyLMStudio()

        # Test methods
        system_message = dummy.system_message("Test system message")
        assert system_message == {"role": "system", "content": "Test system message"}

        user_message = dummy.user_message("Test user message")
        assert user_message == {"role": "user", "content": "Test user message"}

        assistant_message = dummy.assistant_message("Test assistant message")
        assert assistant_message == {"role": "assistant", "content": "Test assistant message"}

        print("\nLMStudio method tests passed!")

    except Exception as e:
        pytest.fail(f"Method test failed: {str(e)}")

@skip_if_no_lmstudio()
def test_submit_prompt_and_sql_extraction():
    """Test submitting a prompt to LMStudio and extracting SQL."""
    try:
        from unittest.mock import MagicMock, patch

        from vanna.lmstudio.lmstudio import LMStudio

        # Mock the lmstudio client
        with patch('lmstudio.Client') as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = """
            Here's a SQL query:
            ```sql
            SELECT * FROM customers
            WHERE age > 30
            ```
            This will retrieve all customers older than 30.
            """

            # Configure the mock
            mock_instance = mock_client.return_value
            mock_instance.chat.completions.create.return_value = mock_response
            mock_instance.llm.list_loaded.return_value = []

            # Create LMStudio instance
            config = {
                'model': 'test-model',
                'options': {'temperature': 0.1, 'max_tokens': 100}
            }

            # Use DummyLMStudio to avoid abstract method errors
            class DummyLMStudio(LMStudio):
                def __init__(self, config):
                    super().__init__(config)

                # Add stub implementations for abstract methods
                def add_ddl(self, ddl, **kwargs): pass
                def add_documentation(self, documentation, **kwargs): pass
                def add_question_sql(self, question, sql, **kwargs): pass
                def generate_embedding(self, text, **kwargs): pass
                def get_related_ddl(self, question, **kwargs): pass
                def get_related_documentation(self, question, **kwargs): pass
                def get_similar_question_sql(self, question, **kwargs): pass
                def get_training_data(self, **kwargs): pass
                def remove_training_data(self, id, **kwargs): pass

            lmstudio = DummyLMStudio(config)

            # Test submitting a prompt
            prompt = [
                {"role": "system", "content": "You are an SQL assistant"},
                {"role": "user", "content": "List all customers over 30"}
            ]

            response = lmstudio.submit_prompt(prompt)

            # Verify response
            assert response is not None
            assert "sql" in response.lower()

            # Test SQL extraction
            extracted_sql = lmstudio.extract_sql(response)
            assert "SELECT * FROM customers" in extracted_sql
            assert "WHERE age > 30" in extracted_sql

            # Verify model loading was attempted
            mock_instance.llm.list_loaded.assert_called_once()

            print("\nLMStudio prompt submission and SQL extraction test passed!")

    except Exception as e:
        pytest.fail(f"Prompt submission test failed: {str(e)}")

@skip_if_no_lmstudio()
def test_model_loading():
    """Test model loading functionality."""
    try:
        from unittest.mock import MagicMock, patch

        from vanna.lmstudio.lmstudio import LMStudio

        # Mock the lmstudio client
        with patch('lmstudio.Client') as mock_client:
            mock_instance = mock_client.return_value

            # Test 1: Model already loaded
            mock_loaded_model = MagicMock()
            mock_loaded_model.key = 'test-model'
            mock_instance.llm.list_loaded.return_value = [mock_loaded_model]

            # Create and initialize LMStudio instance
            class DummyLMStudio(LMStudio):
                def __init__(self, config):
                    super().__init__(config)

                # Add stub implementations for abstract methods
                def add_ddl(self, ddl, **kwargs): pass
                def add_documentation(self, documentation, **kwargs): pass
                def add_question_sql(self, question, sql, **kwargs): pass
                def generate_embedding(self, text, **kwargs): pass
                def get_related_ddl(self, question, **kwargs): pass
                def get_related_documentation(self, question, **kwargs): pass
                def get_similar_question_sql(self, question, **kwargs): pass
                def get_training_data(self, **kwargs): pass
                def remove_training_data(self, id, **kwargs): pass

            config = {'model': 'test-model'}
            lmstudio = DummyLMStudio(config)

            # Verify model loading method called but not the actual loading
            mock_instance.llm.list_loaded.assert_called_once()
            mock_instance.llm.model.assert_not_called()

            # Test 2: Model not loaded
            mock_instance.llm.list_loaded.reset_mock()
            mock_instance.llm.list_loaded.return_value = []

            config = {'model': 'not-loaded-model'}
            lmstudio = DummyLMStudio(config)

            # Verify model loading was attempted
            mock_instance.llm.list_loaded.assert_called_once()
            mock_instance.llm.model.assert_called_once()

            print("\nLMStudio model loading test passed!")

    except Exception as e:
        pytest.fail(f"Model loading test failed: {str(e)}")

@skip_if_no_lmstudio()
def test_error_handling():
    """Test error handling in LMStudio implementation."""
    try:
        import importlib
        from unittest.mock import MagicMock, patch

        from vanna.lmstudio.lmstudio import LMStudio

        # Test 1: Missing dependency
        with patch.dict('sys.modules', {'lmstudio': None}):
            # Force reload to trigger ImportError
            importlib.reload(importlib.import_module('vanna.lmstudio.lmstudio'))

            # Create concrete implementation
            class ConcreteLMStudio(LMStudio):
                def add_ddl(self, ddl, **kwargs): pass
                def add_documentation(self, documentation, **kwargs): pass
                def add_question_sql(self, question, sql, **kwargs): pass
                def generate_embedding(self, text, **kwargs): pass
                def get_related_ddl(self, question, **kwargs): pass
                def get_related_documentation(self, question, **kwargs): pass
                def get_similar_question_sql(self, question, **kwargs): pass
                def get_training_data(self, **kwargs): pass
                def remove_training_data(self, id, **kwargs): pass

            # Attempt to create instance which should raise DependencyError
            from vanna.exceptions import DependencyError

            with pytest.raises(DependencyError):
                ConcreteLMStudio(config={'model': 'test-model'})

        # Create concrete implementation for the rest of the tests
        class ConcreteLMStudio(LMStudio):
            def add_ddl(self, ddl, **kwargs): pass
            def add_documentation(self, documentation, **kwargs): pass
            def add_question_sql(self, question, sql, **kwargs): pass
            def generate_embedding(self, text, **kwargs): pass
            def get_related_ddl(self, question, **kwargs): pass
            def get_related_documentation(self, question, **kwargs): pass
            def get_similar_question_sql(self, question, **kwargs): pass
            def get_training_data(self, **kwargs): pass
            def remove_training_data(self, id, **kwargs): pass

        # Test 2: Missing config
        with pytest.raises(ValueError):
            ConcreteLMStudio(config=None)

        # Test 3: Missing model in config
        with pytest.raises(ValueError):
            ConcreteLMStudio(config={})

        print("\nLMStudio error handling test passed!")

    except Exception as e:
        pytest.fail(f"Error handling test failed: {str(e)}")

@skip_if_no_lmstudio()
def test_end_to_end_with_mock():
    """Test end-to-end workflow using mocks."""
    try:
        from unittest.mock import MagicMock, patch

        from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
        from vanna.lmstudio.lmstudio import LMStudio

        # Setup mocks
        with patch('lmstudio.Client') as mock_client, \
             patch('chromadb.Client') as mock_chromadb:

            # Mock LMStudio response
            mock_lm_instance = mock_client.return_value
            mock_lm_instance.llm.list_loaded.return_value = []

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = """
            ```sql
            SELECT product_name, SUM(sales) AS total_sales
            FROM sales_data
            GROUP BY product_name
            ORDER BY total_sales DESC
            LIMIT 10
            ```
            """
            mock_lm_instance.chat.completions.create.return_value = mock_response

            # Mock ChromaDB
            mock_chromadb_instance = mock_chromadb.return_value
            mock_collection = MagicMock()
            mock_chromadb_instance.get_or_create_collection.return_value = mock_collection

            # Create combined class
            class MyVanna(ChromaDB_VectorStore, LMStudio):
                def __init__(self, config=None):
                    ChromaDB_VectorStore.__init__(self, config=config)
                    LMStudio.__init__(self, config=config)

                # Mock generate_embedding for this test
                def generate_embedding(self, text, **kwargs):
                    return [0.1] * 10

            # Create instance
            config = {
                'model': 'test-model',
                'options': {'temperature': 0.1}
            }
            vn = MyVanna(config=config)

            # Mock get_related methods to return empty
            vn.get_related_ddl = MagicMock(return_value=[])
            vn.get_related_documentation = MagicMock(return_value=[])
            vn.get_similar_question_sql = MagicMock(return_value=[])

            # Test generating SQL from a question
            question = "What are the top 10 products by sales?"
            sql = vn.generate_sql(question)

            # Verify we got SQL back
            assert "SELECT product_name" in sql
            assert "GROUP BY product_name" in sql
            assert "LIMIT 10" in sql

            print("\nLMStudio end-to-end workflow test passed!")

    except Exception as e:
        pytest.fail(f"End-to-end test failed: {str(e)}")

if __name__ == "__main__":
    # When run directly, execute the tests
    test_lmstudio_with_chromadb()
    test_manual_methods()
    test_submit_prompt_and_sql_extraction()
    test_model_loading()
    test_error_handling()
    test_end_to_end_with_mock()
