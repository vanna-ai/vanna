from contextlib import contextmanager

from opentelemetry import trace as otel_trace

from .otel import MISTRAL_SDK_OTEL_TRACER_NAME


@contextmanager
def trace(name: str, **kwargs):
    tracer = otel_trace.get_tracer(MISTRAL_SDK_OTEL_TRACER_NAME)
    with tracer.start_as_current_span(name, **kwargs) as span:
        yield span


__all__ = ["trace"]
