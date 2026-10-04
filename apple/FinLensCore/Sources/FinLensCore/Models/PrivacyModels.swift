import Foundation

/// Audit payload returned by the backend when an atomic data reset is performed.
public struct DataResetResult: Codable, Sendable, Hashable {
    public let status: String
    public let deletedStatements: Int
    public let deletedTransactions: Int
    public let deletedInsights: Int
    public let deletedJobs: Int
    public let message: String
    public let timestamp: String

    public init(
        status: String = "success",
        deletedStatements: Int = 0,
        deletedTransactions: Int = 0,
        deletedInsights: Int = 0,
        deletedJobs: Int = 0,
        message: String = "",
        timestamp: String = ""
    ) {
        self.status = status
        self.deletedStatements = deletedStatements
        self.deletedTransactions = deletedTransactions
        self.deletedInsights = deletedInsights
        self.deletedJobs = deletedJobs
        self.message = message
        self.timestamp = timestamp
    }
}

/// Architectural privacy principles and status returned by `/api/data/privacy-info`.
public struct PrivacyPolicyInfo: Codable, Sendable, Hashable {
    public let architecture: String
    public let bankCredentialsRequired: Bool
    public let inMemoryPdfProcessing: Bool
    public let unencryptedFilesStoredOnDisk: Bool
    public let logRedactionEnabled: Bool
    public let cascadeDeletionSupported: Bool
    public let guarantee: String

    public init(
        architecture: String = "Zero-Retention & In-Memory Extraction",
        bankCredentialsRequired: Bool = false,
        inMemoryPdfProcessing: Bool = true,
        unencryptedFilesStoredOnDisk: Bool = false,
        logRedactionEnabled: Bool = true,
        cascadeDeletionSupported: Bool = true,
        guarantee: String = "FinLens AI does not require, store, or transmit your online banking credentials. Bank statements are analyzed in-memory and all derived financial intelligence can be completely and irreversibly wiped with one tap."
    ) {
        self.architecture = architecture
        self.bankCredentialsRequired = bankCredentialsRequired
        self.inMemoryPdfProcessing = inMemoryPdfProcessing
        self.unencryptedFilesStoredOnDisk = unencryptedFilesStoredOnDisk
        self.logRedactionEnabled = logRedactionEnabled
        self.cascadeDeletionSupported = cascadeDeletionSupported
        self.guarantee = guarantee
    }
}
