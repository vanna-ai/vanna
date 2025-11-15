"""
Tool domain interface.

This module contains the abstract base class for tools.
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Type, TypeVar

from .models import ToolContext, ToolResult, ToolSchema

# Type variable for tool argument types
T = TypeVar("T")


class Tool(ABC, Generic[T]):
    """Abstract base class for tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this tool does."""
        pass

    @property
    def access_groups(self) -> List[str]:
        """Groups permitted to access this tool."""
        return []

    @abstractmethod
    def get_args_schema(self) -> Type[T]:
        """Return the Pydantic model for arguments."""
        pass

    @abstractmethod
    async def execute(self, context: ToolContext, args: T) -> ToolResult:
        """Execute the tool with validated arguments.

        Args:
            context: Execution context containing user, conversation_id, and request_id
            args: Validated tool arguments

        Returns:
            ToolResult with success status, result for LLM, and optional UI component
        """
        pass

    def get_schema(self) -> ToolSchema:
        """Generate tool schema for LLM."""
        from typing import Any, cast

        args_model = self.get_args_schema()
        # Get the schema - args_model should be a Pydantic model class
        schema = (
            cast(Any, args_model).model_json_schema()
            if hasattr(args_model, "model_json_schema")
            else {}
        )
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=schema,
            access_groups=self.access_groups,
        )
