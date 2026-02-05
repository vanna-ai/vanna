"""
Exception classes for the Vanna Agents framework.

This module defines all custom exceptions used throughout the framework.
"""


class AgentError(Exception):
    """Base exception for agent framework."""

    pass


class ToolExecutionError(AgentError):
    """Error during tool execution."""

    pass


class ToolNotFoundError(AgentError):
    """Tool not found in registry."""

    pass


class PermissionError(AgentError):
    """User lacks required permissions."""

    pass


class ConversationNotFoundError(AgentError):
    """Conversation not found."""

    pass


class LlmServiceError(AgentError):
    """Error communicating with LLM service."""

    pass


class ValidationError(AgentError):
    """Data validation error."""

    pass
