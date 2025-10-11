"""
Observability models for spans and metrics.
"""

import time
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Span(BaseModel):
    """Represents a unit of work for distributed tracing."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Span ID")
    name: str = Field(description="Span name/operation")
    start_time: float = Field(
        default_factory=time.time, description="Start timestamp"
    )
    end_time: Optional[float] = Field(default=None, description="End timestamp")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Span attributes"
    )
    parent_id: Optional[str] = Field(default=None, description="Parent span ID")

    def end(self) -> None:
        """Mark span as ended."""
        if self.end_time is None:
            self.end_time = time.time()

    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value


class Metric(BaseModel):
    """Represents a metric measurement."""

    name: str = Field(description="Metric name")
    value: float = Field(description="Metric value")
    unit: str = Field(default="", description="Unit of measurement")
    tags: Dict[str, str] = Field(default_factory=dict, description="Metric tags")
    timestamp: float = Field(default_factory=time.time, description="Measurement time")
