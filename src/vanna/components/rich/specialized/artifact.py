"""Artifact component for interactive content."""

import uuid
from typing import Optional
from pydantic import Field
from ....core.rich_component import RichComponent, ComponentType


class ArtifactComponent(RichComponent):
    """Component for displaying interactive artifacts that can be rendered externally."""

    type: ComponentType = ComponentType.ARTIFACT
    artifact_id: str = Field(default_factory=lambda: f"artifact_{uuid.uuid4().hex[:8]}")
    content: str  # HTML/SVG/JS content
    artifact_type: str  # "html", "svg", "visualization", "interactive", "d3", "threejs"
    title: Optional[str] = None
    description: Optional[str] = None
    editable: bool = True
    fullscreen_capable: bool = True
    external_renderable: bool = True
