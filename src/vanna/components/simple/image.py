"""Simple image component."""

from typing import Optional
from pydantic import Field
from ...core.simple_component import SimpleComponent, SimpleComponentType


class SimpleImageComponent(SimpleComponent):
    """A simple image component."""

    type: SimpleComponentType = SimpleComponentType.IMAGE
    url: str = Field(..., description="The URL of the image to display.")
    alt_text: Optional[str] = Field(default=None, description="Alternative text for the image.")
