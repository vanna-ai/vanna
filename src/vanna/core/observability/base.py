"""
Base observability provider interface.

Observability providers allow you to collect telemetry data about
agent execution for monitoring and debugging.
"""

from abc import ABC
from typing import Any, Dict, Optional

from .models import Span, Metric


class ObservabilityProvider(ABC):
    """Provider for collecting telemetry and observability data.

    Subclass this to create custom observability integrations that can:
    - Emit metrics to monitoring systems
    - Create distributed traces
    - Log performance data
    - Track costs and usage
    - Monitor error rates

    Example:
        class PrometheusProvider(ObservabilityProvider):
            def __init__(self, registry):
                self.registry = registry
                self.request_counter = Counter(
                    'agent_requests_total',
                    'Total agent requests',
                    registry=registry
                )

            async def record_metric(self, name: str, value: float, tags: Dict[str, str]) -> None:
                if name == "agent.request":
                    self.request_counter.inc()

            async def create_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Span:
                span = Span(name=name, attributes=attributes or {})
                return span

        agent = AgentRunner(
            llm_service=...,
            observability_provider=PrometheusProvider(registry)
        )
    """

    async def record_metric(
        self, name: str, value: float, unit: str = "", tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric measurement.

        Args:
            name: Metric name (e.g., "agent.request.duration")
            value: Metric value
            unit: Unit of measurement (e.g., "ms", "tokens")
            tags: Additional tags/labels for the metric
        """
        pass

    async def create_span(
        self, name: str, attributes: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Create a new span for tracing.

        Args:
            name: Span name/operation
            attributes: Initial span attributes

        Returns:
            Span object to track the operation

        Note:
            Call span.end() when the operation completes.
        """
        return Span(name=name, attributes=attributes or {})

    async def end_span(self, span: Span) -> None:
        """End a span and record it.

        Args:
            span: The span to end
        """
        span.end()
