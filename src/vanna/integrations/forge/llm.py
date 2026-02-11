"""
Forge LLM service implementation.

Forge is an OpenAI API compatible LLM router that provides unified access to
multiple AI providers through a single API. This service extends the OpenAI
implementation with Forge-specific defaults.

See https://github.com/TensorBlock/forge for details.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from vanna.integrations.openai.llm import OpenAILlmService


class ForgeLlmService(OpenAILlmService):
    """Forge-backed LLM service.

    Extends ``OpenAILlmService`` with Forge-specific defaults for base URL,
    API key, and model name. Forge uses the standard OpenAI API format so all
    streaming, tool-calling, and response handling from the parent class work
    unchanged.

    Args:
        model: Model name in ``Provider/model-name`` format
            (e.g., ``"OpenAI/gpt-4o"``). Falls back to env
            ``FORGE_MODEL`` then ``"OpenAI/gpt-4o-mini"``.
        api_key: Forge API key; falls back to env ``FORGE_API_KEY``.
        base_url: Optional custom base URL; falls back to env
            ``FORGE_API_BASE`` then ``"https://api.forge.tensorblock.co/v1"``.
        **extra_client_kwargs: Extra kwargs forwarded to ``openai.OpenAI()``.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **extra_client_kwargs: Any,
    ) -> None:
        api_key = api_key or os.getenv("FORGE_API_KEY")
        base_url = base_url or os.getenv(
            "FORGE_API_BASE", "https://api.forge.tensorblock.co/v1"
        )
        model = model or os.getenv("FORGE_MODEL", "OpenAI/gpt-4o-mini")

        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            **extra_client_kwargs,
        )
