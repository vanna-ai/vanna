"""Base classes for simple UI components."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum


class SimpleComponentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    LINK = "link"


class SimpleComponent(BaseModel):
    """A simple UI component with basic attributes."""

    type: SimpleComponentType = Field(..., description="Type of the component.")
    semantic_type: Optional[str] = Field(default=None, description="Semantic type for better categorization.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata for the component.")

    def serialize_for_frontend(self) -> Dict[str, Any]:
        """Serialize simple component for API consumption."""
        return self.model_dump()
