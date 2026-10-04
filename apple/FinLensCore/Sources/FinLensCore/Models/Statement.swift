import Foundation

public struct Statement: Identifiable, Sendable, Codable, Equatable, Hashable {
    public let id: String
    public let filename: String
    public let fileFormat: StatementFormat
    public let status: ProcessingStatus
    public let periodStart: Date?
    public let periodEnd: Date?
    public let totalTransactions: Int
    public let createdAt: Date

    public init(
        id: String = UUID().uuidString,
        filename: String,
        fileFormat: StatementFormat,
        status: ProcessingStatus = .pending,
        periodStart: Date? = nil,
        periodEnd: Date? = nil,
        totalTransactions: Int = 0,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.filename = filename
        self.fileFormat = fileFormat
        self.status = status
        self.periodStart = periodStart
        self.periodEnd = periodEnd
        self.totalTransactions = totalTransactions
        self.createdAt = createdAt
    }
}

public enum StatementFormat: String, Sendable, Codable, Equatable, Hashable, CaseIterable {
    case pdf
    case csv
}

public enum ProcessingStatus: String, Sendable, Codable, Equatable, Hashable, CaseIterable {
    case pending
    case processing
    case completed
    case failed
}
