import SwiftUI
import FinLensCore

struct TabSectionView: View {
    let tab: NavigationTab
    @Environment(AppViewModel.self) private var viewModel

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Header Banner
                VStack(spacing: 8) {
                    Image(systemName: "chart.line.uptrend.xyaxis.circle.fill")
                        .font(.system(size: 54))
                        .foregroundStyle(.tint)
                        .symbolRenderingMode(.hierarchical)
                        .padding(.top, 16)

                    Text(viewModel.appTitle)
                        .font(.largeTitle.bold())
                        .foregroundStyle(.primary)

                    Text(viewModel.appTagline)
                        .font(.headline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding()
                .frame(maxWidth: .infinity)
                .background(
                    RoundedRectangle(cornerRadius: 16)
                        .fill(Color.secondary.opacity(0.1))
                )
                .padding(.horizontal)

                // Current Section Content
                VStack(alignment: .leading, spacing: 16) {
                    HStack {
                        Label(tab.rawValue, systemImage: tab.systemImage)
                            .font(.title2.bold())
                        Spacer()
                    }

                    switch tab {
                    case .dashboard:
                        DashboardPlaceholderView()
                    case .transactions:
                        TransactionsPlaceholderView()
                    case .insights:
                        InsightsPlaceholderView()
                    case .askAI:
                        AskAIPlaceholderView()
                    case .profile:
                        ProfilePlaceholderView()
                    }
                }
                .padding(.horizontal)
            }
            .padding(.vertical)
        }
        .navigationTitle(tab.rawValue)
    }
}

// MARK: - Section Placeholders for Phase 1

struct DashboardPlaceholderView: View {
    @Environment(AppViewModel.self) private var viewModel

    var body: some View {
        VStack(spacing: 16) {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 160))], spacing: 16) {
                MetricCard(title: "Total Expenses", amount: Decimal(string: "-124.30")!, currency: "CAD", color: .red)
                MetricCard(title: "Total Income", amount: Decimal(string: "3200.00")!, currency: "CAD", color: .green)
                MetricCard(title: "Net Cash Flow", amount: Decimal(string: "3075.70")!, currency: "CAD", color: .blue)
            }

            VStack(alignment: .leading, spacing: 12) {
                Text("Recent Activity")
                    .font(.headline)

                ForEach(viewModel.recentTransactions) { txn in
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(txn.merchant)
                                .font(.body.weight(.medium))
                            Text(txn.category)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        Text(CurrencyFormatter.format(amount: txn.amount, currencyCode: txn.currency))
                            .font(.body.monospacedDigit())
                            .foregroundStyle(txn.amount < 0 ? Color.primary : Color.green)
                    }
                    .padding()
                    .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.08)))
                }
            }
            .padding(.top, 8)
        }
    }
}

struct MetricCard: View {
    let title: String
    let amount: Decimal
    let currency: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(CurrencyFormatter.format(amount: amount, currencyCode: currency))
                .font(.title3.bold().monospacedDigit())
                .contentTransition(.numericText())
                .foregroundStyle(color)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 12).fill(Color.secondary.opacity(0.08)))
    }
}

struct TransactionsPlaceholderView: View {
    @Environment(AppViewModel.self) private var viewModel

    var body: some View {
        ContentUnavailableView(
            "Transaction Stream",
            systemImage: "list.bullet.rectangle",
            description: Text("Upload a bank statement (PDF/CSV) to begin automated extraction and categorization.")
        )
        .padding(.vertical, 32)
    }
}

struct InsightsPlaceholderView: View {
    var body: some View {
        ContentUnavailableView(
            "AI Financial Insights",
            systemImage: "sparkles",
            description: Text("Spending trends, recurring charges, and anomalies will appear here once statements are processed.")
        )
        .padding(.vertical, 32)
    }
}

struct AskAIPlaceholderView: View {
    var body: some View {
        ContentUnavailableView(
            "Ask FinLens AI",
            systemImage: "bubble.left.and.bubble.right",
            description: Text("Ask grounded questions about your finances, such as 'How much did I spend on dining out last month?'")
        )
        .padding(.vertical, 32)
    }
}

struct ProfilePlaceholderView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Label("Privacy & Data Security", systemImage: "lock.shield")
                .font(.headline)
            Text("FinLens AI operates with zero bank password requirements. Your financial data is securely analyzed, with permanent deletion controls.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding()
        .background(RoundedRectangle(cornerRadius: 12).fill(Color.secondary.opacity(0.08)))
    }
}
