#if os(macOS)
import SwiftUI
import AppKit
import UniformTypeIdentifiers
import FinLensCore

/// MacRootView: Desktop-first experience for macOS with NavigationSplitView, native Table, Inspector drawer, and keyboard shortcuts
struct MacRootView: View {
    @Environment(AppViewModel.self) private var viewModel
    @State private var columnVisibility: NavigationSplitViewVisibility = .all
    @State private var selectedTransactionId: String? = nil
    @State private var isInspectorPresented: Bool = false
    @State private var isShowingFileImporter: Bool = false
    @State private var isTargetedForDrop: Bool = false

    private var selectedTransaction: Transaction? {
        guard let id = selectedTransactionId else { return nil }
        return viewModel.transactions.first(where: { $0.id == id })
    }

    var body: some View {
        @Bindable var vm = viewModel
        NavigationSplitView(columnVisibility: $columnVisibility) {
            // macOS Sidebar
            VStack(alignment: .leading, spacing: 0) {
                // Header Brand & Server Status
                HStack(spacing: 8) {
                    Image(systemName: "chart.line.uptrend.xyaxis.circle.fill")
                        .font(.title2)
                        .foregroundStyle(.tint)
                    VStack(alignment: .leading, spacing: 1) {
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

                // Sidebar Navigation Tabs
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

                // Sidebar Statements Summary
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
                                    .font(.caption)
                                Text(stmt.filename)
                                    .font(.caption2)
                                    .lineLimit(1)
                                    .truncationMode(.middle)
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

                // Import Button in Sidebar
                Button {
                    isShowingFileImporter = true
                } label: {
                    HStack {
                        Image(systemName: "plus.circle.fill")
                        Text("Import Statement")
                    }
                    .font(.caption.weight(.semibold))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                }
                .buttonStyle(.plain)
                .background(Color.secondary.opacity(0.06))
            }
            .navigationSplitViewColumnWidth(min: 220, ideal: 240, max: 280)
        } detail: {
            // Main Content Area
            Group {
                if vm.selectedTab == .transactions {
                    MacTransactionsTableView(
                        selectedTransactionId: $selectedTransactionId,
                        isInspectorPresented: $isInspectorPresented
                    )
                } else {
                    TabSectionView(tab: vm.selectedTab)
                }
            }
            .navigationTitle(vm.selectedTab.rawValue)
            .toolbar {
                ToolbarItemGroup(placement: .primaryAction) {
                    // Import Statement
                    Button {
                        isShowingFileImporter = true
                    } label: {
                        Label("Import Statement", systemImage: "square.and.arrow.down")
                    }
                    .keyboardShortcut("o", modifiers: .command)
                    .help("Import Statement (⌘O)")

                    // Refresh
                    Button {
                        Task {
                            await vm.refresh()
                        }
                    } label: {
                        Label("Refresh", systemImage: "arrow.clockwise")
                    }
                    .keyboardShortcut("r", modifiers: .command)
                    .help("Refresh All Data (⌘R)")

                    // Inspector Toggle
                    Button {
                        withAnimation {
                            isInspectorPresented.toggle()
                        }
                    } label: {
                        Label("Toggle Inspector", systemImage: "sidebar.trailing")
                    }
                    .keyboardShortcut("i", modifiers: [.command, .option])
                    .help("Toggle Inspector (⌥⌘I)")
                }
            }
            .inspector(isPresented: $isInspectorPresented) {
                if let txn = selectedTransaction {
                    TransactionDetailView(transaction: txn)
                        .inspectorColumnWidth(min: 280, ideal: 320, max: 400)
                } else {
                    ContentUnavailableView(
                        "No Transaction Selected",
                        systemImage: "doc.text.magnifyingglass",
                        description: Text("Select a transaction from the table to inspect details.")
                    )
                    .inspectorColumnWidth(min: 280, ideal: 320, max: 400)
                }
            }
        }
        .frame(minWidth: 850, minHeight: 560)
        .fileImporter(
            isPresented: $isShowingFileImporter,
            allowedContentTypes: [.pdf, .commaSeparatedText]
        ) { result in
            handleFileImport(result: result)
        }
        .dropDestination(for: URL.self) { urls, _ in
            guard let url = urls.first else { return false }
            handleDroppedURL(url)
            return true
        } isTargeted: { targeted in
            isTargetedForDrop = targeted
        }
        .overlay {
            if isTargetedForDrop {
                ZStack {
                    Color.blue.opacity(0.15)
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color.blue, style: StrokeStyle(lineWidth: 3, dash: [8]))
                        .padding(16)
                    VStack(spacing: 8) {
                        Image(systemName: "arrow.down.doc.fill")
                            .font(.system(size: 40))
                            .foregroundStyle(.blue)
                        Text("Drop PDF or CSV to Import Statement")
                            .font(.headline)
                            .foregroundStyle(.blue)
                    }
                }
                .allowsHitTesting(false)
            }
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
        case .failure(let error):
            Task { @MainActor in
                // Set error message
            }
            _ = error
        }
    }

    private func handleDroppedURL(_ url: URL) {
        if let data = try? Data(contentsOf: url) {
            Task {
                await viewModel.uploadStatement(fileData: data, filename: url.lastPathComponent)
            }
        }
    }
}
#endif
