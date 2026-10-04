import Foundation

/// Canonical Transaction Model
/// Represents a validated, normalized financial transaction in the FinLens AI ecosystem.
public struct Transaction: Identifiable, Sendable, Codable, Equatable, Hashable {
    public let id: String
    public let statementId: String?
    public let date: Date
    public let merchant: String
    public let originalDescription: String
    public let amount: Decimal
    public let currency: String
    public let transactionType: TransactionType
    public let category: String
    public let subcategory: String?
    public let confidence: Double
    public let sourcePage: Int?

    public init(
        id: String = UUID().uuidString,
        statementId: String? = nil,
        date: Date,
        merchant: String,
        originalDescription: String,
        amount: Decimal,
        currency: String = "CAD",
        transactionType: TransactionType,
        category: String,
        subcategory: String? = nil,
        confidence: Double = 1.0,
        sourcePage: Int? = nil
    ) {
        self.id = id
        self.statementId = statementId
        self.date = date
        self.merchant = merchant
        self.originalDescription = originalDescription
        self.amount = amount
        self.currency = currency
        self.transactionType = transactionType
        self.category = category
        self.subcategory = subcategory
        self.confidence = confidence
        self.sourcePage = sourcePage
    }
}

public enum TransactionType: String, Sendable, Codable, Equatable, Hashable, CaseIterable {
    case expense
    case income
    case transfer
}
