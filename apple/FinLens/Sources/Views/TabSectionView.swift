import SwiftUI
import UniformTypeIdentifiers
import FinLensCore

typealias Transaction = FinLensCore.Transaction

struct TabSectionView: View {
    let tab: NavigationTab
    @Environment(AppViewModel.self) private var viewModel
    @State private var isShowingFileImporter: Bool = false

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Header Banner
                VStack(spacing: 8) {
                    Image(systemName: "chart.line.uptrend.xyaxis.circle.fill")
                        .font(.system(size: 48))
                        .foregroundStyle(.tint)
                        .symbolRenderingMode(.hierarchical)
                        .padding(.top, 8)

                    Text(viewModel.appTitle)
                        .font(.largeTitle.bold())
                        .foregroundStyle(.primary)

                    Text(viewModel.appTagline)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)

                    // Backend Connection Status Indicator
                    HStack(spacing: 6) {
                        Circle()
                            .fill(viewModel.isServerConnected ? Color.green : Color.orange)
                            .frame(width: 8, height: 8)
                        Text(viewModel.isServerConnected ? "Backend Online (FastAPI + PostgreSQL)" : "Offline Mode (Local Cache)")
                            .font(.caption2.bold())
                            .foregroundStyle(viewModel.isServerConnected ? .green : .secondary)
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(Capsule().fill(Color.secondary.opacity(0.1)))
                }
                .padding()
                .frame(maxWidth: .infinity)
                .background(
                    RoundedRectangle(cornerRadius: 16)
                        .fill(Color.secondary.opacity(0.08))
                )
                .padding(.horizontal)

                if let error = viewModel.errorMessage {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(.orange)
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.primary)
                        Spacer()
                        Button("Dismiss") {
                            viewModel.dismissError()
                        }
                        .font(.caption.bold())
                    }
                    .padding()
                    .background(RoundedRectangle(cornerRadius: 12).fill(Color.orange.opacity(0.12)))
                    .padding(.horizontal)
                }

                // Current Tab Content
                VStack(alignment: .leading, spacing: 16) {
                    switch tab {
                    case .dashboard:
                        DashboardSectionView()
                    case .transactions:
                        TransactionsSectionView()
                    case .insights:
                        InsightsSectionView()
                    case .askAI:
                        AskAISectionView()
                    case .profile:
                        ProfileSectionView(isShowingFileImporter: $isShowingFileImporter)
                    }
                }
                .padding(.horizontal)
            }
            .padding(.vertical)
        }
        .navigationTitle(tab.rawValue)
        .refreshable {
            await viewModel.refresh()
        }
        .fileImporter(
            isPresented: $isShowingFileImporter,
            allowedContentTypes: [.pdf, .commaSeparatedText],
            allowsMultipleSelection: false
        ) { result in
            handleFileSelection(result: result)
        }
    }

    private func handleFileSelection(result: Result<[URL], Error>) {
        guard case .success(let urls) = result, let fileUrl = urls.first else { return }
        guard fileUrl.startAccessingSecurityScopedResource() else { return }
        defer { fileUrl.stopAccessingSecurityScopedResource() }

        do {
            let data = try Data(contentsOf: fileUrl)
            let filename = fileUrl.lastPathComponent
            Task {
                await viewModel.uploadStatement(fileData: data, filename: filename)
            }
        } catch {
            // error handled through view model
        }
    }
}

// MARK: - Dashboard Section
struct DashboardSectionView: View {
    @Environment(AppViewModel.self) private var viewModel

    var body: some View {
        VStack(spacing: 20) {
            // Metric Cards
            let summary = viewModel.summary
            let income = summary?.totalIncome ?? Decimal.zero
            let expenses = summary?.totalExpenses ?? Decimal.zero
            let net = summary?.netCashFlow ?? Decimal.zero

            LazyVGrid(columns: [GridItem(.adaptive(minimum: 150))], spacing: 14) {
                MetricCard(title: "Total Expenses", amount: expenses, currency: "CAD", color: .red)
                MetricCard(title: "Total Income", amount: income, currency: "CAD", color: .green)
                MetricCard(title: "Net Cash Flow", amount: net, currency: "CAD", color: .blue)
            }

            // Spending by Category Breakdown
            if !viewModel.categorySpending.isEmpty {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Top Spending Categories")
                        .font(.headline)

                    ForEach(viewModel.categorySpending) { cat in
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(cat.category)
                                    .font(.subheadline.weight(.semibold))
                                Text("\(cat.percentage, specifier: "%.1f")% of total expenses")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            Text(CurrencyFormatter.format(amount: cat.amount, currencyCode: "CAD"))
                                .font(.subheadline.monospacedDigit().bold())
                        }
                        .padding(.vertical, 4)
                        Divider()
                    }
                }
                .padding()
                .background(RoundedRectangle(cornerRadius: 12).fill(Color.secondary.opacity(0.06)))
            }

            // Recent Transactions Preview
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("Recent Transactions")
                        .font(.headline)
                    Spacer()
                    Text("\(viewModel.transactions.count) total")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                if viewModel.transactions.isEmpty {
                    ContentUnavailableView(
                        "No Transactions Yet",
                        systemImage: "list.bullet.rectangle",
                        description: Text("Upload a bank statement in Profile to view parsed transactions.")
                    )
                } else {
                    ForEach(viewModel.transactions.prefix(5)) { txn in
                        TransactionRowView(transaction: txn)
                    }
                }
            }
        }
    }
}

// MARK: - Transactions Section
struct TransactionsSectionView: View {
    @Environment(AppViewModel.self) private var viewModel
    @State private var searchText: String = ""

    var filteredTransactions: [Transaction] {
        if searchText.isEmpty {
            return viewModel.transactions
        } else {
            return viewModel.transactions.filter {
                $0.merchant.localizedCaseInsensitiveContains(searchText) ||
                $0.category.localizedCaseInsensitiveContains(searchText) ||
                $0.originalDescription.localizedCaseInsensitiveContains(searchText)
            }
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            TextField("Search merchant or category...", text: $searchText)
                .textFieldStyle(.roundedBorder)
                .padding(.bottom, 4)

            if filteredTransactions.isEmpty {
                ContentUnavailableView.search(text: searchText)
            } else {
                ForEach(filteredTransactions) { txn in
                    TransactionRowView(transaction: txn)
                }
            }
        }
    }
}

// MARK: - Insights Section
struct InsightsSectionView: View {
    @Environment(AppViewModel.self) private var viewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Recurring Subscriptions
            VStack(alignment: .leading, spacing: 12) {
                Label("Recurring Subscriptions & Bills", systemImage: "arrow.triangle.2.circlepath")
                    .font(.headline)

                if viewModel.recurringItems.isEmpty {
                    Text("No recurring charges detected yet. Recurring charges like Netflix, utilities, or gym memberships will be detected automatically.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))
                } else {
                    ForEach(viewModel.recurringItems) { item in
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(item.merchant)
                                    .font(.subheadline.bold())
                                HStack(spacing: 8) {
                                    Text(item.frequency.capitalized)
                                        .font(.caption2.bold())
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2)
                                        .background(Capsule().fill(Color.blue.opacity(0.15)))
                                        .foregroundStyle(.blue)
                                    Text("\(item.occurrenceCount) charges")
                                        .font(.caption2)
                                        .foregroundStyle(.secondary)
                                }
                            }
                            Spacer()
                            Text(CurrencyFormatter.format(amount: item.expectedAmount, currencyCode: "CAD"))
                                .font(.body.monospacedDigit().bold())
                        }
                        .padding()
                        .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))
                    }
                }
            }

            // Unusual Transactions & Anomalies
            VStack(alignment: .leading, spacing: 12) {
                Label("Unusual Activity & Anomalies", systemImage: "exclamationmark.shield")
                    .font(.headline)

                if viewModel.unusualTransactions.isEmpty {
                    Text("No spending anomalies or duplicate charges detected.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))
                } else {
                    ForEach(viewModel.unusualTransactions) { alert in
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Text(alert.merchant)
                                    .font(.subheadline.bold())
                                Spacer()
                                Text(alert.severity.uppercased())
                                    .font(.caption2.bold())
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Capsule().fill(alert.severity == "high" ? Color.red.opacity(0.15) : Color.orange.opacity(0.15)))
                                    .foregroundStyle(alert.severity == "high" ? .red : .orange)
                            }
                            Text(alert.reason)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Text(CurrencyFormatter.format(amount: alert.amount, currencyCode: "CAD"))
                                .font(.caption.monospacedDigit().bold())
                                .foregroundStyle(.red)
                        }
                        .padding()
                        .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))
                    }
                }
            }
        }
    }
}

// MARK: - Ask AI Section
struct AskAISectionView: View {
    @State private var queryText: String = ""

    let samplePrompts = [
        "How much did I spend on dining out last month?",
        "What recurring subscriptions do I have?",
        "Which transactions look unusual or unexpected?",
        "Compare this month's spending with last month."
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Ask FinLens AI about your finances")
                .font(.headline)

            VStack(alignment: .leading, spacing: 8) {
                ForEach(samplePrompts, id: \.self) { prompt in
                    Button {
                        queryText = prompt
                    } label: {
                        HStack {
                            Image(systemName: "sparkles")
                                .foregroundStyle(.tint)
                            Text(prompt)
                                .font(.subheadline)
                                .foregroundStyle(.primary)
                            Spacer()
                        }
                        .padding()
                        .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))
                    }
                    .buttonStyle(.plain)
                }
            }

            HStack {
                TextField("Ask a question about your spending...", text: $queryText)
                    .textFieldStyle(.roundedBorder)
                Button("Ask") {
                    // Phase 8 integration
                }
                .buttonStyle(.borderedProminent)
            }
            .padding(.top, 8)
        }
    }
}

// MARK: - Profile & Statements Section
struct ProfileSectionView: View {
    @Environment(AppViewModel.self) private var viewModel
    @Binding var isShowingFileImporter: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Upload Statement CTA
            VStack(alignment: .leading, spacing: 10) {
                Label("Bank Statements (PDF / CSV)", systemImage: "doc.text")
                    .font(.headline)

                Button {
                    isShowingFileImporter = true
                } label: {
                    HStack {
                        Image(systemName: "arrow.up.doc.fill")
                        Text(viewModel.isUploading ? "Uploading & Analyzing..." : "Import Statement (PDF / CSV)")
                            .bold()
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(RoundedRectangle(cornerRadius: 12).fill(Color.accentColor))
                    .foregroundStyle(.white)
                }
                .disabled(viewModel.isUploading)
            }

            // Uploaded Statements List
            if !viewModel.statements.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Uploaded Statements")
                        .font(.subheadline.bold())

                    ForEach(viewModel.statements) { stmt in
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(stmt.filename)
                                    .font(.subheadline.weight(.semibold))
                                HStack(spacing: 8) {
                                    Text(stmt.fileFormat.rawValue.uppercased())
                                        .font(.caption2.bold())
                                        .foregroundStyle(.secondary)
                                    Text(stmt.status.rawValue.capitalized)
                                        .font(.caption2.bold())
                                        .foregroundStyle(stmt.status == .completed ? .green : .blue)
                                }
                            }
                            Spacer()
                            Button(role: .destructive) {
                                Task {
                                    await viewModel.deleteStatement(id: stmt.id)
                                }
                            } label: {
                                Image(systemName: "trash")
                                    .foregroundStyle(.red)
                            }
                            .buttonStyle(.plain)
                        }
                        .padding()
                        .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))
                    }
                }
            }

            // Privacy Assurance
            VStack(alignment: .leading, spacing: 8) {
                Label("Privacy & Data Security", systemImage: "lock.shield.fill")
                    .font(.headline)
                Text("FinLens AI operates with zero bank password requirements. All financial parsing and storage is deterministic, with permanent cascade deletion controls.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 12).fill(Color.secondary.opacity(0.08)))
        }
    }
}

// MARK: - Reusable Transaction Row
struct TransactionRowView: View {
    let transaction: Transaction

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(transaction.merchant)
                    .font(.body.weight(.medium))
                HStack(spacing: 6) {
                    Text(transaction.category)
                        .font(.caption2)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Capsule().fill(Color.secondary.opacity(0.12)))
                    Text(transaction.date.formatted(date: .abbreviated, time: .omitted))
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
            Spacer()
            Text(CurrencyFormatter.format(amount: transaction.amount, currencyCode: transaction.currency))
                .font(.body.monospacedDigit().bold())
                .foregroundStyle(transaction.amount < 0 ? Color.primary : Color.green)
        }
        .padding()
        .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))
    }
}

// MARK: - Metric Card
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
