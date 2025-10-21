"""
Workflow trigger system for deterministic workflow execution.

This module provides the WorkflowTrigger interface for intercepting user messages
and executing deterministic workflows before they reach the LLM. This is useful
for command handling, pattern-based routing, and state-based workflows.
"""

from .base import WorkflowTrigger, TriggerResult

__all__ = ["WorkflowTrigger", "TriggerResult"]
