"""Tests for FinLens AI Observability, Telemetry, and Latency Tracking Framework."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.telemetry import MetricsCollector, correlation_id_ctx
from app.main import app
from app.services.agent.tracker import ToolExecutionSpan, ai_tracker


@pytest.mark.asyncio
async def test_metrics_collector_unit():
    collector = MetricsCollector()
    collector.reset()

    # Record HTTP calls
    collector.record_http_request("GET", "/api/transactions", 200, 12.5)
    collector.record_http_request("POST", "/api/statements/upload", 201, 45.0)
    collector.record_http_request("GET", "/api/transactions/invalid", 404, 3.2)

    # Record Document AI calls
    collector.record_statement_processed(transactions_count=15, duration_ms=120.0, success=True)
    collector.record_statement_processed(transactions_count=0, duration_ms=50.0, success=False)

    # Record AI Agent calls
    collector.record_agent_query(duration_ms=85.0, grounded=True)
    collector.record_agent_tool_call("search_transactions", success=True)
    collector.record_agent_tool_call("summarize_expenses", success=False)

    # Record Insights
    collector.record_insights_generated(3, {"high": 1, "medium": 2})

    snapshot = collector.get_snapshot()

    assert snapshot["http"]["total_requests"] == 3
    assert snapshot["http"]["status_codes"]["2xx"] == 2
    assert snapshot["http"]["status_codes"]["4xx"] == 1
    assert snapshot["document_ai"]["statements_processed"] == 1
    assert snapshot["document_ai"]["statements_failed"] == 1
    assert snapshot["document_ai"]["transactions_extracted"] == 15
    assert snapshot["agent_ai"]["queries_total"] == 1
    assert snapshot["agent_ai"]["grounded_total"] == 1
    assert snapshot["agent_ai"]["grounding_rate"] == 100.0
    assert snapshot["agent_ai"]["tool_executions"]["search_transactions"] == 1
    assert snapshot["agent_ai"]["tool_errors"]["summarize_expenses"] == 1
    assert snapshot["insights"]["total_generated"] == 3


@pytest.mark.asyncio
async def test_observability_middleware_headers_and_correlation_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Automatic Correlation ID generation
        res1 = await client.get("/api/v1/observability/metrics")
        assert res1.status_code == 200
        assert "x-correlation-id" in res1.headers
        assert "x-response-time" in res1.headers
        assert len(res1.headers["x-correlation-id"]) > 10

        # 2. Custom Correlation ID propagation
        custom_cid = "client-trace-abc-12345"
        res2 = await client.get(
            "/api/v1/observability/metrics",
            headers={"X-Correlation-ID": custom_cid},
        )
        assert res2.status_code == 200
        assert res2.headers["X-Correlation-ID"] == custom_cid
        assert "x-response-time" in res2.headers

        data = res2.json()
        assert "system" in data
        assert "http" in data
        assert data["http"]["total_requests"] >= 2


@pytest.mark.asyncio
async def test_ai_tracker_and_sanitization():
    ai_tracker.clear()

    # Record trace with sensitive info
    span = ToolExecutionSpan(
        tool_name="search_transactions",
        arguments={"query": "find card 4532 1234 5678 9012 for sin 123-45-6789"},
        output_summary="Result with account # 12345678",
        duration_ms=15.2,
        success=True,
    )

    token = correlation_id_ctx.set("corr-test-999")
    ai_tracker.record_trace(
        query="What is the balance for card 4532-1234-5678-9012?",
        duration_ms=25.0,
        grounded=True,
        tool_spans=[span],
        response_text="The card 4532 1234 5678 9012 balance is $100.00",
    )
    correlation_id_ctx.reset(token)

    traces = ai_tracker.get_recent_traces(limit=5)
    assert len(traces) == 1
    t = traces[0]

    assert t["correlation_id"] == "corr-test-999"
    assert "[REDACTED_CARD]" in t["query"]
    assert "4532" not in t["query"]
    assert "[REDACTED_CARD]" in t["response_preview"]
    assert "4532" not in t["response_preview"]
    assert "[REDACTED_CARD]" in t["tool_spans"][0]["arguments"]["query"]
    assert "[REDACTED_ACCOUNT]" in t["tool_spans"][0]["output_summary"]


@pytest.mark.asyncio
async def test_observability_api_traces_and_reset():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Reset telemetry
        reset_res = await client.post("/api/v1/observability/reset")
        assert reset_res.status_code == 200
        assert reset_res.json() == {"status": "telemetry_reset"}

        # Traces should now be empty
        traces_res = await client.get("/api/v1/observability/traces")
        assert traces_res.status_code == 200
        assert traces_res.json() == []


@pytest.mark.asyncio
async def test_centralized_error_handling():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Validation error returns 422 with correlation ID
        res = await client.post(
            "/api/agent/query",
            json={"invalid_key": "data"},
            headers={"X-Correlation-ID": "test-err-cid"},
        )
        assert res.status_code == 422
        body = res.json()
        assert body["correlation_id"] == "test-err-cid"
        assert "detail" in body
