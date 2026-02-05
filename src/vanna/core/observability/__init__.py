"""
Observability system for telemetry and monitoring.

This module provides interfaces for collecting metrics, traces, and
monitoring agent behavior.
"""

from .base import ObservabilityProvider
from .models import Span, Metric

__all__ = ["ObservabilityProvider", "Span", "Metric"]
