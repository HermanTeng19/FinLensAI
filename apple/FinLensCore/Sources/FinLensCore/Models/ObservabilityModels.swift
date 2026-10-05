import Foundation

/// System and runtime telemetry metrics snapshot from FinLens AI backend.
public struct SystemMetrics: Codable, Sendable {
    public let uptimeSeconds: Double
    public let system: SystemProcessMetrics
    public let http: HTTPTelemetryMetrics
    public let documentAi: DocumentAIMetrics
    public let agentAi: AgentAIMetrics
    public let insights: InsightsMetrics

    public init(
        uptimeSeconds: Double,
        system: SystemProcessMetrics,
        http: HTTPTelemetryMetrics,
        documentAi: DocumentAIMetrics,
        agentAi: AgentAIMetrics,
        insights: InsightsMetrics
    ) {
        self.uptimeSeconds = uptimeSeconds
        self.system = system
        self.http = http
        self.documentAi = documentAi
        self.agentAi = agentAi
        self.insights = insights
    }
}

public struct SystemProcessMetrics: Codable, Sendable {
    public let processId: Int
    public let memoryRssMb: Double
    public let cpuPercent: Double
}

public struct HTTPLatencyMetrics: Codable, Sendable {
    public let avg: Double
    public let p50: Double
    public let p95: Double
    public let p99: Double
}

public struct HTTPTelemetryMetrics: Codable, Sendable {
    public let totalRequests: Int
    public let statusCodes: [String: Int]
    public let topEndpoints: [String: Int]
    public let latencyMs: HTTPLatencyMetrics
}

public struct DocumentAIMetrics: Codable, Sendable {
    public let statementsProcessed: Int
    public let statementsFailed: Int
    public let transactionsExtracted: Int
    public let avgParsingDurationMs: Double
}

public struct AgentAIMetrics: Codable, Sendable {
    public let queriesTotal: Int
    public let groundedTotal: Int
    public let groundingRate: Double
    public let avgQueryLatencyMs: Double
    public let p95QueryLatencyMs: Double
    public let toolExecutions: [String: Int]
    public let toolErrors: [String: Int]
}

public struct InsightsMetrics: Codable, Sendable {
    public let totalGenerated: Int
    public let bySeverity: [String: Int]
}

/// Sanitized AI execution trace record.
public struct AITraceRecord: Codable, Identifiable, Sendable {
    public var id: String { traceId }
    public let traceId: String
    public let correlationId: String
    public let timestamp: String
    public let query: String
    public let durationMs: Double
    public let grounded: Bool
    public let toolSpans: [ToolExecutionSpanDTO]
    public let responsePreview: String
}

public struct ToolExecutionSpanDTO: Codable, Sendable {
    public let toolName: String
    public let outputSummary: String
    public let durationMs: Double
    public let success: Bool
    public let errorMessage: String?
}
