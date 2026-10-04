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
                // Header Banner (Prominent on Dashboard, Compact on other tabs)
                if tab == .dashboard {
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
                }

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
            .padding(.top)
            .padding(.bottom, 70)
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
    @Environment(AppViewModel.self) private var viewModel
    @State private var queryText: String = ""

    let samplePrompts = [
        "What is my spending by category?",
        "What recurring subscriptions do I have?",
        "Which transactions look unusual or unexpected?",
        "What was my total spending and income?"
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Label("FinLens AI Financial Assistant", systemImage: "sparkles")
                        .font(.headline)
                        .foregroundStyle(.primary)
                    Text("Grounded strictly in your bank statements using deterministic financial tools.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                if !viewModel.chatMessages.isEmpty {
                    Button("Clear", role: .destructive) {
                        viewModel.clearChat()
                    }
                    .font(.caption)
                    .buttonStyle(.bordered)
                }
            }

            // Quick Starter Prompts
            if viewModel.chatMessages.isEmpty {
                VStack(alignment: .leading, spacing: 10) {
                    Text("Quick Prompts")
                        .font(.subheadline.bold())
                        .foregroundStyle(.secondary)

                    ForEach(samplePrompts, id: \.self) { prompt in
                        Button {
                            Task {
                                await viewModel.sendChatMessage(prompt)
                            }
                        } label: {
                            HStack {
                                Image(systemName: "sparkles")
                                    .foregroundStyle(.tint)
                                Text(prompt)
                                    .font(.subheadline)
                                    .foregroundStyle(.primary)
                                Spacer()
                                Image(systemName: "arrow.up.circle.fill")
                                    .foregroundStyle(.tint.opacity(0.8))
                            }
                            .padding()
                            .background(RoundedRectangle(cornerRadius: 12).fill(Color.secondary.opacity(0.06)))
                        }
                        .buttonStyle(.plain)
                    }
                }
            } else {
                // Chat Stream
                VStack(spacing: 16) {
                    ForEach(viewModel.chatMessages) { message in
                        ChatMessageRow(message: message)
                    }

                    if viewModel.isAgentThinking {
                        HStack(spacing: 12) {
                            ProgressView()
                                .controlSize(.small)
                            Text("FinLens AI is executing financial tools...")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Spacer()
                        }
                        .padding()
                        .background(RoundedRectangle(cornerRadius: 12).fill(Color.secondary.opacity(0.05)))
                    }
                }
            }

            // Bottom Input Bar
            HStack(spacing: 8) {
                TextField("Ask about transactions, categories, subscriptions...", text: $queryText)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit {
                        submitCurrentQuery()
                    }

                Button {
                    submitCurrentQuery()
                } label: {
                    Image(systemName: "paperplane.fill")
                        .font(.body)
                }
                .buttonStyle(.borderedProminent)
                .disabled(queryText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isAgentThinking)
            }
            .padding(.top, 4)
        }
    }

    private func submitCurrentQuery() {
        let text = queryText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !viewModel.isAgentThinking else { return }
        queryText = ""
        Task {
            await viewModel.sendChatMessage(text)
        }
    }
}

// MARK: - Chat Message Row
struct ChatMessageRow: View {
    let message: ChatMessage

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            if message.role == .user {
                Spacer(minLength: 40)
                Text(message.content)
                    .font(.body)
                    .foregroundStyle(.white)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(RoundedRectangle(cornerRadius: 16).fill(Color.accentColor))
            } else {
                VStack(alignment: .leading, spacing: 8) {
                    // Header with Grounded Badge
                    HStack(spacing: 6) {
                        Image(systemName: "sparkles")
                            .foregroundStyle(.tint)
                        Text("FinLens AI")
                            .font(.caption.bold())

                        Spacer()

                        if message.isGrounded {
                            HStack(spacing: 4) {
                                Image(systemName: "checkmark.seal.fill")
                                    .foregroundStyle(.green)
                                Text("Grounded")
                                    .font(.caption2.bold())
                                    .foregroundStyle(.green)
                            }
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Capsule().fill(Color.green.opacity(0.12)))
                        }
                    }

                    // Tool Badges
                    if !message.toolCalls.isEmpty {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 6) {
                                ForEach(message.toolCalls) { tool in
                                    HStack(spacing: 4) {
                                        Image(systemName: tool.iconName)
                                            .font(.caption2)
                                        Text(tool.friendlyName)
                                            .font(.caption2.bold())
                                    }
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(Capsule().fill(Color.secondary.opacity(0.1)))
                                    .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }

                    // Message Content
                    Text(message.content)
                        .font(.body)
                        .foregroundStyle(.primary)
                        .textSelection(.enabled)
                }
                .padding(14)
                .background(RoundedRectangle(cornerRadius: 16).fill(Color.secondary.opacity(0.08)))
                Spacer(minLength: 40)
            }
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
