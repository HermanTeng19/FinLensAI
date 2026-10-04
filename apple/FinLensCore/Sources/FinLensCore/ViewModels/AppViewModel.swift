import Foundation
import Observation

/// Primary application-level ViewModel for FinLens AI
/// Uses Swift 6 Observation framework (`@Observable`) and runs on `@MainActor`.
@Observable
@MainActor
public final class AppViewModel {
    public private(set) var appTitle: String = "FinLens AI"
    public private(set) var appTagline: String = "Understand Your Spending with AI"
    public var selectedTab: NavigationTab = .dashboard

    // Financial Data State
    public private(set) var summary: FinancialSummary? = nil
    public private(set) var transactions: [Transaction] = []
    public private(set) var categorySpending: [CategorySpending] = []
    public private(set) var monthlyTrends: [MonthlyTrend] = []
    public private(set) var recurringItems: [RecurringItem] = []
    public private(set) var unusualTransactions: [UnusualTransaction] = []
    public private(set) var statements: [Statement] = []

    // AI Insights State
    public private(set) var insights: [InsightItem] = []
    public private(set) var isGeneratingInsights: Bool = false

    // Agent Chat State

    public private(set) var chatMessages: [ChatMessage] = []
    public private(set) var isAgentThinking: Bool = false
    public private(set) var lastToolCalls: [AgentToolCall] = []

    // Privacy & Data Management State
    public private(set) var privacyInfo: PrivacyPolicyInfo? = nil
    public private(set) var lastResetResult: DataResetResult? = nil
    public private(set) var isResettingData: Bool = false

    // User Navigation & Interaction State
    public var pendingPrompt: String? = nil
    public var isShowingFileImporter: Bool = false
    public var selectedTransactionId: String? = nil

    // Network & UI Status
    public private(set) var isServerConnected: Bool = false
    public private(set) var isLoading: Bool = false
    public private(set) var isUploading: Bool = false
    public private(set) var errorMessage: String? = nil


    private let apiClient: any APIClientProtocol

    public init(apiClient: any APIClientProtocol = APIClient(), initialTab: NavigationTab = .dashboard) {
        self.apiClient = apiClient
        self.selectedTab = initialTab
        Task {
            await self.loadAllData()
        }
    }


    public func selectTab(_ tab: NavigationTab) {
        self.selectedTab = tab
    }

    public func selectTransaction(id: String?) {
        self.selectedTransactionId = id
    }

    public func askAIAssistant(prompt: String) {
        self.pendingPrompt = prompt
        self.selectTab(.askAI)
    }

    public func clearPendingPrompt() {
        self.pendingPrompt = nil
    }

    public func dismissError() {
        self.errorMessage = nil
    }

    public func refresh() async {
        await loadAllData()
    }

    public func loadAllData() async {
        self.isLoading = true
        self.errorMessage = nil

        do {
            self.isServerConnected = try await apiClient.fetchHealth()
            if self.isServerConnected {
                async let sumTask = apiClient.fetchFinancialSummary(statementId: nil)
                async let catTask = apiClient.fetchCategorySpending(statementId: nil)
                async let trendTask = apiClient.fetchMonthlyTrends(statementId: nil)
                async let recTask = apiClient.fetchRecurringItems(statementId: nil)
                async let unTask = apiClient.fetchUnusualTransactions(statementId: nil)
                async let txnsTask = apiClient.fetchTransactions(statementId: nil, limit: 100)
                async let stmtsTask = apiClient.fetchStatements()
                async let insTask = apiClient.fetchInsights(statementId: nil)
                async let privTask = apiClient.fetchPrivacyInfo()

                let (sum, cats, trends, rec, un, txns, stmts, ins, priv) = try await (
                    sumTask, catTask, trendTask, recTask, unTask, txnsTask, stmtsTask, insTask, privTask
                )

                self.summary = sum
                self.categorySpending = cats
                self.monthlyTrends = trends
                self.recurringItems = rec
                self.unusualTransactions = un
                self.transactions = txns
                self.statements = stmts
                self.insights = ins
                self.privacyInfo = priv
            } else {
                self.loadOfflineSampleData()
            }
        } catch {
            self.errorMessage = error.localizedDescription
            self.loadOfflineSampleData()
        }

        self.isLoading = false
    }

    public func uploadStatement(fileData: Data, filename: String) async {
        self.isUploading = true
        self.errorMessage = nil

        do {
            _ = try await apiClient.uploadStatement(data: fileData, filename: filename)
            await loadAllData()
        } catch {
            self.errorMessage = error.localizedDescription
        }

        self.isUploading = false
    }

    public func deleteStatement(id: String) async {
        self.isLoading = true
        self.errorMessage = nil

        do {
            try await apiClient.deleteStatement(id: id)
            await loadAllData()
        } catch {
            self.errorMessage = error.localizedDescription
        }

        self.isLoading = false
    }

    public func resetAllFinancialData() async {
        self.isResettingData = true
        self.errorMessage = nil

        do {
            if isServerConnected {
                let result = try await apiClient.resetAllData()
                self.lastResetResult = result
            }
            // Clear all local in-memory records
            self.statements.removeAll()
            self.transactions.removeAll()
            self.categorySpending.removeAll()
            self.monthlyTrends.removeAll()
            self.recurringItems.removeAll()
            self.unusualTransactions.removeAll()
            self.insights.removeAll()
            self.chatMessages.removeAll()
            self.lastToolCalls.removeAll()
            self.summary = nil
        } catch {
            self.errorMessage = error.localizedDescription
        }

        self.isResettingData = false
    }

    public func fetchPrivacyInfo() async {
        guard isServerConnected else { return }
        do {
            self.privacyInfo = try await apiClient.fetchPrivacyInfo()
        } catch {
            // Non-fatal
        }
    }

    public func sendChatMessage(_ messageText: String) async {
        let trimmed = messageText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        let userMsg = ChatMessage(role: .user, content: trimmed)
        self.chatMessages.append(userMsg)
        self.isAgentThinking = true

        do {
            let history = self.chatMessages.dropLast().map {
                AgentHistoryItem(role: $0.role.rawValue, content: $0.content)
            }
            let response = try await apiClient.askAgent(message: trimmed, history: history)
            let assistantMsg = ChatMessage(
                role: .assistant,
                content: response.response,
                toolCalls: response.toolCalls,
                isGrounded: response.grounded
            )
            self.chatMessages.append(assistantMsg)
            self.lastToolCalls = response.toolCalls
        } catch {
            let fallbackMsg = ChatMessage(
                role: .assistant,
                content: "FinLens AI couldn't process your request: \(error.localizedDescription)",
                toolCalls: [],
                isGrounded: false
            )
            self.chatMessages.append(fallbackMsg)
        }

        self.isAgentThinking = false
    }

    public func clearChat() {
        self.chatMessages.removeAll()
        self.lastToolCalls.removeAll()
    }

    public func loadInsights(statementId: UUID? = nil) async {
        guard isServerConnected else { return }
        do {
            self.insights = try await apiClient.fetchInsights(statementId: statementId?.uuidString)
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    public func refreshInsights(statementId: UUID? = nil) async {
        guard isServerConnected else { return }
        self.isGeneratingInsights = true
        do {
            self.insights = try await apiClient.generateInsights(statementId: statementId?.uuidString)
        } catch {
            self.errorMessage = error.localizedDescription
        }
        self.isGeneratingInsights = false
    }


    private func loadOfflineSampleData() {
        if self.transactions.isEmpty {
            self.summary = FinancialSummary(
                totalIncome: Decimal(string: "3200.00") ?? 3200.00,
                totalExpenses: Decimal(string: "-124.30") ?? -124.30,
                netCashFlow: Decimal(string: "3075.70") ?? 3075.70,
                currency: "CAD",
                transactionCount: 2
            )
            self.transactions = [
                Transaction(
                    id: "sample_001",
                    date: Date(),
                    merchant: "Amazon",
                    originalDescription: "AMZN Mktp CA*9812487",
                    amount: Decimal(string: "-124.30") ?? -124.30,
                    currency: "CAD",
                    transactionType: .expense,
                    category: "Shopping",
                    subcategory: "Online Shopping",
                    confidence: 0.99
                ),
                Transaction(
                    id: "sample_002",
                    date: Date(),
                    merchant: "Payroll",
                    originalDescription: "EMPLOYER DIRECT DEP",
                    amount: Decimal(string: "3200.00") ?? 3200.00,
                    currency: "CAD",
                    transactionType: .income,
                    category: "Income",
                    subcategory: "Salary",
                    confidence: 0.99
                ),
            ]
            self.categorySpending = [
                CategorySpending(
                    category: "Shopping",
                    amount: Decimal(string: "124.30") ?? 124.30,
                    percentage: 100.0,
                    transactionCount: 1
                )
            ]
            self.insights = [
                InsightItem(
                    id: UUID(),
                    statementId: nil,
                    insightType: .positive,
                    category: "cash_flow",
                    title: "Positive Net Cash Flow",
                    content: "Your net savings rate for the period is 96.1%. Total income ($3,200.00) comfortably exceeded total expenses ($124.30).",
                    severity: .low,
                    metric: "+96.1%",
                    supportingTransactions: [
                        SupportingTransaction(
                            id: UUID(),
                            date: "2026-09-30",
                            merchant: "Payroll",
                            amount: Decimal(string: "3200.00") ?? 3200.00,
                            category: "Income"
                        ),
                        SupportingTransaction(
                            id: UUID(),
                            date: "2026-09-28",
                            merchant: "Amazon",
                            amount: Decimal(string: "-124.30") ?? -124.30,
                            category: "Shopping"
                        )
                    ],
                    metadata: [:],
                    generatedAt: "2026-10-04T12:00:00Z"
                )
            ]
        }
    }
}

public enum NavigationTab: String, Sendable, CaseIterable, Identifiable {
    case dashboard = "Dashboard"
    case transactions = "Transactions"
    case insights = "Insights"
    case askAI = "Ask AI"
    case profile = "Profile"

    public var id: String { rawValue }

    public var systemImage: String {
        switch self {
        case .dashboard: return "square.grid.2x2"
        case .transactions: return "list.bullet.rectangle"
        case .insights: return "sparkles"
        case .askAI: return "bubble.left.and.bubble.right"
        case .profile: return "person.crop.circle"
        }
    }
}
