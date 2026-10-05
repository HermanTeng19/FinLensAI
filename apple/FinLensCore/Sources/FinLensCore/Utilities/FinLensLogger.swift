import Foundation
import os

/// FinLens AI Unified Logging Framework.
/// Wraps native `os.Logger` with strict privacy specifiers and category separation.
public enum FinLensLogger: Sendable {
    private static let subsystem = "com.finlens.ai"

    public static let networking = Logger(subsystem: subsystem, category: "networking")
    public static let agent = Logger(subsystem: subsystem, category: "agent")
    public static let analytics = Logger(subsystem: subsystem, category: "analytics")
    public static let insights = Logger(subsystem: subsystem, category: "insights")
    public static let ui = Logger(subsystem: subsystem, category: "ui")
    public static let privacy = Logger(subsystem: subsystem, category: "privacy")

    /// Log outgoing network request with public correlation ID and endpoint.
    public static func logRequest(method: String, url: URL, correlationId: String) {
        networking.info("--> [\(method, privacy: .public)] \(url.path, privacy: .public) [cid: \(correlationId, privacy: .public)]")
    }

    /// Log incoming network response with public correlation ID, status code, and latency.
    public static func logResponse(
        statusCode: Int,
        url: URL,
        correlationId: String,
        responseTime: String?
    ) {
        let latency = responseTime ?? "unknown"
        networking.info("<-- [\(statusCode, privacy: .public)] \(url.path, privacy: .public) (\(latency, privacy: .public)) [cid: \(correlationId, privacy: .public)]")
    }

    /// Log network error safely without leaking sensitive payload data.
    public static func logNetworkError(url: URL, error: String, correlationId: String) {
        networking.error("<!- [ERROR] \(url.path, privacy: .public): \(error, privacy: .public) [cid: \(correlationId, privacy: .public)]")
    }

    /// Log AI agent execution event with public tool name and masked user query.
    public static func logAgentExecution(
        toolName: String?,
        grounded: Bool,
        durationMs: Double
    ) {
        let tool = toolName ?? "direct_response"
        agent.info("AI Agent [tool: \(tool, privacy: .public)] grounded=\(grounded, privacy: .public) latency=\(durationMs, privacy: .public)ms")
    }
}
