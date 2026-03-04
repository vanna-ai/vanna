"""
Groq LLM service implementation.

This module provides an implementation of the LlmService interface backed by
Groq's Chat Completions API. It uses the OpenAI SDK since Groq provides an
OpenAI-compatible endpoint.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from vanna.integrations.openai.llm import OpenAILlmService

class GroqLlmService(OpenAILlmService):
    """Groq Chat Completions-backed LLM service.

    Since Groq's API is OpenAI-compatible, this class inherits from OpenAILlmService
    and simply overrides the default base_url and model parameters.

    Args:
        model: Groq model name (e.g., "llama3-8b-8192", "mixtral-8x7b-32768").
        api_key: API key; falls back to env `GROQ_API_KEY`.
        base_url: Optional custom base URL; defaults to "https://api.groq.com/openai/v1".
        **extra_client_kwargs: Extra kwargs forwarded to `openai.OpenAI()`.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **extra_client_kwargs: Any,
    ) -> None:
        # Default Groq settings
        groq_model = model or os.getenv("GROQ_MODEL", "llama3-8b-8192")
        groq_api_key = api_key or os.getenv("GROQ_API_KEY")
        groq_base_url = base_url or os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

        if not groq_api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable or api_key parameter is required."
            )

        # Initialize the underlying OpenAI client with Groq's configuration
        super().__init__(
            model=groq_model,
            api_key=groq_api_key,
            base_url=groq_base_url,
            **extra_client_kwargs,
        )
