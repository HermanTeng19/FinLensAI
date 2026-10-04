import Foundation

public enum InsightSeverity: String, Sendable, Codable, CaseIterable {
    case high
    case medium
    case low

    public var displayName: String {
        switch self {
        case .high: return "High"
        case .medium: return "Medium"
        case .low: return "Notice"
        }
    }
}

public enum InsightType: String, Sendable, Codable, CaseIterable {
    case warning
    case positive
    case info

    public var iconName: String {
        switch self {
        case .warning:
            return "exclamationmark.triangle.fill"
        case .positive:
            return "sparkles"
        case .info:
            return "info.circle.fill"
        }
    }
}

public struct SupportingTransaction: Identifiable, Sendable, Codable, Hashable {
    public let id: UUID
    public let date: String
    public let merchant: String
    public let amount: Decimal
    public let category: String

    public init(
        id: UUID = UUID(),
        date: String,
        merchant: String,
        amount: Decimal,
        category: String
    ) {
        self.id = id
        self.date = date
        self.merchant = merchant
        self.amount = amount
        self.category = category
    }

    enum CodingKeys: String, CodingKey {
        case id
        case date
        case merchant
        case amount
        case category
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.id = try container.decode(UUID.self, forKey: .id)
        self.date = try container.decode(String.self, forKey: .date)
        self.merchant = try container.decode(String.self, forKey: .merchant)
        self.category = try container.decode(String.self, forKey: .category)

        if let decimalVal = try? container.decode(Decimal.self, forKey: .amount) {
            self.amount = decimalVal
        } else if let strVal = try? container.decode(String.self, forKey: .amount),
                  let decimalVal = Decimal(string: strVal) {
            self.amount = decimalVal
        } else {
            self.amount = Decimal.zero
        }
    }
}

public struct InsightItem: Identifiable, Sendable, Codable, Hashable {
    public let id: UUID
    public let statementId: UUID?
    public let insightType: InsightType
    public let category: String
    public let title: String
    public let content: String
    public let severity: InsightSeverity
    public let metric: String?
    public let supportingTransactions: [SupportingTransaction]
    public let metadata: [String: AnyCodableValue]
    public let generatedAt: String

    public init(
        id: UUID = UUID(),
        statementId: UUID? = nil,
        insightType: InsightType,
        category: String,
        title: String,
        content: String,
        severity: InsightSeverity = .medium,
        metric: String? = nil,
        supportingTransactions: [SupportingTransaction] = [],
        metadata: [String: AnyCodableValue] = [:],
        generatedAt: String = ISO8601DateFormatter().string(from: Date())
    ) {
        self.id = id
        self.statementId = statementId
        self.insightType = insightType
        self.category = category
        self.title = title
        self.content = content
        self.severity = severity
        self.metric = metric
        self.supportingTransactions = supportingTransactions
        self.metadata = metadata
        self.generatedAt = generatedAt
    }

    enum CodingKeys: String, CodingKey {
        case id
        case statementId
        case insightType
        case category
        case title
        case content
        case severity
        case metric
        case supportingTransactions
        case metadata
        case generatedAt
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.id = try container.decode(UUID.self, forKey: .id)
        self.statementId = try container.decodeIfPresent(UUID.self, forKey: .statementId)

        let rawType = try container.decode(String.self, forKey: .insightType)
        self.insightType = InsightType(rawValue: rawType.lowercased()) ?? .info

        self.category = try container.decode(String.self, forKey: .category)
        self.title = try container.decode(String.self, forKey: .title)
        self.content = try container.decode(String.self, forKey: .content)

        let rawSeverity = try container.decodeIfPresent(String.self, forKey: .severity) ?? "medium"
        self.severity = InsightSeverity(rawValue: rawSeverity.lowercased()) ?? .medium

        self.metric = try container.decodeIfPresent(String.self, forKey: .metric)
        self.supportingTransactions = try container.decodeIfPresent([SupportingTransaction].self, forKey: .supportingTransactions) ?? []
        self.metadata = try container.decodeIfPresent([String: AnyCodableValue].self, forKey: .metadata) ?? [:]
        self.generatedAt = try container.decodeIfPresent(String.self, forKey: .generatedAt) ?? ""
    }

    public static func == (lhs: InsightItem, rhs: InsightItem) -> Bool {
        lhs.id == rhs.id
    }

    public func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

public struct InsightListResponse: Sendable, Codable {
    public let insights: [InsightItem]
    public let totalCount: Int
    public let warningCount: Int
    public let positiveCount: Int
    public let infoCount: Int

    enum CodingKeys: String, CodingKey {
        case insights
        case totalCount
        case warningCount
        case positiveCount
        case infoCount
    }

    public init(
        insights: [InsightItem],
        totalCount: Int,
        warningCount: Int,
        positiveCount: Int,
        infoCount: Int
    ) {
        self.insights = insights
        self.totalCount = totalCount
        self.warningCount = warningCount
        self.positiveCount = positiveCount
        self.infoCount = infoCount
    }
}
