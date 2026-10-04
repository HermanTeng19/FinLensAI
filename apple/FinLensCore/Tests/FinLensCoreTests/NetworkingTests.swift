import XCTest
@testable import FinLensCore

final class NetworkingTests: XCTestCase {
    func testTransactionJSONDecoding() throws {
        let json = """
        {
            "id": "11111111-2222-3333-4444-555555555555",
            "statement_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "date": "2026-09-18",
            "merchant": "Amazon",
            "original_description": "AMZN Mktp CA*9812487",
            "amount": "-124.30",
            "currency": "CAD",
            "transaction_type": "expense",
            "category": "Shopping",
            "subcategory": "Online Shopping",
            "confidence": 0.98,
            "source_page": 1
        }
        """.data(using: .utf8)!

        let decoder = FinLensJSONDecoder.makeStandard()
        let txn = try decoder.decode(Transaction.self, from: json)

        XCTAssertEqual(txn.id, "11111111-2222-3333-4444-555555555555")
        XCTAssertEqual(txn.merchant, "Amazon")
        XCTAssertEqual(txn.amount, Decimal(string: "-124.30")!)
        XCTAssertEqual(txn.transactionType, .expense)
        XCTAssertEqual(txn.category, "Shopping")
    }

    func testFinancialSummaryJSONDecoding() throws {
        let json = """
        {
            "total_income": "3500.00",
            "total_expenses": "-189.50",
            "net_cash_flow": "3310.50",
            "currency": "CAD",
            "transaction_count": 5
        }
        """.data(using: .utf8)!

        let decoder = FinLensJSONDecoder.makeStandard()
        let summary = try decoder.decode(FinancialSummary.self, from: json)

        XCTAssertEqual(summary.totalIncome, Decimal(string: "3500.00")!)
        XCTAssertEqual(summary.totalExpenses, Decimal(string: "-189.50")!)
        XCTAssertEqual(summary.netCashFlow, Decimal(string: "3310.50")!)
        XCTAssertEqual(summary.transactionCount, 5)
    }

    func testRecurringItemJSONDecoding() throws {
        let json = """
        {
            "merchant": "Netflix",
            "category": "Entertainment",
            "frequency": "monthly",
            "expected_amount": "16.99",
            "last_date": "2026-08-15",
            "next_expected_date": "2026-09-15",
            "occurrence_count": 3,
            "confidence": 0.98,
            "is_subscription": true,
            "transaction_ids": ["11111111-2222-3333-4444-555555555555"]
        }
        """.data(using: .utf8)!

        let decoder = FinLensJSONDecoder.makeStandard()
        let item = try decoder.decode(RecurringItem.self, from: json)

        XCTAssertEqual(item.merchant, "Netflix")
        XCTAssertEqual(item.frequency, "monthly")
        XCTAssertEqual(item.expectedAmount, Decimal(string: "16.99")!)
        XCTAssertTrue(item.isSubscription)
    }

    func testUnusualTransactionJSONDecoding() throws {
        let json = """
        {
            "transaction_id": "22222222-3333-4444-5555-666666666666",
            "date": "2026-08-20",
            "merchant": "Bistro Paris",
            "amount": "-68.50",
            "category": "Food",
            "anomaly_type": "duplicate_charge",
            "reason": "Potential duplicate charge",
            "severity": "high"
        }
        """.data(using: .utf8)!

        let decoder = FinLensJSONDecoder.makeStandard()
        let unusual = try decoder.decode(UnusualTransaction.self, from: json)

        XCTAssertEqual(unusual.merchant, "Bistro Paris")
        XCTAssertEqual(unusual.anomalyType, "duplicate_charge")
        XCTAssertEqual(unusual.severity, "high")
    }

    func testAgentQueryResponseDecoding() throws {
        let json = """
        {
            "response": "You spent $450.00 on groceries this month.",
            "tool_calls": [
                {
                    "tool_name": "get_spending_by_category",
                    "arguments": { "category": "Food" },
                    "output": { "total": "450.00" }
                }
            ],
            "grounded": true
        }
        """.data(using: .utf8)!

        let decoder = FinLensJSONDecoder.makeStandard()
        let dto = try decoder.decode(AgentResponseDTO.self, from: json)
        XCTAssertEqual(dto.response, "You spent $450.00 on groceries this month.")
        XCTAssertEqual(dto.toolCalls.count, 1)
        XCTAssertEqual(dto.toolCalls[0].toolName, "get_spending_by_category")
        XCTAssertTrue(dto.grounded)
    }

    @MainActor
    func testAppViewModelWithMockAPIClient() async {
        let mockClient = MockAPIClient()
        let vm = AppViewModel(apiClient: mockClient)

        await vm.loadAllData()

        XCTAssertTrue(vm.isServerConnected)
        XCTAssertEqual(vm.summary?.totalIncome, Decimal(string: "5000.00")!)
        XCTAssertEqual(vm.transactions.count, 1)
        XCTAssertEqual(vm.categorySpending.count, 1)

        await vm.sendChatMessage("What is my spending?")
        XCTAssertEqual(vm.chatMessages.count, 2)
        XCTAssertEqual(vm.chatMessages[0].role, .user)
        XCTAssertEqual(vm.chatMessages[1].role, .assistant)
        XCTAssertEqual(vm.chatMessages[1].content, "Mock agent answer: You spent $1200.00")
        XCTAssertEqual(vm.lastToolCalls.count, 1)
        XCTAssertEqual(vm.lastToolCalls[0].friendlyName, "Category Breakdown")
    }
}

// MARK: - Mock API Client for Testing
final class MockAPIClient: APIClientProtocol, Sendable {
    func fetchHealth() async throws -> Bool { true }
    func fetchFinancialSummary(statementId: String?) async throws -> FinancialSummary {
        FinancialSummary(
            totalIncome: Decimal(string: "5000.00")!,
            totalExpenses: Decimal(string: "-1200.00")!,
            netCashFlow: Decimal(string: "3800.00")!,
            currency: "CAD",
            transactionCount: 1
        )
    }
    func fetchCategorySpending(statementId: String?) async throws -> [CategorySpending] {
        [CategorySpending(category: "Food", amount: Decimal(string: "1200.00")!, percentage: 100.0, transactionCount: 1)]
    }
    func fetchMonthlyTrends(statementId: String?) async throws -> [MonthlyTrend] { [] }
    func fetchRecurringItems(statementId: String?) async throws -> [RecurringItem] { [] }
    func fetchUnusualTransactions(statementId: String?) async throws -> [UnusualTransaction] { [] }
    func fetchTransactions(statementId: String?, limit: Int?) async throws -> [Transaction] {
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
    func fetchStatements() async throws -> [Statement] { [] }
    func uploadStatement(data: Data, filename: String) async throws -> Statement {
        Statement(filename: filename, fileFormat: .csv)
    }
    func deleteStatement(id: String) async throws {}
    func resetAllData() async throws -> DataResetResult {
        DataResetResult(
            status: "success",
            deletedStatements: 1,
            deletedTransactions: 1,
            deletedInsights: 1,
            deletedJobs: 1,
            message: "All data cleared",
            timestamp: "2026-10-04T22:30:00Z"
        )
    }
    func fetchPrivacyInfo() async throws -> PrivacyPolicyInfo {
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
    func askAgent(message: String, history: [AgentHistoryItem]?) async throws -> AgentQueryResult {
        AgentQueryResult(
            response: "Mock agent answer: You spent $1200.00",
            toolCalls: [AgentToolCall(toolName: "get_spending_by_category", description: "Food")],
            grounded: true
        )
    }
    func fetchInsights(statementId: String?) async throws -> [InsightItem] {
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
    func generateInsights(statementId: String?) async throws -> [InsightItem] {
        try await fetchInsights(statementId: statementId)
    }
}

extension NetworkingTests {
    func testInsightJSONDecoding() throws {
        let json = """
        {
            "insights": [
                {
                    "id": "11111111-2222-3333-4444-555555555555",
                    "statement_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "insight_type": "warning",
                    "category": "spending_spike",
                    "title": "Food Spending Increased by 35%",
                    "content": "Spending in Food rose sharply.",
                    "severity": "medium",
                    "metric": "+35.0%",
                    "supporting_transactions": [
                        {
                            "id": "22222222-3333-4444-5555-666666666666",
                            "date": "2026-09-15",
                            "merchant": "Safeway",
                            "amount": "-150.00",
                            "category": "Food"
                        }
                    ],
                    "metadata": {
                        "category": "Food"
                    },
                    "generated_at": "2026-10-04T22:00:00Z"
                }
            ],
            "total_count": 1,
            "warning_count": 1,
            "positive_count": 0,
            "info_count": 0
        }
        """.data(using: .utf8)!

        let decoder = FinLensJSONDecoder.makeStandard()
        let res = try decoder.decode(InsightListResponse.self, from: json)

        XCTAssertEqual(res.totalCount, 1)
        XCTAssertEqual(res.warningCount, 1)
        XCTAssertEqual(res.insights.count, 1)

        let insight = res.insights[0]
        XCTAssertEqual(insight.insightType, .warning)
        XCTAssertEqual(insight.category, "spending_spike")
        XCTAssertEqual(insight.metric, "+35.0%")
        XCTAssertEqual(insight.supportingTransactions.count, 1)
        XCTAssertEqual(insight.supportingTransactions[0].merchant, "Safeway")
        XCTAssertEqual(insight.supportingTransactions[0].amount, Decimal(string: "-150.00")!)
    }

    func testDataResetResultDecoding() throws {
        let json = """
        {
            "status": "success",
            "deleted_statements": 3,
            "deleted_transactions": 45,
            "deleted_insights": 6,
            "deleted_jobs": 3,
            "message": "All financial records purged.",
            "timestamp": "2026-10-04T22:30:00Z"
        }
        """.data(using: .utf8)!

        let decoder = FinLensJSONDecoder.makeStandard()
        let result = try decoder.decode(DataResetResult.self, from: json)
        XCTAssertEqual(result.status, "success")
        XCTAssertEqual(result.deletedStatements, 3)
        XCTAssertEqual(result.deletedTransactions, 45)
        XCTAssertEqual(result.deletedInsights, 6)
        XCTAssertEqual(result.deletedJobs, 3)
    }

    func testPrivacyPolicyInfoDecoding() throws {
        let json = """
        {
            "architecture": "Zero-Retention & In-Memory Extraction",
            "bank_credentials_required": false,
            "in_memory_pdf_processing": true,
            "unencrypted_files_stored_on_disk": false,
            "log_redaction_enabled": true,
            "cascade_deletion_supported": true,
            "guarantee": "FinLens AI does not store credentials."
        }
        """.data(using: .utf8)!

        let decoder = FinLensJSONDecoder.makeStandard()
        let info = try decoder.decode(PrivacyPolicyInfo.self, from: json)
        XCTAssertEqual(info.bankCredentialsRequired, false)
        XCTAssertEqual(info.inMemoryPdfProcessing, true)
        XCTAssertEqual(info.cascadeDeletionSupported, true)
    }

    @MainActor
    func testAppViewModelResetData() async {
        let mock = MockAPIClient()
        let vm = AppViewModel(apiClient: mock)
        await vm.loadAllData()

        XCTAssertFalse(vm.transactions.isEmpty)
        XCTAssertFalse(vm.insights.isEmpty)

        await vm.resetAllFinancialData()

        XCTAssertTrue(vm.transactions.isEmpty)
        XCTAssertTrue(vm.insights.isEmpty)
        XCTAssertTrue(vm.statements.isEmpty)
        XCTAssertNil(vm.summary)
        XCTAssertEqual(vm.lastResetResult?.status, "success")
    }
}

