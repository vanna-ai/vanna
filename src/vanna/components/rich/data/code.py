"""Code block component with syntax highlighting."""

from typing import List, Optional
from pydantic import Field
from ....core.rich_component import RichComponent, ComponentType


class CodeBlockComponent(RichComponent):
    """Code block with syntax highlighting."""

    type: ComponentType = ComponentType.CODE_BLOCK
    code: str
    language: str = "text"
    title: Optional[str] = None
    line_numbers: bool = True
    highlight_lines: List[int] = Field(default_factory=list)
    wrap_lines: bool = False
    copyable: bool = True
