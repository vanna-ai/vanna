"""Badge component for displaying status or labels."""

from typing import Optional
from ....core.rich_component import RichComponent, ComponentType


class BadgeComponent(RichComponent):
    """Simple badge/pill component for displaying status or labels."""

    type: ComponentType = ComponentType.BADGE
    text: str
    variant: str = "default"  # "default", "primary", "success", "warning", "error", "info"
    size: str = "medium"  # "small", "medium", "large"
    icon: Optional[str] = None
