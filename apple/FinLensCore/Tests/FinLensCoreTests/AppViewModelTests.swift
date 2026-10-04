import XCTest
@testable import FinLensCore

@MainActor
final class AppViewModelTests: XCTestCase {

    func testViewModelInitializationAndDefaults() {
        let mock = MockAPIClient()
        let vm = AppViewModel(apiClient: mock, initialTab: .dashboard)

        XCTAssertEqual(vm.appTitle, "FinLens AI")
        XCTAssertEqual(vm.appTagline, "Understand Your Spending with AI")
        XCTAssertEqual(vm.selectedTab, .dashboard)
        XCTAssertFalse(vm.isGeneratingInsights)
        XCTAssertFalse(vm.isAgentThinking)
        XCTAssertFalse(vm.isResettingData)
        XCTAssertNil(vm.errorMessage)
    }

    func testNavigationTabSwitching() {
        let mock = MockAPIClient()
        let vm = AppViewModel(apiClient: mock)

        vm.selectTab(.transactions)
        XCTAssertEqual(vm.selectedTab, .transactions)

        vm.selectTab(.insights)
        XCTAssertEqual(vm.selectedTab, .insights)

        vm.selectTab(.askAI)
        XCTAssertEqual(vm.selectedTab, .askAI)

        vm.selectTab(.profile)
        XCTAssertEqual(vm.selectedTab, .profile)

        vm.selectTab(.dashboard)
        XCTAssertEqual(vm.selectedTab, .dashboard)
    }

    func testLoadAllDataSuccess() async {
        let mock = MockAPIClient()
        let vm = AppViewModel(apiClient: mock)

        await vm.loadAllData()

        XCTAssertTrue(vm.isServerConnected)
        XCTAssertNotNil(vm.summary)
        XCTAssertEqual(vm.summary?.totalIncome, Decimal(string: "5000.00")!)
        XCTAssertEqual(vm.summary?.totalExpenses, Decimal(string: "-1200.00")!)
        XCTAssertEqual(vm.transactions.count, 1)
        XCTAssertEqual(vm.categorySpending.count, 1)
        XCTAssertEqual(vm.monthlyTrends.count, 1)
        XCTAssertEqual(vm.recurringItems.count, 1)
        XCTAssertEqual(vm.unusualTransactions.count, 1)
        XCTAssertEqual(vm.statements.count, 1)
        XCTAssertEqual(vm.insights.count, 1)
        XCTAssertNil(vm.errorMessage)
    }

    func testLoadAllDataFailureSetsErrorMessage() async {
        let mock = MockAPIClient()
        mock.shouldFailHealth = true
        let vm = AppViewModel(apiClient: mock)

        await vm.loadAllData()

        XCTAssertFalse(vm.isServerConnected)
        XCTAssertNotNil(vm.errorMessage)
    }

    func testSendChatMessageFlowAndToolTracking() async {
        let mock = MockAPIClient()
        let vm = AppViewModel(apiClient: mock)

        await vm.sendChatMessage("What is my food spending?")

        XCTAssertEqual(vm.chatMessages.count, 2)
        XCTAssertEqual(vm.chatMessages[0].role, .user)
        XCTAssertEqual(vm.chatMessages[0].content, "What is my food spending?")
        XCTAssertEqual(vm.chatMessages[1].role, .assistant)
        XCTAssertEqual(vm.chatMessages[1].content, "Mock agent answer: You spent $1200.00")
        XCTAssertFalse(vm.isAgentThinking)
        XCTAssertEqual(vm.lastToolCalls.count, 1)
        XCTAssertEqual(vm.lastToolCalls[0].toolName, "get_spending_by_category")
        XCTAssertEqual(mock.askAgentCallCount, 1)
    }

    func testSendChatMessageEmptyDoesNotTriggerCall() async {
        let mock = MockAPIClient()
        let vm = AppViewModel(apiClient: mock)

        await vm.sendChatMessage("   ")
        XCTAssertEqual(vm.chatMessages.count, 0)
        XCTAssertEqual(mock.askAgentCallCount, 0)
    }

    func testSendChatMessageFailureSetsError() async {
        let mock = MockAPIClient()
        mock.shouldFailAskAgent = true
        let vm = AppViewModel(apiClient: mock)

        await vm.sendChatMessage("Show me subscriptions")

        XCTAssertFalse(vm.isAgentThinking)
        XCTAssertEqual(vm.chatMessages.count, 2)
        XCTAssertTrue(vm.chatMessages.last?.content.contains("Agent service unreachable") == true)
    }

    func testGenerateInsightsSuccess() async {
        let mock = MockAPIClient()
        let vm = AppViewModel(apiClient: mock)
        await vm.loadAllData()

        await vm.refreshInsights()

        XCTAssertFalse(vm.isGeneratingInsights)
        XCTAssertFalse(vm.insights.isEmpty)
        XCTAssertEqual(mock.generateInsightsCallCount, 1)
    }

    func testGenerateInsightsFailureSetsError() async {
        let mock = MockAPIClient()
        let vm = AppViewModel(apiClient: mock)
        await vm.loadAllData()
        mock.shouldFailInsights = true

        await vm.refreshInsights()

        XCTAssertFalse(vm.isGeneratingInsights)
        XCTAssertNotNil(vm.errorMessage)
    }

    func testDeleteStatementWorkflow() async {
        let mock = MockAPIClient()
        let vm = AppViewModel(apiClient: mock)
        await vm.loadAllData()

        await vm.deleteStatement(id: "stmt_mock_1")

        XCTAssertEqual(mock.deleteStatementCallCount, 1)
        XCTAssertNil(vm.errorMessage)
    }

    func testUploadStatementWorkflow() async {
        let mock = MockAPIClient()
        let vm = AppViewModel(apiClient: mock)

        let dummyData = "Date,Description,Amount\n2026-09-01,AMZN,-50.00".data(using: .utf8)!
        await vm.uploadStatement(fileData: dummyData, filename: "sept.csv")

        XCTAssertEqual(mock.uploadCallCount, 1)
        XCTAssertFalse(vm.isUploading)
        XCTAssertNil(vm.errorMessage)
    }

    func testUploadStatementFailureSetsError() async {
        let mock = MockAPIClient()
        mock.shouldFailUpload = true
        let vm = AppViewModel(apiClient: mock)

        let dummyData = "Date,Description,Amount\n2026-09-01,AMZN,-50.00".data(using: .utf8)!
        await vm.uploadStatement(fileData: dummyData, filename: "sept.csv")

        XCTAssertEqual(mock.uploadCallCount, 1)
        XCTAssertFalse(vm.isUploading)
        XCTAssertNotNil(vm.errorMessage)
        XCTAssertTrue(vm.errorMessage?.contains("Upload timeout") == true)
    }

    func testDismissError() async {
        let mock = MockAPIClient()
        mock.shouldFailHealth = true
        let vm = AppViewModel(apiClient: mock)

        await vm.loadAllData()
        XCTAssertNotNil(vm.errorMessage)

        vm.dismissError()
        XCTAssertNil(vm.errorMessage)
    }

    func testResetAllFinancialData() async {
        let mock = MockAPIClient()
        let vm = AppViewModel(apiClient: mock)
        await vm.loadAllData()

        XCTAssertNotNil(vm.summary)
        XCTAssertFalse(vm.transactions.isEmpty)

        await vm.resetAllFinancialData()

        XCTAssertEqual(mock.resetAllDataCallCount, 1)
        XCTAssertNil(vm.summary)
        XCTAssertTrue(vm.transactions.isEmpty)
        XCTAssertTrue(vm.insights.isEmpty)
        XCTAssertTrue(vm.statements.isEmpty)
        XCTAssertEqual(vm.lastResetResult?.status, "success")
    }
}
