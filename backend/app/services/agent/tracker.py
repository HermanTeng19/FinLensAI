"""FinLens AI Agent Execution Profiler & Trace Logger.

Tracks and records:
1. End-to-end user question duration.
2. Chronological sequence of deterministic tool calls.
3. Execution latency and success status per tool.
4. Privacy-safe audit trail (ring-buffered) for runtime diagnostics.
"""

import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.privacy import redact_sensitive_text
from app.core.telemetry import correlation_id_ctx, metrics_collector


@dataclass
class ToolExecutionSpan:
    tool_name: str
    arguments: dict[str, Any]
    output_summary: str
    duration_ms: float
    success: bool = True
    error_message: str | None = None


@dataclass
class AITraceRecord:
    trace_id: str
    correlation_id: str
    timestamp: str
    query: str
    duration_ms: float
    grounded: bool
    tool_spans: list[ToolExecutionSpan] = field(default_factory=list)
    response_preview: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AITracker:
    """Singleton tracker maintaining runtime traces of Agentic AI queries."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._traces = deque(maxlen=100)
        return cls._instance

    def record_trace(
        self,
        query: str,
        duration_ms: float,
        grounded: bool,
        tool_spans: list[ToolExecutionSpan],
        response_text: str = "",
        trace_id: str | None = None,
    ) -> AITraceRecord:
        cid = correlation_id_ctx.get() or "none"
        tid = trace_id or str(uuid.uuid4())

        # Redact any PII from query and preview
        clean_query = redact_sensitive_text(query)
        clean_preview = redact_sensitive_text(response_text[:150])

        sanitized_spans: list[ToolExecutionSpan] = []
        for span in tool_spans:
            clean_args = {}
            for k, v in span.arguments.items():
                if isinstance(v, str):
                    clean_args[k] = redact_sensitive_text(v)
                else:
                    clean_args[k] = v
            clean_output = redact_sensitive_text(span.output_summary)
            sanitized_spans.append(
                ToolExecutionSpan(
                    tool_name=span.tool_name,
                    arguments=clean_args,
                    output_summary=clean_output,
                    duration_ms=span.duration_ms,
                    success=span.success,
                    error_message=span.error_message,
                )
            )

        record = AITraceRecord(
            trace_id=tid,
            correlation_id=cid,
            timestamp=datetime.now(UTC).isoformat(),
            query=clean_query,
            duration_ms=round(duration_ms, 2),
            grounded=grounded,
            tool_spans=sanitized_spans,
            response_preview=clean_preview,
        )

        self._traces.append(record)

        # Notify metrics collector
        metrics_collector.record_agent_query(duration_ms=duration_ms, grounded=grounded)
        for span in tool_spans:
            metrics_collector.record_agent_tool_call(tool_name=span.tool_name, success=span.success)

        return record

    def get_recent_traces(self, limit: int = 20) -> list[dict[str, Any]]:
        traces = list(self._traces)
        return [t.to_dict() for t in reversed(traces[-limit:])]

    def clear(self):
        self._traces.clear()


ai_tracker = AITracker()
