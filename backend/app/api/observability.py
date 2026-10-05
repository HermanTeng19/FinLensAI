"""FinLens AI Observability & Diagnostics Endpoints.

Provides:
- GET /api/v1/observability/metrics: Real-time telemetry, latency percentiles, Document AI & Agent metrics.
- GET /api/v1/observability/traces: Ring-buffered AI agent execution traces with sanitized audit trails.
- POST /api/v1/observability/reset: Reset in-memory telemetry counters (testing & diagnostics).
"""

from typing import Any

from fastapi import APIRouter, Query

from app.core.telemetry import metrics_collector
from app.services.agent.tracker import ai_tracker

router = APIRouter(prefix="/observability", tags=["Observability"])


@router.get("/metrics")
async def get_system_metrics() -> dict[str, Any]:
    """Retrieve runtime telemetry, HTTP latency distributions, and AI subsystem metrics."""
    return metrics_collector.get_snapshot()


@router.get("/traces")
async def get_recent_ai_traces(
    limit: int = Query(default=20, ge=1, le=100, description="Max number of traces to return"),
) -> list[dict[str, Any]]:
    """Retrieve recent sanitized AI Agent execution traces."""
    return ai_tracker.get_recent_traces(limit=limit)


@router.post("/reset")
async def reset_telemetry() -> dict[str, str]:
    """Reset telemetry counters and traces (diagnostic use)."""
    metrics_collector.reset()
    ai_tracker.clear()
    return {"status": "telemetry_reset"}
