"""Rich text component."""

from typing import Optional
from ...core.rich_component import RichComponent, ComponentType


class RichTextComponent(RichComponent):
    """Rich text component with formatting options."""

    type: ComponentType = ComponentType.TEXT
    content: str
    markdown: bool = False
    code_language: Optional[str] = None  # For syntax highlighting
    font_size: Optional[str] = None
    font_weight: Optional[str] = None
    text_align: Optional[str] = None
