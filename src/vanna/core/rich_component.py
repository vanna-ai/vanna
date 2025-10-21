"""
Base classes for rich UI components.

This module provides the base RichComponent class and supporting enums
for the component system.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, TypeVar

from pydantic import BaseModel, Field

# Type variable for self-returning methods
T = TypeVar('T', bound='RichComponent')


class ComponentType(str, Enum):
    """Types of rich UI components."""

    # Basic components
    TEXT = "text"
    CARD = "card"
    CONTAINER = "container"

    # Primitive UI components (domain-agnostic)
    STATUS_CARD = "status_card"
    PROGRESS_DISPLAY = "progress_display"
    LOG_VIEWER = "log_viewer"
    BADGE = "badge"
    ICON_TEXT = "icon_text"

    # Interactive components
    TASK_LIST = "task_list"
    PROGRESS_BAR = "progress_bar"
    BUTTON = "button"
    BUTTON_GROUP = "button_group"

    # Data components
    TABLE = "table"
    DATAFRAME = "dataframe"
    CHART = "chart"
    CODE_BLOCK = "code_block"

    # Status components
    STATUS_INDICATOR = "status_indicator"
    NOTIFICATION = "notification"
    ALERT = "alert"

    # Artifact components
    ARTIFACT = "artifact"

    # UI state components
    STATUS_BAR_UPDATE = "status_bar_update"
    TASK_TRACKER_UPDATE = "task_tracker_update"
    CHAT_INPUT_UPDATE = "chat_input_update"

    # Legacy (deprecated - use primitives instead)
    TOOL_EXECUTION = "tool_execution"


class ComponentLifecycle(str, Enum):
    """Component lifecycle operations."""

    CREATE = "create"
    UPDATE = "update"
    REPLACE = "replace"
    REMOVE = "remove"


class RichComponent(BaseModel):
    """Base class for all rich UI components."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ComponentType
    lifecycle: ComponentLifecycle = ComponentLifecycle.CREATE
    data: Dict[str, Any] = Field(default_factory=dict)
    children: List[str] = Field(default_factory=list)  # Child component IDs
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    visible: bool = True
    interactive: bool = False

    def update(self: T, **kwargs: Any) -> T:
        """Create an updated copy of this component."""
        updated_data = self.model_dump()
        updated_data.update(kwargs)
        updated_data["lifecycle"] = ComponentLifecycle.UPDATE
        updated_data["timestamp"] = datetime.utcnow().isoformat()
        return self.__class__(**updated_data)

    def hide(self: T) -> T:
        """Create a hidden copy of this component."""
        return self.update(visible=False)

    def show(self: T) -> T:
        """Create a visible copy of this component."""
        return self.update(visible=True)

    def serialize_for_frontend(self) -> Dict[str, Any]:
        """Normalize component payload for the frontend renderer.

        The frontend expects component-specific fields to live under the
        ``data`` key while the shared metadata (``id``, ``type``, layout hints,
        etc.) remains at the top level. Pydantic's ``model_dump`` keeps
        component attributes at the top level, so we remap them here before
        streaming them across the wire.
        """

        # Base fields that should remain at the top level of the payload.
        shared_fields = {
            "id",
            "type",
            "lifecycle",
            "children",
            "timestamp",
            "visible",
            "interactive",
        }

        raw = self.model_dump()
        payload: Dict[str, Any] = {}

        # Preserve any existing data payload so implementations can opt-in to
        # advanced usage without losing information.
        raw_data = raw.get("data")
        if raw_data is not None and isinstance(raw_data, dict):
            component_data: Dict[str, Any] = raw_data.copy()
        else:
            # Handle case where data might be a sequence or other type, or None
            component_data = {}

        for key, value in raw.items():
            if key in shared_fields:
                payload[key] = value
            elif key == "data":
                # For most components, skip the base data field
                continue
            elif key == "rows" and hasattr(self, 'type') and self.type.value == 'dataframe':
                # For DataFrame components, the 'rows' field contains the actual row data
                # which should be included in the component_data as 'data' for the frontend
                component_data["data"] = value
            else:
                component_data[key] = value

        payload["data"] = component_data

        # Ensure enums are serialized as primitive values for the frontend.
        payload["type"] = self.type.value
        payload["lifecycle"] = self.lifecycle.value

        return payload
