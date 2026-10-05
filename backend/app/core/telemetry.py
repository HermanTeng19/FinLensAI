"""FinLens AI Telemetry & Observability Framework.

Provides:
1. Thread-safe MetricsCollector for HTTP traffic, document processing, and AI tool telemetry.
2. ContextVar-driven Correlation ID propagation (X-Correlation-ID).
3. Latency measurement middleware injecting X-Response-Time headers and logging slow requests.
"""

import os
import time
import uuid
from contextvars import ContextVar
from typing import Any

try:
    import psutil
except ImportError:
    psutil = None
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context variable for request correlation ID
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


class MetricsCollector:
    """Thread-safe in-memory metrics and telemetry aggregator for FinLens AI."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_metrics()
        return cls._instance

    def _init_metrics(self):
        self.start_time = time.time()
        # HTTP Traffic
        self.total_requests = 0
        self.status_code_counts: dict[str, int] = {}
        self.endpoint_counts: dict[str, int] = {}
        self.latencies_ms: list[float] = []

        # Document AI Processing
        self.statements_processed = 0
        self.statements_failed = 0
        self.total_transactions_extracted = 0
        self.parsing_durations_ms: list[float] = []

        # AI Agent Execution
        self.agent_queries_total = 0
        self.agent_grounded_total = 0
        self.agent_latencies_ms: list[float] = []
        self.agent_tool_executions: dict[str, int] = {}
        self.agent_tool_errors: dict[str, int] = {}

        # AI Insights Engine
        self.insights_generated_total = 0
        self.insights_by_severity: dict[str, int] = {
            "high": 0,
            "medium": 0,
            "low": 0,
        }

    def reset(self):
        """Reset metrics (useful for testing)."""
        self._init_metrics()

    # --- HTTP Metrics ---
    def record_http_request(self, method: str, path: str, status_code: int, duration_ms: float):
        self.total_requests += 1

        # Status code group (e.g. "2xx", "4xx", "5xx")
        group = f"{status_code // 100}xx"
        self.status_code_counts[group] = self.status_code_counts.get(group, 0) + 1

        # Specific code
        code_str = str(status_code)
        self.status_code_counts[code_str] = self.status_code_counts.get(code_str, 0) + 1

        # Endpoint count (normalized)
        normalized_path = path.split("?")[0]
        key = f"{method.upper()} {normalized_path}"
        self.endpoint_counts[key] = self.endpoint_counts.get(key, 0) + 1

        # Latency tracking (bounded to last 10,000 samples)
        self.latencies_ms.append(duration_ms)
        if len(self.latencies_ms) > 10000:
            self.latencies_ms = self.latencies_ms[-5000:]

    # --- Document AI Metrics ---
    def record_statement_processed(
        self, transactions_count: int, duration_ms: float, success: bool = True
    ):
        if success:
            self.statements_processed += 1
            self.total_transactions_extracted += transactions_count
            self.parsing_durations_ms.append(duration_ms)
            if len(self.parsing_durations_ms) > 1000:
                self.parsing_durations_ms = self.parsing_durations_ms[-500:]
        else:
            self.statements_failed += 1

    # --- AI Agent Metrics ---
    def record_agent_query(self, duration_ms: float, grounded: bool = True):
        self.agent_queries_total += 1
        if grounded:
            self.agent_grounded_total += 1
        self.agent_latencies_ms.append(duration_ms)
        if len(self.agent_latencies_ms) > 1000:
            self.agent_latencies_ms = self.agent_latencies_ms[-500:]

    def record_agent_tool_call(self, tool_name: str, success: bool = True):
        self.agent_tool_executions[tool_name] = self.agent_tool_executions.get(tool_name, 0) + 1
        if not success:
            self.agent_tool_errors[tool_name] = self.agent_tool_errors.get(tool_name, 0) + 1

    # --- Insights Metrics ---
    def record_insights_generated(self, count: int, severity_counts: dict[str, int] | None = None):
        self.insights_generated_total += count
        if severity_counts:
            for sev, c in severity_counts.items():
                self.insights_by_severity[sev] = self.insights_by_severity.get(sev, 0) + c

    # --- Snapshot & Calculations ---
    def get_snapshot(self) -> dict[str, Any]:
        uptime_seconds = time.time() - self.start_time

        # Calculate latency percentiles for HTTP
        http_p50, http_p95, http_p99, http_avg = 0.0, 0.0, 0.0, 0.0
        if self.latencies_ms:
            sorted_lat = sorted(self.latencies_ms)
            n = len(sorted_lat)
            http_avg = sum(sorted_lat) / n
            http_p50 = sorted_lat[int(n * 0.50)]
            http_p95 = sorted_lat[int(min(n * 0.95, n - 1))]
            http_p99 = sorted_lat[int(min(n * 0.99, n - 1))]

        # Calculate AI latency percentiles
        ai_avg, ai_p95 = 0.0, 0.0
        if self.agent_latencies_ms:
            sorted_ai = sorted(self.agent_latencies_ms)
            ai_avg = sum(sorted_ai) / len(sorted_ai)
            ai_p95 = sorted_ai[int(min(len(sorted_ai) * 0.95, len(sorted_ai) - 1))]

        # Memory & Process info
        mem_rss_mb = 0.0
        cpu_pct = 0.0
        if psutil is not None:
            try:
                process = psutil.Process(os.getpid())
                mem_rss_mb = round(process.memory_info().rss / (1024 * 1024), 2)
                cpu_pct = process.cpu_percent(interval=None)
            except Exception:
                pass

        return {
            "uptime_seconds": round(uptime_seconds, 2),
            "system": {
                "process_id": os.getpid(),
                "memory_rss_mb": mem_rss_mb,
                "cpu_percent": cpu_pct,
            },
            "http": {
                "total_requests": self.total_requests,
                "status_codes": self.status_code_counts,
                "top_endpoints": dict(
                    sorted(self.endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                ),
                "latency_ms": {
                    "avg": round(http_avg, 2),
                    "p50": round(http_p50, 2),
                    "p95": round(http_p95, 2),
                    "p99": round(http_p99, 2),
                },
            },
            "document_ai": {
                "statements_processed": self.statements_processed,
                "statements_failed": self.statements_failed,
                "transactions_extracted": self.total_transactions_extracted,
                "avg_parsing_duration_ms": (
                    round(sum(self.parsing_durations_ms) / len(self.parsing_durations_ms), 2)
                    if self.parsing_durations_ms
                    else 0.0
                ),
            },
            "agent_ai": {
                "queries_total": self.agent_queries_total,
                "grounded_total": self.agent_grounded_total,
                "grounding_rate": (
                    round((self.agent_grounded_total / self.agent_queries_total) * 100, 1)
                    if self.agent_queries_total > 0
                    else 100.0
                ),
                "avg_query_latency_ms": round(ai_avg, 2),
                "p95_query_latency_ms": round(ai_p95, 2),
                "tool_executions": self.agent_tool_executions,
                "tool_errors": self.agent_tool_errors,
            },
            "insights": {
                "total_generated": self.insights_generated_total,
                "by_severity": self.insights_by_severity,
            },
        }


# Global singleton instance
metrics_collector = MetricsCollector()


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Extracts or creates an X-Correlation-ID / X-Request-ID.
    2. Measures request execution duration.
    3. Records HTTP metrics in MetricsCollector.
    4. Injects X-Correlation-ID and X-Response-Time headers into the response.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 1. Resolve Correlation ID
        cid = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )
        token = correlation_id_ctx.set(cid)

        # 2. Measure Execution Latency
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # Still record metrics on unhandled error before re-raising
            duration_ms = (time.perf_counter() - start_time) * 1000
            metrics_collector.record_http_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=duration_ms,
            )
            correlation_id_ctx.reset(token)
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        # 3. Record HTTP Telemetry
        metrics_collector.record_http_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # 4. Attach Observability Headers
        response.headers["X-Correlation-ID"] = cid
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        correlation_id_ctx.reset(token)
        return response
