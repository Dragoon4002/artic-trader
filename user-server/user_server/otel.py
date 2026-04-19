"""OTel tracer/meter setup. No-op if OTEL_EXPORTER_OTLP_ENDPOINT is unset.

Kept minimal in alpha — just enough for explicit spans elsewhere in the
codebase to ship to a collector when one is configured.
"""
from __future__ import annotations

import os


def setup() -> None:
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return
    try:
        from opentelemetry import trace  # noqa: PLC0415
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # noqa: PLC0415
        from opentelemetry.sdk.resources import Resource  # noqa: PLC0415
        from opentelemetry.sdk.trace import TracerProvider  # noqa: PLC0415
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # noqa: PLC0415
    except ImportError:
        return  # opentelemetry not installed

    provider = TracerProvider(resource=Resource.create({"service.name": "artic-user-server"}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
