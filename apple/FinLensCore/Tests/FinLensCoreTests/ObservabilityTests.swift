import Foundation
import Testing
@testable import FinLensCore

struct ObservabilityTests {
    @Test func testFinLensLoggerInvocations() {
        let testURL = URL(string: "http://127.0.0.1:8000/api/v1/observability/metrics")!
        FinLensLogger.logRequest(method: "GET", url: testURL, correlationId: "test-cid-123")
        FinLensLogger.logResponse(statusCode: 200, url: testURL, correlationId: "test-cid-123", responseTime: "1.23ms")
        FinLensLogger.logNetworkError(url: testURL, error: "Connection refused", correlationId: "test-cid-123")
        FinLensLogger.logAgentExecution(toolName: "get_monthly_summary", grounded: true, durationMs: 14.5)
    }

    @Test func testSystemMetricsDecoding() throws {
        let json = """
        {
            "uptime_seconds": 125.4,
            "system": {
                "process_id": 1234,
                "memory_rss_mb": 82.5,
                "cpu_percent": 0.5
            },
            "http": {
                "total_requests": 42,
                "status_codes": {"200": 40, "404": 2},
                "top_endpoints": {"GET /api/transactions": 25},
                "latency_ms": {
                    "avg": 8.5,
                    "p50": 6.2,
                    "p95": 18.4,
                    "p99": 22.0
                }
            },
            "document_ai": {
                "statements_processed": 5,
                "statements_failed": 0,
                "transactions_extracted": 120,
                "avg_parsing_duration_ms": 45.2
            },
            "agent_ai": {
                "queries_total": 8,
                "grounded_total": 8,
                "grounding_rate": 100.0,
                "avg_query_latency_ms": 15.6,
                "p95_query_latency_ms": 22.1,
                "tool_executions": {"get_spending_by_category": 5},
                "tool_errors": {}
            },
            "insights": {
                "total_generated": 10,
                "by_severity": {"high": 2, "medium": 5, "low": 3}
            }
        }
        """

        let decoder = FinLensJSONDecoder.makeStandard()
        let metrics = try decoder.decode(SystemMetrics.self, from: json.data(using: .utf8)!)

        #expect(metrics.uptimeSeconds == 125.4)
        #expect(metrics.system.processId == 1234)
        #expect(metrics.system.memoryRssMb == 82.5)
        #expect(metrics.http.totalRequests == 42)
        #expect(metrics.http.latencyMs.p95 == 18.4)
        #expect(metrics.documentAi.statementsProcessed == 5)
        #expect(metrics.agentAi.groundingRate == 100.0)
        #expect(metrics.insights.totalGenerated == 10)
    }

    @Test func testAITraceRecordDecoding() throws {
        let json = """
        [
            {
                "trace_id": "tr-abc-123",
                "correlation_id": "cid-xyz-789",
                "timestamp": "2026-10-05T00:20:00Z",
                "query": "Find spending for card [REDACTED_CARD]",
                "duration_ms": 14.8,
                "grounded": true,
                "tool_spans": [
                    {
                        "tool_name": "search_transactions",
                        "output_summary": "1 transaction found",
                        "duration_ms": 14.8,
                        "success": true,
                        "error_message": null
                    }
                ],
                "response_preview": "Found transaction for [REDACTED_CARD]"
            }
        ]
        """

        let decoder = FinLensJSONDecoder.makeStandard()
        let traces = try decoder.decode([AITraceRecord].self, from: json.data(using: .utf8)!)

        #expect(traces.count == 1)
        let trace = traces[0]
        #expect(trace.traceId == "tr-abc-123")
        #expect(trace.correlationId == "cid-xyz-789")
        #expect(trace.grounded == true)
        #expect(trace.toolSpans.count == 1)
        #expect(trace.toolSpans[0].toolName == "search_transactions")
        #expect(trace.query.contains("[REDACTED_CARD]"))
    }

    @Test func testMockObservabilityMethods() async throws {
        let mock = MockAPIClient()
        let metrics = try await mock.fetchSystemMetrics()
        #expect(metrics.uptimeSeconds == 120.0)
        #expect(metrics.http.totalRequests == 10)

        let traces = try await mock.fetchAITraces(limit: 5)
        #expect(traces.count == 1)
        #expect(traces[0].traceId == "trace_mock_1")
    }
}
