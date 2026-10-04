import SwiftUI
import FinLensCore

#if canImport(AppKit)
import AppKit
#endif
#if canImport(UIKit)
import UIKit
#endif

/// TransactionDetailView: A platform-native detail inspector view
/// Usable across macOS (Inspector pane), iPadOS (Detail column), and iOS (Navigation destination / Sheet)
struct TransactionDetailView: View {
    let transaction: Transaction
    @Environment(AppViewModel.self) private var viewModel
    @State private var copiedMerchantNotice: Bool = false
    @State private var copiedRawNotice: Bool = false

    private var isIncome: Bool {
        transaction.transactionType == .income || transaction.amount > 0
    }

    private var amountColor: Color {
        isIncome ? .green : .primary
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header: Merchant & Category
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text(transaction.merchant)
                            .font(.title2.bold())
                            .foregroundStyle(.primary)

                        Spacer()

                        Text(transaction.transactionType.rawValue.capitalized)
                            .font(.caption2.bold())
                            .foregroundStyle(isIncome ? .green : .secondary)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Capsule().fill((isIncome ? Color.green : Color.secondary).opacity(0.12)))
                    }

                    // Formatted Amount
                    Text(CurrencyFormatter.format(amount: transaction.amount, currencyCode: transaction.currency))
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundStyle(amountColor)
                        .contentTransition(.numericText())
                }
                .padding()
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 14).fill(Color.secondary.opacity(0.06)))

                // Quick Ask AI Action Banner
                Button {
                    viewModel.askAIAssistant(
                        prompt: "Tell me more about my transactions at \(transaction.merchant). How much have I spent there?"
                    )
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "sparkles")
                            .font(.headline)
                            .foregroundStyle(.white)
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Ask FinLens AI about this")
                                .font(.subheadline.bold())
                                .foregroundStyle(.white)
                            Text("Analyze spending patterns and history for \(transaction.merchant)")
                                .font(.caption2)
                                .foregroundStyle(.white.opacity(0.8))
                        }
                        Spacer()
                        Image(systemName: "arrow.right.circle.fill")
                            .font(.title3)
                            .foregroundStyle(.white.opacity(0.9))
                    }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(
                        LinearGradient(
                            colors: [Color.blue, Color.indigo],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Ask FinLens AI about \(transaction.merchant)")
                .accessibilityHint("Switches to the AI assistant to analyze this merchant")

                // Categorization & Normalization Audit
                VStack(alignment: .leading, spacing: 14) {
                    Label("Categorization & Audit", systemImage: "checkmark.shield.fill")
                        .font(.headline)
                        .foregroundStyle(.primary)

                    VStack(spacing: 12) {
                        DetailRow(
                            label: "Category",
                            value: transaction.category,
                            icon: "folder.fill"
                        )

                        if let subcat = transaction.subcategory, !subcat.isEmpty {
                            DetailRow(
                                label: "Subcategory",
                                value: subcat,
                                icon: "tag.fill"
                            )
                        }

                        DetailRow(
                            label: "Date",
                            value: transaction.date.formatted(date: .complete, time: .omitted),
                            icon: "calendar"
                        )

                        // Confidence Meter
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Label("Extraction Confidence", systemImage: "chart.bar.xaxis")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                Spacer()
                                Text("\(Int(transaction.confidence * 100))%")
                                    .font(.subheadline.monospacedDigit().bold())
                                    .foregroundStyle(transaction.confidence >= 0.9 ? Color.green : Color.orange)
                            }
                            ProgressView(value: transaction.confidence)
                                .tint(transaction.confidence >= 0.9 ? .green : .orange)
                        }
                    }
                    .padding()
                    .background(RoundedRectangle(cornerRadius: 12).fill(Color.secondary.opacity(0.05)))
                }

                // Ground Truth Statement Data
                VStack(alignment: .leading, spacing: 12) {
                    Label("Source Attribution", systemImage: "doc.text.magnifyingglass")
                        .font(.headline)
                        .foregroundStyle(.primary)

                    VStack(alignment: .leading, spacing: 10) {
                        Text("Original Statement Description:")
                            .font(.caption)
                            .foregroundStyle(.secondary)

                        HStack {
                            Text(transaction.originalDescription)
                                .font(.system(.body, design: .monospaced))
                                .foregroundStyle(.primary)
                                .textSelection(.enabled)

                            Spacer()

                            Button {
                                copyToClipboard(transaction.originalDescription)
                                copiedRawNotice = true
                                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                                    copiedRawNotice = false
                                }
                            } label: {
                                Image(systemName: copiedRawNotice ? "checkmark" : "doc.on.doc")
                                    .foregroundStyle(copiedRawNotice ? .green : .secondary)
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel("Copy original description")
                        }
                        .padding(10)
                        .background(RoundedRectangle(cornerRadius: 8).fill(Color.secondary.opacity(0.08)))

                        if let page = transaction.sourcePage {
                            DetailRow(label: "Document Page", value: "Page \(page)", icon: "book.pages.fill")
                        }

                        if let stmtId = transaction.statementId {
                            DetailRow(label: "Statement ID", value: String(stmtId.prefix(8)) + "...", icon: "tray.fill")
                        }
                    }
                    .padding()
                    .background(RoundedRectangle(cornerRadius: 12).fill(Color.secondary.opacity(0.05)))
                }

                // Copy Merchant Action
                Button {
                    copyToClipboard(transaction.merchant)
                    copiedMerchantNotice = true
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                        copiedMerchantNotice = false
                    }
                } label: {
                    HStack {
                        Image(systemName: copiedMerchantNotice ? "checkmark" : "doc.on.doc")
                        Text(copiedMerchantNotice ? "Merchant Name Copied" : "Copy Merchant Name")
                    }
                    .font(.subheadline.bold())
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(RoundedRectangle(cornerRadius: 10).fill(Color.secondary.opacity(0.1)))
                }
                .buttonStyle(.plain)
            }
            .padding()
        }
        .navigationTitle("Transaction")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
    }

    private func copyToClipboard(_ text: String) {
        #if os(macOS)
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)
        #elseif os(iOS)
        UIPasteboard.general.string = text
        let generator = UIImpactFeedbackGenerator(style: .light)
        generator.impactOccurred()
        #endif
    }
}

private struct DetailRow: View {
    let label: String
    let value: String
    let icon: String

    var body: some View {
        HStack {
            Label(label, systemImage: icon)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Spacer()
            Text(value)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.primary)
        }
    }
}
