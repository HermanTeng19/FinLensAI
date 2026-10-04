import Foundation
import Observation

/// Primary application-level ViewModel for FinLens AI
/// Uses Swift 6 Observation framework (`@Observable`) and runs on `@MainActor`.
@Observable
@MainActor
public final class AppViewModel {
    public private(set) var appTitle: String = "FinLens AI"
    public private(set) var appTagline: String = "Understand Your Spending with AI"
    public private(set) var recentTransactions: [Transaction] = []
    public private(set) var categories: [Category] = Category.defaults
    public var selectedTab: NavigationTab = .dashboard
    public private(set) var isLoading: Bool = false
    public private(set) var errorMessage: String? = nil

    public init() {
        loadInitialState()
    }

    public func selectTab(_ tab: NavigationTab) {
        self.selectedTab = tab
    }

    public func refresh() async {
        self.isLoading = true
        // Simulated deterministic load
        try? await Task.sleep(nanoseconds: 300_000_000)
        self.isLoading = false
    }

    private func loadInitialState() {
        // Sample seed data to ensure Phase 1 displays correctly
        self.recentTransactions = [
            Transaction(
                id: "sample_001",
                date: Date(),
                merchant: "Apple Store",
                originalDescription: "APPLE.COM/BILL",
                amount: Decimal(string: "-12.99") ?? -12.99,
                currency: "CAD",
                transactionType: .expense,
                category: "Shopping",
                subcategory: "Digital Services",
                confidence: 0.99
            )
        ]
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
