"""
ModelsLab LLM service implementation.

This module provides an implementation of the LlmService interface backed by
ModelsLab's OpenAI-compatible uncensored chat API.  Because ModelsLab's
``/uncensored-chat/v1`` endpoint is 100% compatible with the OpenAI Chat
Completions API, this class is a thin wrapper around
:class:`vanna.integrations.openai.OpenAILlmService` that pre-configures the
correct base URL and environment-variable name.

Supported models
----------------
- ``llama-3.1-8b-uncensored``  (128 K context, **default**)
- ``llama-3.1-70b-uncensored`` (128 K context)

Quick start
-----------
.. code-block:: python

    import vanna
    from vanna.integrations.modelslab import ModelsLabLlmService

    vn = vanna.create_client(
        llm=ModelsLabLlmService(
            model="llama-3.1-70b-uncensored",
            api_key="YOUR_MODELSLAB_API_KEY",  # or set MODELSLAB_API_KEY env var
        ),
        # ... vector store, SQL connection, etc.
    )

    sql = await vn.generate_sql("Show me total revenue by month for 2024")
    print(sql)

Configuration
-------------
The following environment variables are recognised:

- ``MODELSLAB_API_KEY``   — API key (required when ``api_key`` is not passed).
- ``MODELSLAB_MODEL``     — Model override (optional).
- ``MODELSLAB_BASE_URL``  — Base URL override (optional).

Get an API key at https://modelslab.com/api-keys
Full API docs: https://docs.modelslab.com
"""

from __future__ import annotations

import os
from typing import Any, Optional

from vanna.integrations.openai import OpenAILlmService

MODELSLAB_BASE_URL = "https://modelslab.com/api/uncensored-chat/v1"
MODELSLAB_DEFAULT_MODEL = "llama-3.1-8b-uncensored"


class ModelsLabLlmService(OpenAILlmService):
    """ModelsLab-backed LLM service for Vanna.

    Wraps :class:`OpenAILlmService` with ModelsLab's uncensored-chat endpoint
    pre-configured.  All streaming, tool-calling, and structured-output
    features inherited from :class:`OpenAILlmService` work without changes.

    Args:
        model: ModelsLab model identifier.  Defaults to the value of
            ``MODELSLAB_MODEL`` env var, or ``"llama-3.1-8b-uncensored"``.
        api_key: ModelsLab API key.  Falls back to ``MODELSLAB_API_KEY``
            env var.
        base_url: Override the ModelsLab endpoint URL.  Falls back to
            ``MODELSLAB_BASE_URL`` env var.
        **extra_client_kwargs: Extra keyword arguments forwarded to the
            underlying :class:`openai.OpenAI` client.

    Raises:
        ValueError: When no API key is found in either the argument or the
            environment.

    Example::

        from vanna.integrations.modelslab import ModelsLabLlmService

        llm = ModelsLabLlmService(
            model="llama-3.1-70b-uncensored",
            api_key="YOUR_API_KEY",
        )
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **extra_client_kwargs: Any,
    ) -> None:
        resolved_api_key = api_key or os.getenv("MODELSLAB_API_KEY")
        if not resolved_api_key:
            raise ValueError(
                "ModelsLab API key is required.  Pass it via the `api_key` "
                "argument or set the MODELSLAB_API_KEY environment variable.  "
                "Get your key at https://modelslab.com/api-keys"
            )

        resolved_model = (
            model
            or os.getenv("MODELSLAB_MODEL")
            or MODELSLAB_DEFAULT_MODEL
        )
        resolved_base_url = (
            base_url
            or os.getenv("MODELSLAB_BASE_URL")
            or MODELSLAB_BASE_URL
        )

        super().__init__(
            model=resolved_model,
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            **extra_client_kwargs,
        )
