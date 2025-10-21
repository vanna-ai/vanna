"""Button component for interactive actions."""

from typing import Literal, Optional
from ....core.rich_component import RichComponent


class ButtonComponent(RichComponent):
    """Interactive button that sends a message when clicked.
    
    The button renders in the UI and when clicked, sends its action
    value as a message to the chat input.
    
    Args:
        label: Text displayed on the button
        action: Message/command to send when clicked
        variant: Visual style variant
        size: Button size
        icon: Optional emoji or icon
        icon_position: Position of icon relative to label
        disabled: Whether button is disabled
    
    Example:
        ButtonComponent(
            label="Generate Report",
            action="/report sales",
            variant="primary",
            icon="📊"
        )
    """

    def __init__(
        self,
        label: str,
        action: str,
        variant: Literal["primary", "secondary", "success", "warning", "error", "ghost", "link"] = "primary",
        size: Literal["small", "medium", "large"] = "medium",
        icon: Optional[str] = None,
        icon_position: Literal["left", "right"] = "left",
        disabled: bool = False,
    ):
        super().__init__(
            type="button",
            data={
                "label": label,
                "action": action,
                "variant": variant,
                "size": size,
                "icon": icon,
                "icon_position": icon_position,
                "disabled": disabled,
            },
        )


class ButtonGroupComponent(RichComponent):
    """Group of buttons with consistent styling.
    
    Args:
        buttons: List of button data dictionaries
        orientation: Layout direction
        spacing: Gap between buttons
        alignment: Button alignment within group
        full_width: Whether buttons should stretch to fill width
    
    Example:
        ButtonGroupComponent(
            buttons=[
                {"label": "Yes", "action": "/confirm yes", "variant": "success"},
                {"label": "No", "action": "/confirm no", "variant": "error"},
            ],
            orientation="horizontal",
            spacing="medium"
        )
    """

    def __init__(
        self,
        buttons: list[dict],
        orientation: Literal["horizontal", "vertical"] = "horizontal",
        spacing: Literal["small", "medium", "large"] = "medium",
        alignment: Literal["start", "center", "end", "stretch"] = "start",
        full_width: bool = False,
    ):
        super().__init__(
            type="button_group",
            data={
                "buttons": buttons,
                "orientation": orientation,
                "spacing": spacing,
                "alignment": alignment,
                "full_width": full_width,
            },
        )
