"""
UI component base class.

This module defines the UiComponent class which is the return type for tool executions.
It's placed in core/ because it's a fundamental type that tools return, not just a UI concern.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class UiComponent(BaseModel):
    """Base class for UI components streamed to client.

    This wraps both rich and simple component representations,
    allowing tools to return structured UI updates.

    Note: We use Any for component types to avoid circular dependencies.
    Type validation happens at runtime through validators.
    """

    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    rich_component: Any = Field(..., description="Rich component for advanced rendering")
    simple_component: Optional[Any] = Field(None, description="Simple component for basic rendering")

    @model_validator(mode='after')
    def validate_components(self) -> 'UiComponent':
        """Validate that components are the correct types at runtime."""
        # Import from core - clean imports, no circular dependency
        from .rich_component import RichComponent
        from .simple_component import SimpleComponent

        if not isinstance(self.rich_component, RichComponent):
            raise ValueError(f"rich_component must be a RichComponent, got {type(self.rich_component)}")

        if self.simple_component is not None and not isinstance(self.simple_component, SimpleComponent):
            raise ValueError(f"simple_component must be a SimpleComponent or None, got {type(self.simple_component)}")

        return self

    model_config = {
        'arbitrary_types_allowed': True
    }
