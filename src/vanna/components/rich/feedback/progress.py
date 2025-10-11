"""Progress components for displaying progress indicators."""

from typing import Any, Dict, Optional
from ....core.rich_component import RichComponent, ComponentType


class ProgressBarComponent(RichComponent):
    """Progress bar with status and value."""

    type: ComponentType = ComponentType.PROGRESS_BAR
    value: float  # 0.0 to 1.0
    label: Optional[str] = None
    show_percentage: bool = True
    status: Optional[str] = None  # "success", "warning", "error"
    animated: bool = False


class ProgressDisplayComponent(RichComponent):
    """Generic progress display for any long-running process."""

    type: ComponentType = ComponentType.PROGRESS_DISPLAY
    label: str
    value: float = 0.0  # 0.0 to 1.0
    description: Optional[str] = None
    status: Optional[str] = None  # "info", "success", "warning", "error"
    show_percentage: bool = True
    animated: bool = False
    indeterminate: bool = False

    def update_progress(self, value: float, description: Optional[str] = None) -> "ProgressDisplayComponent":
        """Update progress value and optionally description."""
        updates: Dict[str, Any] = {"value": max(0.0, min(1.0, value))}
        if description is not None:
            updates["description"] = description
        return self.update(**updates)
