"""
Tool domain.

This module provides the core abstractions for tools in the Vanna Agents framework.
"""

from .base import T, Tool
from .models import ToolCall, ToolContext, ToolResult, ToolSchema

__all__ = [
    "Tool",
    "T",
    "ToolCall",
    "ToolContext",
    "ToolResult",
    "ToolSchema",
]
