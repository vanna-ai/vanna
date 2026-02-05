"""Chart component for data visualization."""

from typing import Any, Dict, Optional, Union
from pydantic import Field
from ....core.rich_component import RichComponent, ComponentType


class ChartComponent(RichComponent):
    """Chart component for data visualization."""

    type: ComponentType = ComponentType.CHART
    chart_type: str  # "line", "bar", "pie", "scatter", etc.
    data: Dict[str, Any]  # Chart data in format expected by frontend
    title: Optional[str] = None
    width: Optional[Union[str, int]] = None
    height: Optional[Union[str, int]] = None
    config: Dict[str, Any] = Field(default_factory=dict)  # Chart-specific config
