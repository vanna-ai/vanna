"""Status indicator component."""

from typing import Optional
from ....core.rich_component import RichComponent, ComponentType


class StatusIndicatorComponent(RichComponent):
    """Status indicator with icon and message."""

    type: ComponentType = ComponentType.STATUS_INDICATOR
    status: str  # "success", "warning", "error", "info", "loading"
    message: str
    icon: Optional[str] = None
    pulse: bool = False
