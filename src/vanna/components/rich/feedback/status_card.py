"""Status card component for displaying process status."""

from typing import Any, Dict, List, Optional
from pydantic import Field
from ....core.rich_component import RichComponent, ComponentType


class StatusCardComponent(RichComponent):
    """Generic status card that can display any process status."""

    type: ComponentType = ComponentType.STATUS_CARD
    title: str
    status: str  # "pending", "running", "completed", "failed", "success", "warning", "error"
    description: Optional[str] = None
    icon: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    collapsible: bool = False
    collapsed: bool = False

    def set_status(self, status: str, description: Optional[str] = None) -> "StatusCardComponent":
        """Update the status and optionally the description."""
        updates = {"status": status}
        if description is not None:
            updates["description"] = description
        return self.update(**updates)
