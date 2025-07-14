
from typing import Any, Dict, Optional
from ..base import VannaBase


class MockLLM(VannaBase):
    """
    A mock implementation of an LLM for testing and demonstration purposes.
    Returns canned responses and does not require any external API keys or services.
    """
    def __init__(self, config: Optional[dict] = None) -> None:
        """
        Initialize the mock LLM. Config is ignored.
        """
        pass

    def system_message(self, message: str) -> Dict[str, str]:
        """
        Create a mock system message.
        Args:
            message (str): The system message content.
        Returns:
            dict: A dictionary representing the system message.
        """
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> Dict[str, str]:
        """
        Create a mock user message.
        Args:
            message (str): The user message content.
        Returns:
            dict: A dictionary representing the user message.
        """
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> Dict[str, str]:
        """
        Create a mock assistant message.
        Args:
            message (str): The assistant message content.
        Returns:
            dict: A dictionary representing the assistant message.
        """
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt: str, **kwargs: Any) -> str:
        """
        Return a canned response for any prompt.
        Args:
            prompt (str): The prompt to submit.
            **kwargs: Additional keyword arguments (ignored).
        Returns:
            str: A mock LLM response string.
        """
        return "Mock LLM response"
