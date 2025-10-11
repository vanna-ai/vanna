"""Card component for displaying structured information."""

from typing import Any, Dict, List, Optional
from pydantic import Field
from ....core.rich_component import RichComponent, ComponentType


class CardComponent(RichComponent):
    """Card component for displaying structured information."""

    type: ComponentType = ComponentType.CARD
    title: str
    content: str
    subtitle: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[str] = None  # "success", "warning", "error", "info"
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    collapsible: bool = False
    collapsed: bool = False
