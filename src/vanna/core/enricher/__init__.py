"""
Context enrichment system for adding data to tool execution context.

This module provides interfaces for enriching ToolContext with additional
data before tool execution.
"""

from .base import ToolContextEnricher

__all__ = ["ToolContextEnricher"]
