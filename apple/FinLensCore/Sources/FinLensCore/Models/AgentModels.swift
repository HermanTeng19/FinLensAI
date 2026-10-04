import Foundation

public enum MessageRole: String, Codable, Sendable, Equatable {
    case user
    case assistant
    case system
}

public enum AnyCodableValue: Codable, Sendable, Equatable {
    case string(String)
    case int(Int)
    case double(Double)
    case bool(Bool)
    case dictionary([String: AnyCodableValue])
    case array([AnyCodableValue])
    case null

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let b = try? container.decode(Bool.self) {
            self = .bool(b)
        } else if let i = try? container.decode(Int.self) {
            self = .int(i)
        } else if let d = try? container.decode(Double.self) {
            self = .double(d)
        } else if let s = try? container.decode(String.self) {
            self = .string(s)
        } else if let dict = try? container.decode([String: AnyCodableValue].self) {
            self = .dictionary(dict)
        } else if let arr = try? container.decode([AnyCodableValue].self) {
            self = .array(arr)
        } else {
            self = .null
        }
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let s): try container.encode(s)
        case .int(let i): try container.encode(i)
        case .double(let d): try container.encode(d)
        case .bool(let b): try container.encode(b)
        case .dictionary(let dict): try container.encode(dict)
        case .array(let arr): try container.encode(arr)
        case .null: try container.encodeNil()
        }
    }
}

public struct AgentToolCall: Identifiable, Codable, Sendable, Equatable {
    public var id: UUID
    public var toolName: String
    public var description: String

    public init(id: UUID = UUID(), toolName: String, description: String = "") {
        self.id = id
        self.toolName = toolName
        self.description = description
    }

    public var friendlyName: String {
        switch toolName {
        case "search_transactions":
            return "Search Transactions"
        case "get_transaction_details":
            return "Transaction Details"
        case "get_spending_by_category":
            return "Category Breakdown"
        case "compare_periods":
            return "Period Comparison"
        case "get_top_transactions":
            return "Top Expenses"
        case "detect_recurring_transactions":
            return "Recurring Subscriptions"
        case "detect_unusual_transactions":
            return "Anomaly Detection"
        case "get_monthly_summary":
            return "Monthly Financial Summary"
        default:
            return toolName.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }

    public var iconName: String {
        switch toolName {
        case "search_transactions":
            return "magnifyingglass"
        case "get_transaction_details":
            return "doc.text.magnifyingglass"
        case "get_spending_by_category":
            return "chart.pie.fill"
        case "compare_periods":
            return "arrow.left.arrow.right"
        case "get_top_transactions":
            return "arrow.up.circle.fill"
        case "detect_recurring_transactions":
            return "arrow.triangle.2.circlepath"
        case "detect_unusual_transactions":
            return "exclamationmark.shield.fill"
        case "get_monthly_summary":
            return "chart.line.uptrend.xyaxis"
        default:
            return "sparkles"
        }
    }
}

public struct ChatMessage: Identifiable, Codable, Sendable, Equatable {
    public var id: UUID
    public var role: MessageRole
    public var content: String
    public var timestamp: Date
    public var toolCalls: [AgentToolCall]
    public var isGrounded: Bool

    public init(
        id: UUID = UUID(),
        role: MessageRole,
        content: String,
        timestamp: Date = Date(),
        toolCalls: [AgentToolCall] = [],
        isGrounded: Bool = true
    ) {
        self.id = id
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.toolCalls = toolCalls
        self.isGrounded = isGrounded
    }
}

public struct AgentHistoryItem: Codable, Sendable {
    public let role: String
    public let content: String

    public init(role: String, content: String) {
        self.role = role
        self.content = content
    }
}

public struct AgentQueryRequest: Codable, Sendable {
    public let message: String
    public let history: [AgentHistoryItem]?

    public init(message: String, history: [AgentHistoryItem]? = nil) {
        self.message = message
        self.history = history
    }
}

public struct AgentRawToolCall: Codable, Sendable {
    public let toolName: String
    public let arguments: [String: AnyCodableValue]?
    public let output: AnyCodableValue?
}

public struct AgentResponseDTO: Codable, Sendable {
    public let response: String
    public let toolCalls: [AgentRawToolCall]
    public let grounded: Bool
}

public struct AgentQueryResult: Sendable {
    public let response: String
    public let toolCalls: [AgentToolCall]
    public let grounded: Bool

    public init(response: String, toolCalls: [AgentToolCall], grounded: Bool) {
        self.response = response
        self.toolCalls = toolCalls
        self.grounded = grounded
    }
}
