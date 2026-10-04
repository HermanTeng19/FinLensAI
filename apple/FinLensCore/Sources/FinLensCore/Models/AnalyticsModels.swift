import Foundation

/// Deterministic financial summary matching backend /analytics/summary
public struct FinancialSummary: Sendable, Codable, Equatable {
    public let totalIncome: Decimal
    public let totalExpenses: Decimal
    public let netCashFlow: Decimal
    public let currency: String
    public let transactionCount: Int

    public init(
        totalIncome: Decimal,
        totalExpenses: Decimal,
        netCashFlow: Decimal,
        currency: String = "CAD",
        transactionCount: Int
    ) {
        self.totalIncome = totalIncome
        self.totalExpenses = totalExpenses
        self.netCashFlow = netCashFlow
        self.currency = currency
        self.transactionCount = transactionCount
    }

    private enum CodingKeys: String, CodingKey {
        case totalIncome
        case totalExpenses
        case netCashFlow
        case currency
        case transactionCount
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.totalIncome = try container.decodeFlexibleDecimal(forKey: .totalIncome)
        self.totalExpenses = try container.decodeFlexibleDecimal(forKey: .totalExpenses)
        self.netCashFlow = try container.decodeFlexibleDecimal(forKey: .netCashFlow)
        self.currency = try container.decodeIfPresent(String.self, forKey: .currency) ?? "CAD"
        self.transactionCount = try container.decode(Int.self, forKey: .transactionCount)
    }
}

/// Spending aggregated per category
public struct CategorySpending: Identifiable, Sendable, Codable, Equatable {
    public var id: String { category }
    public let category: String
    public let amount: Decimal
    public let percentage: Double
    public let transactionCount: Int

    public init(
        category: String,
        amount: Decimal,
        percentage: Double,
        transactionCount: Int
    ) {
        self.category = category
        self.amount = amount
        self.percentage = percentage
        self.transactionCount = transactionCount
    }

    private enum CodingKeys: String, CodingKey {
        case category
        case amount
        case percentage
        case transactionCount
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.category = try container.decode(String.self, forKey: .category)
        self.amount = try container.decodeFlexibleDecimal(forKey: .amount)
        self.percentage = try container.decode(Double.self, forKey: .percentage)
        self.transactionCount = try container.decode(Int.self, forKey: .transactionCount)
    }
}

/// Monthly cash flow trend
public struct MonthlyTrend: Identifiable, Sendable, Codable, Equatable {
    public var id: String { month }
    public let month: String
    public let totalIncome: Decimal
    public let totalExpenses: Decimal
    public let netCashFlow: Decimal

    public init(
        month: String,
        totalIncome: Decimal,
        totalExpenses: Decimal,
        netCashFlow: Decimal
    ) {
        self.month = month
        self.totalIncome = totalIncome
        self.totalExpenses = totalExpenses
        self.netCashFlow = netCashFlow
    }

    private enum CodingKeys: String, CodingKey {
        case month
        case totalIncome
        case totalExpenses
        case netCashFlow
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.month = try container.decode(String.self, forKey: .month)
        self.totalIncome = try container.decodeFlexibleDecimal(forKey: .totalIncome)
        self.totalExpenses = try container.decodeFlexibleDecimal(forKey: .totalExpenses)
        self.netCashFlow = try container.decodeFlexibleDecimal(forKey: .netCashFlow)
    }
}

/// Detected periodic charge or subscription
public struct RecurringItem: Identifiable, Sendable, Codable, Equatable {
    public var id: String { "\(merchant)_\(frequency)" }
    public let merchant: String
    public let category: String
    public let frequency: String
    public let expectedAmount: Decimal
    public let lastDate: Date
    public let nextExpectedDate: Date?
    public let occurrenceCount: Int
    public let confidence: Double
    public let isSubscription: Bool
    public let transactionIds: [String]

    public init(
        merchant: String,
        category: String,
        frequency: String,
        expectedAmount: Decimal,
        lastDate: Date,
        nextExpectedDate: Date? = nil,
        occurrenceCount: Int,
        confidence: Double,
        isSubscription: Bool = false,
        transactionIds: [String] = []
    ) {
        self.merchant = merchant
        self.category = category
        self.frequency = frequency
        self.expectedAmount = expectedAmount
        self.lastDate = lastDate
        self.nextExpectedDate = nextExpectedDate
        self.occurrenceCount = occurrenceCount
        self.confidence = confidence
        self.isSubscription = isSubscription
        self.transactionIds = transactionIds
    }

    private enum CodingKeys: String, CodingKey {
        case merchant
        case category
        case frequency
        case expectedAmount
        case lastDate
        case nextExpectedDate
        case occurrenceCount
        case confidence
        case isSubscription
        case transactionIds
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.merchant = try container.decode(String.self, forKey: .merchant)
        self.category = try container.decode(String.self, forKey: .category)
        self.frequency = try container.decode(String.self, forKey: .frequency)
        self.expectedAmount = try container.decodeFlexibleDecimal(forKey: .expectedAmount)
        self.lastDate = try container.decode(Date.self, forKey: .lastDate)
        self.nextExpectedDate = try container.decodeIfPresent(Date.self, forKey: .nextExpectedDate)
        self.occurrenceCount = try container.decode(Int.self, forKey: .occurrenceCount)
        self.confidence = try container.decode(Double.self, forKey: .confidence)
        self.isSubscription = try container.decodeIfPresent(Bool.self, forKey: .isSubscription) ?? false
        self.transactionIds = try container.decodeIfPresent([String].self, forKey: .transactionIds) ?? []
    }
}

/// Detected anomaly or unusual spending
public struct UnusualTransaction: Identifiable, Sendable, Codable, Equatable {
    public var id: String { transactionId }
    public let transactionId: String
    public let date: Date
    public let merchant: String
    public let amount: Decimal
    public let category: String
    public let anomalyType: String
    public let reason: String
    public let severity: String

    public init(
        transactionId: String,
        date: Date,
        merchant: String,
        amount: Decimal,
        category: String,
        anomalyType: String,
        reason: String,
        severity: String = "medium"
    ) {
        self.transactionId = transactionId
        self.date = date
        self.merchant = merchant
        self.amount = amount
        self.category = category
        self.anomalyType = anomalyType
        self.reason = reason
        self.severity = severity
    }

    private enum CodingKeys: String, CodingKey {
        case transactionId
        case date
        case merchant
        case amount
        case category
        case anomalyType
        case reason
        case severity
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.transactionId = try container.decode(String.self, forKey: .transactionId)
        self.date = try container.decode(Date.self, forKey: .date)
        self.merchant = try container.decode(String.self, forKey: .merchant)
        self.amount = try container.decodeFlexibleDecimal(forKey: .amount)
        self.category = try container.decode(String.self, forKey: .category)
        self.anomalyType = try container.decode(String.self, forKey: .anomalyType)
        self.reason = try container.decode(String.self, forKey: .reason)
        self.severity = try container.decodeIfPresent(String.self, forKey: .severity) ?? "medium"
    }
}
