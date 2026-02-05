"""Simple UI components for basic rendering."""

# Import from core
from ...core.simple_component import SimpleComponent, SimpleComponentType
from .text import SimpleTextComponent
from .image import SimpleImageComponent
from .link import SimpleLinkComponent

__all__ = [
    "SimpleComponent",
    "SimpleComponentType",
    "SimpleTextComponent",
    "SimpleImageComponent",
    "SimpleLinkComponent",
]
