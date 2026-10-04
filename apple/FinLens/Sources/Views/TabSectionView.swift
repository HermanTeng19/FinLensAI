import SwiftUI
import UniformTypeIdentifiers
import FinLensCore
#if canImport(UIKit)
import UIKit
#endif
#if canImport(AppKit)
import AppKit
#endif

typealias Transaction = FinLensCore.Transaction

/// Cross-platform clipboard helper with haptic feedback
@MainActor
struct PlatformClipboard {
    static func copy(_ text: String) {
        #if os(iOS)
        UIPasteboard.general.string = text
        let generator = UIImpactFeedbackGenerator(style: .medium)
        generator.prepare()
        generator.impactOccurred()
        #elseif os(macOS)
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)
        #endif
    }
}

struct TabSectionView: View {
    let tab: NavigationTab
    @Environment(AppViewModel.self) private var viewModel
    @State private var isShowingFileImporter: Bool = false

    var body: some View {
        Group {
            if tab == .transactions {
                TransactionsSectionView()
            } else {
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
                                EmptyView()
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
            }
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
                        NavigationLink(destination: TransactionDetailView(transaction: txn)) {
                            TransactionRowView(transaction: txn)
                                .padding(10)
                                .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))
                        }
                        .buttonStyle(.plain)
                        .contextMenu {
                            NavigationLink(destination: TransactionDetailView(transaction: txn)) {
                                Label("Inspect Details", systemImage: "info.circle")
                            }
                            Button {
                                PlatformClipboard.copy(txn.merchant)
                            } label: {
                                Label("Copy Merchant", systemImage: "doc.on.doc")
                            }
                            Button {
                                PlatformClipboard.copy(CurrencyFormatter.format(amount: txn.amount, currencyCode: txn.currency))
                            } label: {
                                Label("Copy Amount", systemImage: "dollarsign.circle")
                            }
                            Button {
                                let prompt = "Tell me more about my spending at \(txn.merchant) for \(CurrencyFormatter.format(amount: txn.amount, currencyCode: txn.currency))."
                                viewModel.askAIAssistant(prompt: prompt)
                            } label: {
                                Label("Ask FinLens AI", systemImage: "sparkles")
                            }
                        }
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
    @State private var selectedCategory: String = "All"

    private var availableCategories: [String] {
        let set = Set(viewModel.transactions.map { $0.category })
        return ["All"] + set.sorted()
    }

    var filteredTransactions: [Transaction] {
        var list = viewModel.transactions

        if selectedCategory != "All" {
            list = list.filter { $0.category == selectedCategory }
        }

        if !searchText.isEmpty {
            let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
            list = list.filter {
                $0.merchant.localizedCaseInsensitiveContains(query) ||
                $0.category.localizedCaseInsensitiveContains(query) ||
                $0.originalDescription.localizedCaseInsensitiveContains(query)
            }
        }

        return list
    }

    var body: some View {
        VStack(spacing: 0) {
            // Category Filter Pills
            if !viewModel.transactions.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(availableCategories, id: \.self) { cat in
                            Button {
                                selectedCategory = cat
                            } label: {
                                Text(cat)
                                    .font(.caption.weight(selectedCategory == cat ? .bold : .regular))
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 6)
                                    .background(
                                        Capsule()
                                            .fill(selectedCategory == cat ? Color.accentColor : Color.secondary.opacity(0.12))
                                    )
                                    .foregroundStyle(selectedCategory == cat ? Color.white : Color.primary)
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel("Filter by \(cat)")
                            .accessibilityAddTraits(selectedCategory == cat ? [.isSelected] : [])
                        }
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 8)
                }
                #if os(iOS)
                .background(Color(uiColor: .systemGroupedBackground))
                #else
                .background(Color.secondary.opacity(0.04))
                #endif
                Divider()
            }

            // Transaction List with Swipe Actions & Details
            if viewModel.transactions.isEmpty {
                ContentUnavailableView(
                    "No Transactions Yet",
                    systemImage: "list.bullet.rectangle",
                    description: Text("Upload a bank statement in Profile to view parsed transactions.")
                )
                .frame(maxHeight: .infinity)
            } else if filteredTransactions.isEmpty {
                ContentUnavailableView.search(text: searchText.isEmpty ? selectedCategory : searchText)
                    .frame(maxHeight: .infinity)
            } else {
                List {
                    ForEach(filteredTransactions) { txn in
                        NavigationLink(destination: TransactionDetailView(transaction: txn)) {
                            TransactionRowView(transaction: txn)
                        }
                        .swipeActions(edge: .leading, allowsFullSwipe: true) {
                            Button {
                                let prompt = "Analyze transaction: \(txn.merchant) on \(txn.date) for \(CurrencyFormatter.format(amount: txn.amount, currencyCode: txn.currency)). Is this recurring, unusual, or expected?"
                                viewModel.askAIAssistant(prompt: prompt)
                            } label: {
                                Label("Ask AI", systemImage: "sparkles")
                            }
                            .tint(.blue)
                        }
                        .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                            Button {
                                PlatformClipboard.copy(txn.merchant)
                            } label: {
                                Label("Copy Merchant", systemImage: "doc.on.doc")
                            }
                            .tint(.gray)

                            Button {
                                PlatformClipboard.copy(CurrencyFormatter.format(amount: txn.amount, currencyCode: txn.currency))
                            } label: {
                                Label("Copy Amount", systemImage: "dollarsign.circle")
                            }
                            .tint(.indigo)
                        }
                        .contextMenu {
                            NavigationLink(destination: TransactionDetailView(transaction: txn)) {
                                Label("Inspect Details", systemImage: "info.circle")
                            }
                            Button {
                                PlatformClipboard.copy(txn.merchant)
                            } label: {
                                Label("Copy Merchant", systemImage: "doc.on.doc")
                            }
                            Button {
                                PlatformClipboard.copy(CurrencyFormatter.format(amount: txn.amount, currencyCode: txn.currency))
                            } label: {
                                Label("Copy Amount", systemImage: "dollarsign.circle")
                            }
                            Button {
                                let prompt = "Tell me more about my transaction at \(txn.merchant) for \(CurrencyFormatter.format(amount: txn.amount, currencyCode: txn.currency))."
                                viewModel.askAIAssistant(prompt: prompt)
                            } label: {
                                Label("Ask FinLens AI", systemImage: "sparkles")
                            }
                        }
                    }
                }
                #if os(iOS)
                .listStyle(.insetGrouped)
                #else
                .listStyle(.inset(alternatesRowBackgrounds: true))
                #endif
            }
        }
        .searchable(text: $searchText, prompt: "Search merchant or category...")
    }
}

// MARK: - Insights Section
enum InsightFilter: String, CaseIterable, Identifiable {
    case all = "All"
    case warnings = "Warnings"
    case opportunities = "Opportunities"
    case observations = "Observations"

    var id: String { rawValue }
}

struct InsightsSectionView: View {
    @Environment(AppViewModel.self) private var viewModel
    @State private var selectedFilter: InsightFilter = .all

    var filteredInsights: [InsightItem] {
        switch selectedFilter {
        case .all:
            return viewModel.insights
        case .warnings:
            return viewModel.insights.filter { $0.insightType == .warning }
        case .opportunities:
            return viewModel.insights.filter { $0.insightType == .positive }
        case .observations:
            return viewModel.insights.filter { $0.insightType == .info }
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Header & Refresh Action
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Label("AI Financial Insights", systemImage: "sparkles")
                        .font(.headline)
                    Text("Deterministic attribution across cash flow, spikes, subscriptions, and anomalies.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Button {
                    Task {
                        await viewModel.refreshInsights()
                    }
                } label: {
                    HStack(spacing: 6) {
                        if viewModel.isGeneratingInsights {
                            ProgressView()
                                .controlSize(.small)
                        } else {
                            Image(systemName: "arrow.clockwise")
                        }
                        Text("Regenerate")
                            .font(.caption.bold())
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Capsule().fill(Color.blue.opacity(0.12)))
                    .foregroundStyle(.blue)
                }
                .buttonStyle(.plain)
                .disabled(viewModel.isGeneratingInsights)
            }

            // Stat Counter Pills
            let totalCount = viewModel.insights.count
            let warningCount = viewModel.insights.filter { $0.insightType == .warning }.count
            let oppCount = viewModel.insights.filter { $0.insightType == .positive }.count
            let supportingCount = viewModel.insights.reduce(0) { $0 + $1.supportingTransactions.count }

            LazyVGrid(columns: [GridItem(.adaptive(minimum: 140))], spacing: 10) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Total Insights")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                        Text("\(totalCount)")
                            .font(.title3.bold().monospacedDigit())
                    }
                    Spacer()
                    Image(systemName: "sparkles.rectangle.stack")
                        .foregroundStyle(.blue)
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))

                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Warnings")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                        Text("\(warningCount)")
                            .font(.title3.bold().monospacedDigit())
                            .foregroundStyle(warningCount > 0 ? Color.red : Color.primary)
                    }
                    Spacer()
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(warningCount > 0 ? Color.red : Color.secondary)
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))

                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Opportunities")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                        Text("\(oppCount)")
                            .font(.title3.bold().monospacedDigit())
                            .foregroundStyle(oppCount > 0 ? Color.green : Color.primary)
                    }
                    Spacer()
                    Image(systemName: "leaf.fill")
                        .foregroundStyle(oppCount > 0 ? Color.green : Color.secondary)
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))

                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Attributions")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                        Text("\(supportingCount)")
                            .font(.title3.bold().monospacedDigit())
                            .foregroundStyle(.blue)
                    }
                    Spacer()
                    Image(systemName: "checkmark.seal.fill")
                        .foregroundStyle(.blue)
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))
            }

            // Filter Segmented Control
            Picker("Filter Insights", selection: $selectedFilter) {
                ForEach(InsightFilter.allCases) { filter in
                    Text(filter.rawValue).tag(filter)
                }
            }
            .pickerStyle(.segmented)

            // Insights Card List
            if filteredInsights.isEmpty {
                ContentUnavailableView(
                    "No Insights In This Category",
                    systemImage: "sparkles",
                    description: Text(selectedFilter == .all ? "Upload statements or click Regenerate to compute AI insights." : "No \(selectedFilter.rawValue.lowercased()) generated for this period.")
                )
                .padding(.vertical, 20)
            } else {
                ForEach(Array(filteredInsights.enumerated()), id: \.element.id) { index, insight in
                    InsightCardView(insight: insight, initiallyExpanded: index == 0)
                }
            }
        }
    }
}

// MARK: - Insight Card View
struct InsightCardView: View {
    let insight: InsightItem
    @State private var isAttributionExpanded: Bool

    init(insight: InsightItem, initiallyExpanded: Bool = false) {
        self.insight = insight
        self._isAttributionExpanded = State(initialValue: initiallyExpanded)
    }

    private var typeColor: Color {
        switch insight.insightType {
        case .warning: return .red
        case .positive: return .green
        case .info: return .blue
        }
    }

    private var severityColor: Color {
        switch insight.severity {
        case .high: return .red
        case .medium: return .orange
        case .low: return .blue
        }
    }

    private var categoryDisplayName: String {
        switch insight.category {
        case "cash_flow": return "Cash Flow"
        case "spending_spike": return "Spending Spike"
        case "unusual_transaction": return "Anomaly"
        case "subscription": return "Subscription"
        case "large_purchase": return "Large Purchase"
        case "category_dominance": return "Concentration"
        default: return insight.category.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }

    private var categoryIcon: String {
        switch insight.category {
        case "cash_flow": return "banknote"
        case "spending_spike": return "chart.line.uptrend.xyaxis"
        case "unusual_transaction": return "exclamationmark.shield"
        case "subscription": return "arrow.triangle.2.circlepath"
        case "large_purchase": return "cart.fill"
        case "category_dominance": return "pie.chart.fill"
        default: return "sparkles"
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Card Header
            HStack(spacing: 8) {
                Label(categoryDisplayName, systemImage: categoryIcon)
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Capsule().fill(Color.secondary.opacity(0.10)))

                if let metric = insight.metric {
                    Text(metric)
                        .font(.caption2.monospacedDigit().bold())
                        .foregroundStyle(typeColor)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(Capsule().fill(typeColor.opacity(0.12)))
                }

                Spacer()

                Text(insight.severity.displayName.uppercased())
                    .font(.caption2.weight(.heavy))
                    .foregroundStyle(severityColor)
                    .padding(.horizontal, 7)
                    .padding(.vertical, 2.5)
                    .background(Capsule().fill(severityColor.opacity(0.12)))
            }

            // Title & Content
            VStack(alignment: .leading, spacing: 6) {
                Text(insight.title)
                    .font(.headline)
                    .foregroundStyle(.primary)

                Text(insight.content)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }

            // Grounded Attribution Section
            if !insight.supportingTransactions.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Button {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            isAttributionExpanded.toggle()
                        }
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "checkmark.seal.fill")
                                .foregroundStyle(.blue)
                            Text("Grounded in \(insight.supportingTransactions.count) supporting transaction\(insight.supportingTransactions.count > 1 ? "s" : "")")
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(.primary)
                            Spacer()
                            Image(systemName: isAttributionExpanded ? "chevron.up" : "chevron.down")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .buttonStyle(.plain)

                    if isAttributionExpanded {
                        VStack(spacing: 6) {
                            ForEach(insight.supportingTransactions) { txn in
                                HStack {
                                    VStack(alignment: .leading, spacing: 2) {
                                        HStack(spacing: 6) {
                                            Text(txn.merchant)
                                                .font(.caption.weight(.semibold))
                                                .foregroundStyle(.primary)
                                            Text(txn.category)
                                                .font(.caption2)
                                                .foregroundStyle(.secondary)
                                        }
                                        Text(txn.date)
                                            .font(.caption2.monospacedDigit())
                                            .foregroundStyle(.tertiary)
                                    }
                                    Spacer()
                                    Text(CurrencyFormatter.format(amount: txn.amount, currencyCode: "CAD"))
                                        .font(.caption.monospacedDigit().bold())
                                        .foregroundStyle(txn.amount < 0 ? Color.primary : Color.green)
                                }
                                .padding(8)
                                .background(RoundedRectangle(cornerRadius: 8).fill(Color.secondary.opacity(0.04)))
                            }
                        }
                        .transition(.opacity.combined(with: .move(edge: .top)))
                    }
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.05)))
            }
        }
        .padding(14)
        .background(RoundedRectangle(cornerRadius: 14).fill(Color.secondary.opacity(0.06)))
        .overlay(
            RoundedRectangle(cornerRadius: 14)
                .stroke(severityColor.opacity(0.20), lineWidth: 1)
        )
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
        .onAppear {
            consumePendingPrompt()
        }
        .onChange(of: viewModel.pendingPrompt) { _, newPrompt in
            if newPrompt != nil {
                consumePendingPrompt()
            }
        }
    }

    private func consumePendingPrompt() {
        guard let prompt = viewModel.pendingPrompt, !prompt.isEmpty else { return }
        viewModel.clearPendingPrompt()
        queryText = prompt
        submitCurrentQuery()
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

    @State private var statementToDelete: Statement? = nil
    @State private var isShowingDeleteStatementAlert: Bool = false
    @State private var isShowingResetConfirmation: Bool = false
    @State private var showResetSuccessBanner: Bool = false

    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
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
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Uploaded Statements")
                            .font(.headline)
                        Spacer()
                        Text("\(viewModel.statements.count) total")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

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
                                    if stmt.totalTransactions > 0 {
                                        Text("• \(stmt.totalTransactions) txns")
                                            .font(.caption2)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                            }
                            Spacer()
                            Button(role: .destructive) {
                                statementToDelete = stmt
                                isShowingDeleteStatementAlert = true
                            } label: {
                                Image(systemName: "trash")
                                    .foregroundStyle(.red)
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel("Delete statement \(stmt.filename)")
                        }
                        .padding()
                        .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.06)))
                    }
                }
            }

            // Privacy & Data Security Badges
            VStack(alignment: .leading, spacing: 12) {
                Label("Privacy & Security Architecture", systemImage: "lock.shield.fill")
                    .font(.headline)

                VStack(spacing: 10) {
                    PrivacyFeatureRow(
                        icon: "memorychip",
                        title: "In-Memory Parsing",
                        description: "Bank statement PDFs/CSVs are processed in-memory. Cleartext documents are never stored on disk."
                    )
                    PrivacyFeatureRow(
                        icon: "eye.slash.fill",
                        title: "Sensitive Data Redaction",
                        description: "Credit card PANs, Canadian SINs, and bank transit codes are automatically masked from all logs."
                    )
                    PrivacyFeatureRow(
                        icon: "arrow.triangle.2.circlepath",
                        title: "Cascade Deletion",
                        description: "Deleting a statement atomically purges all linked transactions, insights, and processing jobs."
                    )
                    PrivacyFeatureRow(
                        icon: "key.slash",
                        title: "Zero Bank Passwords",
                        description: "FinLens AI never requests, stores, or accesses your bank login credentials."
                    )
                }
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 12).fill(Color.secondary.opacity(0.06)))

            // Reset Confirmation Success Banner
            if showResetSuccessBanner, let result = viewModel.lastResetResult {
                HStack(spacing: 12) {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Data Reset Complete")
                            .font(.subheadline.bold())
                        Text("Purged \(result.deletedStatements) statements, \(result.deletedTransactions) transactions, and \(result.deletedInsights) insights.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Button {
                        showResetSuccessBanner = false
                    } label: {
                        Image(systemName: "xmark")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }
                .padding()
                .background(RoundedRectangle(cornerRadius: 10).fill(Color.green.opacity(0.12)))
            }

            // Danger Zone: Total Data Purge
            VStack(alignment: .leading, spacing: 12) {
                Label("Danger Zone", systemImage: "exclamationmark.triangle.fill")
                    .font(.headline)
                    .foregroundStyle(.red)

                Text("Permanently erase all uploaded statements, transactions, AI insights, and jobs. This operation is irreversible.")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Button(role: .destructive) {
                    isShowingResetConfirmation = true
                } label: {
                    HStack {
                        if viewModel.isResettingData {
                            ProgressView()
                                .controlSize(.small)
                                .padding(.trailing, 4)
                        } else {
                            Image(systemName: "trash.fill")
                        }
                        Text(viewModel.isResettingData ? "Erasing Financial Records..." : "Erase All Financial Data")
                            .bold()
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(RoundedRectangle(cornerRadius: 12).fill(Color.red.opacity(0.12)))
                    .foregroundStyle(.red)
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(Color.red.opacity(0.3), lineWidth: 1)
                    )
                }
                .disabled(viewModel.isResettingData)
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 12).fill(Color.red.opacity(0.04)))
        }
        // Confirmation alert for single statement deletion
        .confirmationDialog(
            "Delete Statement?",
            isPresented: $isShowingDeleteStatementAlert,
            titleVisibility: .visible,
            presenting: statementToDelete
        ) { stmt in
            Button("Delete Statement and Transactions", role: .destructive) {
                Task {
                    await viewModel.deleteStatement(id: stmt.id)
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: { stmt in
            Text("Are you sure you want to delete \"\(stmt.filename)\"? All transactions, insights, and jobs associated with this statement will be permanently erased.")
        }
        // Confirmation alert for total reset
        .alert("Erase All Financial Data?", isPresented: $isShowingResetConfirmation) {
            Button("Permanently Erase Everything", role: .destructive) {
                Task {
                    await viewModel.resetAllFinancialData()
                    showResetSuccessBanner = true
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will permanently and irreversibly wipe all uploaded statements, parsed transactions, AI insights, and category summaries. You cannot undo this action.")
        }
    }
}

// MARK: - Privacy Feature Row
struct PrivacyFeatureRow: View {
    let icon: String
    let title: String
    let description: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundStyle(Color.accentColor)
                .frame(width: 24)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline.weight(.semibold))
                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 2)
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
        .padding(.vertical, 2)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(transaction.merchant), \(transaction.category), \(CurrencyFormatter.format(amount: transaction.amount, currencyCode: transaction.currency)), on \(transaction.date.formatted(date: .abbreviated, time: .omitted))")
        .accessibilityHint("Double tap to inspect full transaction details.")
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
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(title): \(CurrencyFormatter.format(amount: amount, currencyCode: currency))")
    }
}
