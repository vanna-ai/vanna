"""
Azure AI Foundry integration for Vanna.

Provides an `LlmService` backed by Azure AI Foundry's inference endpoint
using the azure-ai-inference SDK.
"""

from .llm import AzureAIFoundryLlmService

__all__ = ["AzureAIFoundryLlmService"]
