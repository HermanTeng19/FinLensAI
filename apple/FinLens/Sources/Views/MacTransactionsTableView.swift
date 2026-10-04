#if os(macOS)
import SwiftUI
import AppKit
import FinLensCore

/// MacTransactionsTableView: macOS-optimized Table component with multi-column sorting, selection, and context menus
struct MacTransactionsTableView: View {
    @Environment(AppViewModel.self) private var viewModel
    @Binding var selectedTransactionId: String?
    @Binding var isInspectorPresented: Bool

    @State private var searchText: String = ""
    @State private var selectedCategory: String = "All"
    @State private var sortOrder: [KeyPathComparator<Transaction>] = [
        .init(\.date, order: .reverse)
    ]

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

        return list.sorted(using: sortOrder)
    }

    var body: some View {
        VStack(spacing: 0) {
            // macOS Toolbar Filter Bar
            HStack(spacing: 12) {
                // Category Filter
                Picker("Category", selection: $selectedCategory) {
                    ForEach(availableCategories, id: \.self) { cat in
                        Text(cat).tag(cat)
                    }
                }
                .pickerStyle(.menu)
                .frame(width: 170)

                Spacer()

                // Quick Statistics
                Text("\(filteredTransactions.count) of \(viewModel.transactions.count) transactions")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
            .background(Color(NSColor.windowBackgroundColor))

            Divider()

            if filteredTransactions.isEmpty {
                if viewModel.transactions.isEmpty {
                    ContentUnavailableView(
                        "No Transactions Available",
                        systemImage: "list.bullet.rectangle.portrait",
                        description: Text("Import a PDF or CSV bank statement with ⌘O to populate transactions.")
                    )
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    ContentUnavailableView.search(text: searchText)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            } else {
                Table(filteredTransactions, selection: $selectedTransactionId, sortOrder: $sortOrder) {
                    // Date Column
                    TableColumn("Date", value: \.date) { txn in
                        Text(txn.date.formatted(date: .abbreviated, time: .omitted))
                            .font(.body.monospacedDigit())
                            .foregroundStyle(.secondary)
                    }
                    .width(min: 85, ideal: 100, max: 120)

                    // Merchant Column
                    TableColumn("Merchant", value: \.merchant) { txn in
                        HStack(spacing: 6) {
                            Text(txn.merchant)
                                .font(.body.weight(.medium))
                            if txn.confidence < 0.90 {
                                Image(systemName: "exclamationmark.circle.fill")
                                    .foregroundStyle(.orange)
                                    .font(.caption)
                                    .help("Lower extraction confidence (\(Int(txn.confidence * 100))%)")
                            }
                        }
                    }
                    .width(min: 130, ideal: 160)

                    // Category Column
                    TableColumn("Category", value: \.category) { txn in
                        Text(txn.category)
                            .font(.caption.weight(.medium))
                            .padding(.horizontal, 7)
                            .padding(.vertical, 2.5)
                            .background(Capsule().fill(Color.secondary.opacity(0.12)))
                    }
                    .width(min: 100, ideal: 120, max: 140)

                    // Original Statement Description Column
                    TableColumn("Original Description", value: \.originalDescription) { txn in
                        Text(txn.originalDescription)
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                    .width(min: 160, ideal: 240)

                    // Confidence Score
                    TableColumn("Confidence", value: \.confidence) { txn in
                        Text("\(Int(txn.confidence * 100))%")
                            .font(.caption2.monospacedDigit().bold())
                            .foregroundStyle(txn.confidence >= 0.9 ? Color.green : Color.orange)
                    }
                    .width(min: 75, ideal: 85, max: 95)

                    // Amount Column
                    TableColumn("Amount", value: \.amount) { txn in
                        Text(CurrencyFormatter.format(amount: txn.amount, currencyCode: txn.currency))
                            .font(.body.monospacedDigit().bold())
                            .foregroundStyle(txn.amount < 0 ? Color.primary : Color.green)
                            .frame(maxWidth: .infinity, alignment: .trailing)
                    }
                    .width(min: 100, ideal: 120, max: 140)
                }
                .contextMenu(forSelectionType: String.self) { selection in
                    if let id = selection.first, let txn = viewModel.transactions.first(where: { $0.id == id }) {
                        Button {
                            selectedTransactionId = id
                            isInspectorPresented = true
                        } label: {
                            Label("Inspect Transaction", systemImage: "info.circle")
                        }

                        Button {
                            copyText(txn.merchant)
                        } label: {
                            Label("Copy Merchant Name", systemImage: "doc.on.doc")
                        }

                        Button {
                            copyText(CurrencyFormatter.format(amount: txn.amount, currencyCode: txn.currency))
                        } label: {
                            Label("Copy Amount", systemImage: "dollarsign.circle")
                        }

                        Button {
                            copyText(txn.originalDescription)
                        } label: {
                            Label("Copy Raw Description", systemImage: "text.alignleft")
                        }

                        Divider()

                        Button {
                            viewModel.askAIAssistant(prompt: "Analyze my transactions for \(txn.merchant)")
                        } label: {
                            Label("Ask AI About \(txn.merchant)", systemImage: "sparkles")
                        }
                    }
                }
                .onChange(of: selectedTransactionId) { _, newValue in
                    if newValue != nil {
                        isInspectorPresented = true
                    }
                }
            }
        }
        .searchable(text: $searchText, placement: .toolbar, prompt: "Search merchant, category, or description (⌘F)")
    }

    private func copyText(_ text: String) {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)
    }
}
#endif
