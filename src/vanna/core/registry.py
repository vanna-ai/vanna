"""
Tool registry for the Vanna Agents framework.

This module provides the ToolRegistry class for managing and executing tools.
"""

import time
from typing import Any, Dict, List, Optional

from .tool import Tool, ToolCall, ToolContext, ToolResult, ToolSchema
from .user import User


class ToolRegistry:
    """Registry for managing tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool[Any]] = {}

    def register(self, tool: Tool[Any]) -> None:
        """Register a tool."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool[Any]]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_schemas(self, user: Optional[User] = None) -> List[ToolSchema]:
        """Get schemas for all tools accessible to user."""
        schemas = []
        for tool in self._tools.values():
            if user is None or self._validate_tool_permissions(tool, user):
                schemas.append(tool.get_schema())
        return schemas

    def _validate_tool_permissions(self, tool: Tool[Any], user: User) -> bool:
        """Validate if user has permissions for tool."""
        required_permissions = tool.required_permissions
        if not required_permissions:
            return True

        user_permissions = set(user.permissions)
        required_permissions_set = set(required_permissions)
        return required_permissions_set.issubset(user_permissions)

    async def execute(
        self,
        tool_call: ToolCall,
        context: ToolContext,
    ) -> ToolResult:
        """Execute a tool call with validation."""
        tool = self.get_tool(tool_call.name)
        if not tool:
            msg = f"Tool '{tool_call.name}' not found"
            return ToolResult(
                success=False,
                result_for_llm=msg,
                ui_component=None,
                error=msg,
            )

        # Validate permissions
        if not self._validate_tool_permissions(tool, context.user):
            msg = f"Insufficient permissions for tool '{tool_call.name}'"
            return ToolResult(
                success=False,
                result_for_llm=msg,
                ui_component=None,
                error=msg,
            )

        # Validate and parse arguments
        try:
            args_model = tool.get_args_schema()
            validated_args = args_model.model_validate(tool_call.arguments)
        except Exception as e:
            msg = f"Invalid arguments: {str(e)}"
            return ToolResult(
                success=False,
                result_for_llm=msg,
                ui_component=None,
                error=msg,
            )

        # Execute tool with context-first signature
        try:
            start_time = time.perf_counter()
            result = await tool.execute(context, validated_args)
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # Add execution time to metadata
            result.metadata["execution_time_ms"] = execution_time_ms

            return result
        except Exception as e:
            msg = f"Execution failed: {str(e)}"
            return ToolResult(
                success=False,
                result_for_llm=msg,
                ui_component=None,
                error=msg,
            )
