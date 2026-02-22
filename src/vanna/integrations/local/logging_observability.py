"""
LoggingObservabilityProvider — ObservabilityProvider backed by Python logging.

Writes span lifecycle events and metric measurements to Python's standard
logging module. Zero external dependencies — useful for development,
testing, and lightweight production deployments that already ship logs
to a log aggregation system (e.g., CloudWatch, Datadog log agent).

Usage::

    from vanna.integrations.local.logging_observability import LoggingObservabilityProvider

    obs = LoggingObservabilityProvider()
    agent = Agent(llm_service=..., observability_provider=obs)

Log format examples::

    [SPAN START] agent_comparison | id=3f2a... | {"num_variants": 2}
    [SPAN END]   agent_comparison | id=3f2a... | duration=142.3ms | {"num_variants": 2}
    [METRIC]     agent.request.duration=342.1ms | tags={"variant": "gpt-4"}
"""

import logging
from typing import Any, Dict, Optional

from vanna.core.observability import ObservabilityProvider
from vanna.core.observability.models import Span

logger = logging.getLogger(__name__)


class LoggingObservabilityProvider(ObservabilityProvider):
    """ObservabilityProvider that writes spans and metrics to Python logging.

    Args:
        span_log_level: Log level for span events (default: DEBUG).
        metric_log_level: Log level for metric events (default: DEBUG).
    """

    def __init__(
        self,
        span_log_level: int = logging.DEBUG,
        metric_log_level: int = logging.DEBUG,
    ) -> None:
        self.span_log_level = span_log_level
        self.metric_log_level = metric_log_level

    async def create_span(
        self, name: str, attributes: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Create and log a new span.

        Args:
            name: Span name / operation label.
            attributes: Optional key-value attributes to attach to the span.

        Returns:
            A new :class:`Span` instance.
        """
        span = Span(name=name, attributes=attributes or {})
        attrs_str = _fmt_attrs(span.attributes)
        logger.log(
            self.span_log_level,
            "[SPAN START] %s | id=%.8s%s",
            name,
            span.id,
            f" | {attrs_str}" if attrs_str else "",
        )
        return span

    async def end_span(self, span: Span) -> None:
        """End a span and log its duration.

        Args:
            span: The span to end.
        """
        span.end()
        duration = span.duration_ms()
        duration_str = f"{duration:.1f}ms" if duration is not None else "n/a"
        attrs_str = _fmt_attrs(span.attributes)
        logger.log(
            self.span_log_level,
            "[SPAN END]   %s | id=%.8s | duration=%s%s",
            span.name,
            span.id,
            duration_str,
            f" | {attrs_str}" if attrs_str else "",
        )

    async def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "",
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Log a metric measurement.

        Args:
            name: Metric name (e.g., ``"agent.request.duration"``).
            value: Numeric value.
            unit: Unit of measurement (e.g., ``"ms"``, ``"tokens"``).
            tags: Optional string key-value tags.
        """
        value_str = f"{value}{unit}" if unit else str(value)
        tags_str = f" | tags={tags}" if tags else ""
        logger.log(
            self.metric_log_level,
            "[METRIC]     %s=%s%s",
            name,
            value_str,
            tags_str,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt_attrs(attrs: Dict[str, Any]) -> str:
    """Return a compact string representation of span attributes, or ''."""
    if not attrs:
        return ""
    parts = [f"{k}={v!r}" for k, v in attrs.items()]
    return "{" + ", ".join(parts) + "}"
