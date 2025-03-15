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
