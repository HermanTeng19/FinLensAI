#if os(iOS)
import SwiftUI
import UniformTypeIdentifiers
import FinLensCore

/// iPadRootView: Adaptive 3-Column NavigationSplitView designed specifically for iPadOS
/// Sidebar: Navigation & Statements | Content: Primary Lists | Detail: Inspectors & AI Assistant
struct iPadRootView: View {
    @Environment(AppViewModel.self) private var viewModel
    @State private var columnVisibility: NavigationSplitViewVisibility = .all
    @State private var selectedTransactionId: String? = nil
    @State private var isShowingFileImporter: Bool = false

    private var selectedTransaction: Transaction? {
        guard let id = selectedTransactionId else { return nil }
        return viewModel.transactions.first(where: { $0.id == id })
    }

    var body: some View {
        @Bindable var vm = viewModel
        NavigationSplitView(columnVisibility: $columnVisibility) {
            // MARK: - 1. Sidebar Column
            VStack(alignment: .leading, spacing: 0) {
                // Header
                HStack(spacing: 8) {
                    Image(systemName: "chart.line.uptrend.xyaxis.circle.fill")
                        .font(.title2)
                        .foregroundStyle(.tint)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(vm.appTitle)
                            .font(.headline)
                        HStack(spacing: 4) {
                            Circle()
                                .fill(vm.isServerConnected ? Color.green : Color.orange)
                                .frame(width: 6, height: 6)
                            Text(vm.isServerConnected ? "Connected" : "Offline")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 14)

                Divider()

                // Navigation Tabs
                List(NavigationTab.allCases, selection: Binding(
                    get: { vm.selectedTab },
                    set: { if let newTab = $0 { vm.selectTab(newTab) } }
                )) { tab in
                    HStack {
                        Label(tab.rawValue, systemImage: tab.systemImage)
                        Spacer()
                        tabBadge(for: tab)
                    }
                    .tag(tab)
                }
                .listStyle(.sidebar)

                Divider()

                // Statements Section
                if !vm.statements.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Statements (\(vm.statements.count))")
                            .font(.caption2.bold())
                            .foregroundStyle(.secondary)
                            .padding(.horizontal, 16)
                            .padding(.top, 8)

                        ForEach(vm.statements.prefix(3)) { stmt in
                            HStack(spacing: 6) {
                                Image(systemName: stmt.fileFormat == .pdf ? "doc.richtext" : "tablecells")
                                    .foregroundStyle(.secondary)
                                    .font(.caption2)
                                Text(stmt.filename)
                                    .font(.caption2)
                                    .lineLimit(1)
                                Spacer()
                                Text("\(stmt.totalTransactions)")
                                    .font(.caption2.monospacedDigit())
                                    .foregroundStyle(.tertiary)
                            }
                            .padding(.horizontal, 16)
                            .padding(.vertical, 2)
                        }
                    }
                    .padding(.bottom, 8)
                }

                // Import Action
                Button {
                    isShowingFileImporter = true
                } label: {
                    HStack {
                        Image(systemName: "plus.circle.fill")
                        Text("Import Statement")
                    }
                    .font(.subheadline.weight(.semibold))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                }
                .buttonStyle(.plain)
                .background(Color.secondary.opacity(0.06))
            }
            .navigationSplitViewColumnWidth(min: 220, ideal: 250, max: 280)
        } content: {
            // MARK: - 2. Content Column
            NavigationStack {
                Group {
                    switch vm.selectedTab {
                    case .dashboard:
                        ScrollView {
                            DashboardSectionView()
                                .padding()
                        }
                    case .transactions:
                        iPadTransactionsListView(selectedTransactionId: $selectedTransactionId)
                    case .insights:
                        ScrollView {
                            InsightsSectionView()
                                .padding()
                        }
                    case .askAI:
                        ScrollView {
                            AskAISectionView()
                                .padding()
                        }
                    case .profile:
                        ScrollView {
                            ProfileSectionView(isShowingFileImporter: $isShowingFileImporter)
                                .padding()
                        }
                    }
                }
                .navigationTitle(vm.selectedTab.rawValue)
                .toolbar {
                    ToolbarItemGroup(placement: .topBarTrailing) {
                        Button {
                            Task {
                                await vm.refresh()
                            }
                        } label: {
                            Image(systemName: "arrow.clockwise")
                        }
                        .help("Refresh (⌘R)")

                        Button {
                            isShowingFileImporter = true
                        } label: {
                            Image(systemName: "square.and.arrow.down")
                        }
                        .help("Import Statement (⌘O)")
                    }
                }
            }
            .navigationSplitViewColumnWidth(min: 320, ideal: 380, max: 480)
        } detail: {
            // MARK: - 3. Detail Column
            NavigationStack {
                if let txn = selectedTransaction {
                    TransactionDetailView(transaction: txn)
                } else if vm.selectedTab == .askAI {
                    // When on Ask AI, the detail panel can show full conversation
                    AskAISectionView()
                        .padding()
                } else {
                    ContentUnavailableView(
                        "No Selection",
                        systemImage: "sidebar.right",
                        description: Text("Select a transaction or item from the list to inspect details.")
                    )
                }
            }
        }
        .fileImporter(
            isPresented: $isShowingFileImporter,
            allowedContentTypes: [.pdf, .commaSeparatedText]
        ) { result in
            handleFileImport(result: result)
        }
    }

    @ViewBuilder
    private func tabBadge(for tab: NavigationTab) -> some View {
        switch tab {
        case .transactions:
            if !viewModel.transactions.isEmpty {
                Text("\(viewModel.transactions.count)")
                    .font(.caption2.monospacedDigit())
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 1.5)
                    .background(Capsule().fill(Color.secondary.opacity(0.12)))
            }
        case .insights:
            let warningCount = viewModel.insights.filter { $0.insightType == .warning }.count
            if warningCount > 0 {
                Text("\(warningCount)")
                    .font(.caption2.bold())
                    .foregroundStyle(.white)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 1.5)
                    .background(Capsule().fill(Color.red))
            }
        default:
            EmptyView()
        }
    }

    private func handleFileImport(result: Result<URL, Error>) {
        switch result {
        case .success(let url):
            guard url.startAccessingSecurityScopedResource() else { return }
            defer { url.stopAccessingSecurityScopedResource() }
            if let data = try? Data(contentsOf: url) {
                Task {
                    await viewModel.uploadStatement(fileData: data, filename: url.lastPathComponent)
                }
            }
        case .failure:
            break
        }
    }
}

/// iPad-optimized Transactions List with Category Chips and Row Selection
private struct iPadTransactionsListView: View {
    @Environment(AppViewModel.self) private var viewModel
    @Binding var selectedTransactionId: String?
    @State private var searchText: String = ""
    @State private var selectedCategory: String = "All"

    private var availableCategories: [String] {
        let cats = Set(viewModel.transactions.map { $0.category })
        return ["All"] + cats.sorted()
    }

    private var filteredTransactions: [Transaction] {
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
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(availableCategories, id: \.self) { cat in
                        Button {
                            selectedCategory = cat
                        } label: {
                            Text(cat)
                                .font(.caption.weight(selectedCategory == cat ? .bold : .regular))
                                .padding(.horizontal, 10)
                                .padding(.vertical, 5)
                                .background(
                                    Capsule()
                                        .fill(selectedCategory == cat ? Color.blue : Color.secondary.opacity(0.12))
                                )
                                .foregroundStyle(selectedCategory == cat ? Color.white : Color.primary)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal)
                .padding(.vertical, 8)
            }
            .background(Color(uiColor: .systemGroupedBackground))

            Divider()

            if filteredTransactions.isEmpty {
                ContentUnavailableView.search(text: searchText)
            } else {
                List(filteredTransactions, selection: $selectedTransactionId) { txn in
                    HStack {
                        VStack(alignment: .leading, spacing: 3) {
                            Text(txn.merchant)
                                .font(.body.weight(.medium))
                            HStack(spacing: 6) {
                                Text(txn.category)
                                    .font(.caption2)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Capsule().fill(Color.secondary.opacity(0.12)))
                                Text(txn.date.formatted(date: .abbreviated, time: .omitted))
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        Spacer()
                        Text(CurrencyFormatter.format(amount: txn.amount, currencyCode: txn.currency))
                            .font(.body.monospacedDigit().bold())
                            .foregroundStyle(txn.amount < 0 ? Color.primary : Color.green)
                    }
                    .tag(txn.id)
                    .contentShape(Rectangle())
                    .onTapGesture {
                        selectedTransactionId = txn.id
                    }
                }
                .listStyle(.insetGrouped)
            }
        }
        .searchable(text: $searchText, prompt: "Search transactions...")
    }
}
#endif
