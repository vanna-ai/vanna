"""Icon with text component."""

from ....core.rich_component import RichComponent, ComponentType


class IconTextComponent(RichComponent):
    """Simple component for displaying an icon with text."""

    type: ComponentType = ComponentType.ICON_TEXT
    icon: str
    text: str
    variant: str = "default"  # "default", "primary", "secondary", "muted"
    size: str = "medium"  # "small", "medium", "large"
    alignment: str = "left"  # "left", "center", "right"
