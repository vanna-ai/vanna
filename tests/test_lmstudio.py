import os
import unittest
from unittest.mock import MagicMock, patch

from vanna.lmstudio.lmstudio import LMStudio


class TestLMStudio(unittest.TestCase):

    @patch("builtins.__import__")
    def test_initialization(self, mock_import):
        # Setup the mock LMStudio client
        mock_lmstudio = MagicMock()
        mock_lmstudio_client = MagicMock()
        mock_lmstudio.Client.return_value = mock_lmstudio_client
        mock_import.return_value = mock_lmstudio

        # Test initialization with minimal config
        config = {"model": "test-model"}
        lmstudio = LMStudio(config=config)

        # Verify the client was initialized with correct parameters
        self.assertEqual(lmstudio.model, "test-model")
        self.assertEqual(lmstudio.host, "http://localhost:1234/v1")
        self.assertEqual(lmstudio.lmstudio_timeout, 240.0)
        self.assertEqual(lmstudio.temperature, 0.1)
        self.assertEqual(lmstudio.max_tokens, 4096)

        # Verify the model load check was called
        mock_lmstudio_client.llm.list_loaded.assert_called_once()

    @patch("builtins.__import__")
    def test_message_formatting(self, mock_import):
        # Setup the mock
        mock_lmstudio = MagicMock()
        mock_import.return_value = mock_lmstudio

        # Create an instance
        config = {"model": "test-model"}
        lmstudio = LMStudio(config=config)

        # Test message formatting methods
        system_msg = lmstudio.system_message("I am a system message")
        user_msg = lmstudio.user_message("I am a user message")
        assistant_msg = lmstudio.assistant_message("I am an assistant message")

        # Verify the message formats
        self.assertEqual(system_msg, {"role": "system", "content": "I am a system message"})
        self.assertEqual(user_msg, {"role": "user", "content": "I am a user message"})
        self.assertEqual(assistant_msg, {"role": "assistant", "content": "I am an assistant message"})

    @patch("builtins.__import__")
    def test_extract_sql(self, mock_import):
        # Setup the mock
        mock_lmstudio = MagicMock()
        mock_import.return_value = mock_lmstudio

        # Create an instance
        config = {"model": "test-model"}
        lmstudio = LMStudio(config=config)

        # Test SQL extraction with code block format
        sql_response = "Here is your SQL query:\n```sql\nSELECT * FROM users\n```"
        extracted_sql = lmstudio.extract_sql(sql_response)
        self.assertEqual(extracted_sql, "\nSELECT * FROM users\n")

        # Test SQL extraction with direct SELECT statement
        sql_response = "SELECT * FROM users WHERE age > 30"
        extracted_sql = lmstudio.extract_sql(sql_response)
        self.assertEqual(extracted_sql, "SELECT * FROM users WHERE age > 30")

        # Test SQL extraction with WITH statement
        sql_response = "with active_users as (SELECT * FROM users WHERE status = 'active') SELECT * FROM active_users"
        extracted_sql = lmstudio.extract_sql(sql_response)
        self.assertEqual(extracted_sql, "with active_users as (SELECT * FROM users WHERE status = 'active') SELECT * FROM active_users")

    @patch("builtins.__import__")
    def test_submit_prompt(self, mock_import):
        # Setup the mock LMStudio client
        mock_lmstudio = MagicMock()
        mock_lmstudio_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()

        # Setup the response structure
        mock_message.content = "This is the LLM response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        # Link the mocks
        mock_lmstudio_client.chat.completions.create.return_value = mock_response
        mock_lmstudio.Client.return_value = mock_lmstudio_client
        mock_import.return_value = mock_lmstudio

        # Create an instance
        config = {"model": "test-model"}
        lmstudio = LMStudio(config=config)

        # Test the submit_prompt method
        prompt = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write SQL to find all users."}
        ]

        result = lmstudio.submit_prompt(prompt)

        # Verify the client was called with correct parameters
        mock_lmstudio_client.chat.completions.create.assert_called_once_with(
            model="test-model",
            messages=prompt,
            temperature=0.1,
            max_tokens=4096
        )

        # Verify the response was correctly processed
        self.assertEqual(result, "This is the LLM response")


if __name__ == "__main__":
    unittest.main()
