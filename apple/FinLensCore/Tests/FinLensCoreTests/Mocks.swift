import Foundation
@testable import FinLensCore

public final class MockAPIClient: APIClientProtocol, @unchecked Sendable {
    public var shouldFailHealth: Bool = false
    public var shouldFailSummary: Bool = false
    public var shouldFailAskAgent: Bool = false
    public var shouldFailUpload: Bool = false
    public var shouldFailInsights: Bool = false

    public var uploadCallCount: Int = 0
    public var deleteStatementCallCount: Int = 0
    public var resetAllDataCallCount: Int = 0
    public var askAgentCallCount: Int = 0
    public var generateInsightsCallCount: Int = 0

    public init() {}

    public func fetchHealth() async throws -> Bool {
        if shouldFailHealth { throw APIError.networkError("Mock network offline") }
        return true
    }

    public func fetchFinancialSummary(statementId: String?) async throws -> FinancialSummary {
        if shouldFailSummary { throw APIError.serverError(statusCode: 500, message: "Internal Server Error") }
        return FinancialSummary(
            totalIncome: Decimal(string: "5000.00")!,
            totalExpenses: Decimal(string: "-1200.00")!,
            netCashFlow: Decimal(string: "3800.00")!,
            currency: "CAD",
            transactionCount: 1
        )
    }

    public func fetchCategorySpending(statementId: String?) async throws -> [CategorySpending] {
        [CategorySpending(category: "Food", amount: Decimal(string: "1200.00")!, percentage: 100.0, transactionCount: 1)]
    }

    public func fetchMonthlyTrends(statementId: String?) async throws -> [MonthlyTrend] {
        [MonthlyTrend(month: "2026-09", totalIncome: Decimal(string: "5000.00")!, totalExpenses: Decimal(string: "-1200.00")!, netCashFlow: Decimal(string: "3800.00")!)]
    }

    public func fetchRecurringItems(statementId: String?) async throws -> [RecurringItem] {
        [RecurringItem(merchant: "Netflix", category: "Entertainment", frequency: "monthly", expectedAmount: Decimal(string: "19.99")!, lastDate: Date(), nextExpectedDate: Date(), occurrenceCount: 3, confidence: 0.95, isSubscription: true, transactionIds: ["t1"])]
    }

    public func fetchUnusualTransactions(statementId: String?) async throws -> [UnusualTransaction] {
        [UnusualTransaction(transactionId: "u1", date: Date(), merchant: "Best Buy", amount: Decimal(string: "-899.00")!, category: "Shopping", anomalyType: "large_expense", reason: "Exceeds normal spending threshold", severity: "high")]
    }

    public func fetchTransactions(statementId: String?, limit: Int?) async throws -> [Transaction] {
        [
            Transaction(
                id: "mock_1",
                date: Date(),
                merchant: "Mock Mart",
                originalDescription: "MOCK MART",
                amount: Decimal(string: "-1200.00")!,
                currency: "CAD",
                transactionType: .expense,
                category: "Food"
            )
        ]
    }

    public func fetchStatements() async throws -> [Statement] {
        [Statement(id: "stmt_mock_1", filename: "september_checking.csv", fileFormat: .csv, status: .completed, periodStart: Date(), periodEnd: Date(), totalTransactions: 10)]
    }

    public func uploadStatement(data: Data, filename: String) async throws -> Statement {
        uploadCallCount += 1
        if shouldFailUpload { throw APIError.networkError("Upload timeout") }
        return Statement(id: "stmt_new_1", filename: filename, fileFormat: .csv, status: .completed, totalTransactions: 5)
    }

    public func deleteStatement(id: String) async throws {
        deleteStatementCallCount += 1
    }

    public func resetAllData() async throws -> DataResetResult {
        resetAllDataCallCount += 1
        return DataResetResult(
            status: "success",
            deletedStatements: 1,
            deletedTransactions: 1,
            deletedInsights: 1,
            deletedJobs: 1,
            message: "All data cleared",
            timestamp: "2026-10-04T22:30:00Z"
        )
    }

    public func fetchPrivacyInfo() async throws -> PrivacyPolicyInfo {
        PrivacyPolicyInfo(
            architecture: "Zero-Retention & In-Memory Extraction",
            bankCredentialsRequired: false,
            inMemoryPdfProcessing: true,
            unencryptedFilesStoredOnDisk: false,
            logRedactionEnabled: true,
            cascadeDeletionSupported: true,
            guarantee: "FinLens AI does not require, store, or transmit your online banking credentials."
        )
    }

    public func askAgent(message: String, history: [AgentHistoryItem]?) async throws -> AgentQueryResult {
        askAgentCallCount += 1
        if shouldFailAskAgent { throw APIError.networkError("Agent service unreachable") }
        return AgentQueryResult(
            response: "Mock agent answer: You spent $1200.00",
            toolCalls: [AgentToolCall(toolName: "get_spending_by_category", description: "Food")],
            grounded: true
        )
    }

    public func fetchInsights(statementId: String?) async throws -> [InsightItem] {
        [
            InsightItem(
                insightType: .positive,
                category: "cash_flow",
                title: "Positive Cash Flow: Saved $3,800.00",
                content: "You achieved a healthy net surplus of $3,800.00.",
                severity: .low,
                metric: "+76.0% Saved",
                supportingTransactions: [
                    SupportingTransaction(date: "2026-09-01", merchant: "Mock Mart", amount: Decimal(string: "-1200.00")!, category: "Food")
                ]
            )
        ]
    }

    public func generateInsights(statementId: String?) async throws -> [InsightItem] {
        generateInsightsCallCount += 1
        if shouldFailInsights { throw APIError.serverError(statusCode: 500, message: "Insight generation failed") }
        return try await fetchInsights(statementId: statementId)
    }

    public func fetchSystemMetrics() async throws -> SystemMetrics {
        SystemMetrics(
            uptimeSeconds: 120.0,
            system: SystemProcessMetrics(processId: 100, memoryRssMb: 45.2, cpuPercent: 1.5),
            http: HTTPTelemetryMetrics(
                totalRequests: 10,
                statusCodes: ["200": 10],
                topEndpoints: ["GET /health": 10],
                latencyMs: HTTPLatencyMetrics(avg: 5.0, p50: 4.5, p95: 8.0, p99: 9.0)
            ),
            documentAi: DocumentAIMetrics(
                statementsProcessed: 2,
                statementsFailed: 0,
                transactionsExtracted: 25,
                avgParsingDurationMs: 45.0
            ),
            agentAi: AgentAIMetrics(
                queriesTotal: 5,
                groundedTotal: 5,
                groundingRate: 100.0,
                avgQueryLatencyMs: 20.0,
                p95QueryLatencyMs: 25.0,
                toolExecutions: ["search_transactions": 5],
                toolErrors: [:]
            ),
            insights: InsightsMetrics(totalGenerated: 2, bySeverity: ["medium": 2])
        )
    }

    public func fetchAITraces(limit: Int?) async throws -> [AITraceRecord] {
        [
            AITraceRecord(
                traceId: "trace_mock_1",
                correlationId: "cid_mock_1",
                timestamp: "2026-10-04T22:30:00Z",
                query: "What is my spending?",
                durationMs: 15.0,
                grounded: true,
                toolSpans: [
                    ToolExecutionSpanDTO(
                        toolName: "get_spending_by_category",
                        outputSummary: "categories: Food",
                        durationMs: 15.0,
                        success: true,
                        errorMessage: nil
                    )
                ],
                responsePreview: "You spent $1,200 on Food."
            )
        ]
    }
}
