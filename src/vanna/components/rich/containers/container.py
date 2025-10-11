"""Container component for grouping other components."""

from typing import Optional
from ....core.rich_component import RichComponent, ComponentType


class ContainerComponent(RichComponent):
    """Container for grouping other components."""

    type: ComponentType = ComponentType.CONTAINER
    title: Optional[str] = None
    direction: str = "column"  # "row" or "column"
    spacing: Optional[str] = None
    wrap: bool = False
