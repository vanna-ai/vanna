"""Notification component for alerts and messages."""

from typing import Any, Dict, List, Optional
from pydantic import Field
from ....core.rich_component import RichComponent, ComponentType


class NotificationComponent(RichComponent):
    """Notification component for alerts and messages."""

    type: ComponentType = ComponentType.NOTIFICATION
    message: str
    title: Optional[str] = None
    level: str = "info"  # "success", "info", "warning", "error"
    icon: Optional[str] = None
    dismissible: bool = True
    auto_dismiss: bool = False
    auto_dismiss_delay: int = 5000  # milliseconds
    actions: List[Dict[str, Any]] = Field(default_factory=list)
