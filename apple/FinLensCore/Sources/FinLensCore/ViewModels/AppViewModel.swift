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

    // Network & UI Status
    public private(set) var isServerConnected: Bool = false
    public private(set) var isLoading: Bool = false
    public private(set) var isUploading: Bool = false
    public private(set) var errorMessage: String? = nil

    private let apiClient: any APIClientProtocol

    public init(apiClient: any APIClientProtocol = APIClient()) {
        self.apiClient = apiClient
        Task {
            await self.loadAllData()
        }
    }

    public func selectTab(_ tab: NavigationTab) {
        self.selectedTab = tab
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

                let (sum, cats, trends, rec, un, txns, stmts) = try await (
                    sumTask, catTask, trendTask, recTask, unTask, txnsTask, stmtsTask
                )

                self.summary = sum
                self.categorySpending = cats
                self.monthlyTrends = trends
                self.recurringItems = rec
                self.unusualTransactions = un
                self.transactions = txns
                self.statements = stmts
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
