"""Simple link component."""

from typing import Optional
from pydantic import Field
from ...core.simple_component import SimpleComponent, SimpleComponentType


class SimpleLinkComponent(SimpleComponent):
    """A simple link component."""

    type: SimpleComponentType = SimpleComponentType.LINK
    url: str = Field(..., description="The URL the link points to.")
    text: Optional[str] = Field(default=None, description="The display text for the link.")
