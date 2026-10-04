import Foundation

public enum APIError: Error, LocalizedError, Sendable {
    case invalidURL
    case serverError(statusCode: Int, message: String)
    case decodingError(String)
    case networkError(String)
    case missingData

    public var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL requested."
        case .serverError(let code, let msg):
            return "Server returned error (\(code)): \(msg)"
        case .decodingError(let msg):
            return "Failed to process server response: \(msg)"
        case .networkError(let msg):
            return "Network connection issue: \(msg)"
        case .missingData:
            return "No data received from server."
        }
    }
}

public protocol APIClientProtocol: Sendable {
    func fetchHealth() async throws -> Bool
    func fetchFinancialSummary(statementId: String?) async throws -> FinancialSummary
    func fetchCategorySpending(statementId: String?) async throws -> [CategorySpending]
    func fetchMonthlyTrends(statementId: String?) async throws -> [MonthlyTrend]
    func fetchRecurringItems(statementId: String?) async throws -> [RecurringItem]
    func fetchUnusualTransactions(statementId: String?) async throws -> [UnusualTransaction]
    func fetchTransactions(statementId: String?, limit: Int?) async throws -> [Transaction]
    func fetchStatements() async throws -> [Statement]
    func uploadStatement(data: Data, filename: String) async throws -> Statement
    func deleteStatement(id: String) async throws
    func resetAllData() async throws -> DataResetResult
    func fetchPrivacyInfo() async throws -> PrivacyPolicyInfo
    func askAgent(message: String, history: [AgentHistoryItem]?) async throws -> AgentQueryResult
    func fetchInsights(statementId: String?) async throws -> [InsightItem]
    func generateInsights(statementId: String?) async throws -> [InsightItem]
}


public actor APIClient: APIClientProtocol {
    public let baseURL: URL
    private let session: URLSession
    private let decoder: JSONDecoder

    public init(
        baseURL: URL = URL(string: "http://127.0.0.1:8000")!,
        session: URLSession = .shared
    ) {
        self.baseURL = baseURL
        self.session = session
        self.decoder = FinLensJSONDecoder.makeStandard()
    }

    public func fetchHealth() async throws -> Bool {
        let url = baseURL.appendingPathComponent("health")
        let (data, response) = try await session.data(from: url)
        guard let httpRes = response as? HTTPURLResponse, httpRes.statusCode == 200 else {
            return false
        }
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return false
        }
        return json["status"] as? String == "ok"
    }

    public func fetchFinancialSummary(statementId: String? = nil) async throws -> FinancialSummary {
        var components = URLComponents(url: baseURL.appendingPathComponent("api/analytics/summary"), resolvingAgainstBaseURL: true)!
        if let statementId = statementId {
            components.queryItems = [URLQueryItem(name: "statement_id", value: statementId)]
        }
        guard let url = components.url else { throw APIError.invalidURL }
        return try await performRequest(url: url)
    }

    public func fetchCategorySpending(statementId: String? = nil) async throws -> [CategorySpending] {
        var components = URLComponents(url: baseURL.appendingPathComponent("api/analytics/categories"), resolvingAgainstBaseURL: true)!
        if let statementId = statementId {
            components.queryItems = [URLQueryItem(name: "statement_id", value: statementId)]
        }
        guard let url = components.url else { throw APIError.invalidURL }
        return try await performRequest(url: url)
    }

    public func fetchMonthlyTrends(statementId: String? = nil) async throws -> [MonthlyTrend] {
        var components = URLComponents(url: baseURL.appendingPathComponent("api/analytics/monthly-trends"), resolvingAgainstBaseURL: true)!
        if let statementId = statementId {
            components.queryItems = [URLQueryItem(name: "statement_id", value: statementId)]
        }
        guard let url = components.url else { throw APIError.invalidURL }
        return try await performRequest(url: url)
    }

    public func fetchRecurringItems(statementId: String? = nil) async throws -> [RecurringItem] {
        var components = URLComponents(url: baseURL.appendingPathComponent("api/analytics/recurring"), resolvingAgainstBaseURL: true)!
        if let statementId = statementId {
            components.queryItems = [URLQueryItem(name: "statement_id", value: statementId)]
        }
        guard let url = components.url else { throw APIError.invalidURL }
        return try await performRequest(url: url)
    }

    public func fetchUnusualTransactions(statementId: String? = nil) async throws -> [UnusualTransaction] {
        var components = URLComponents(url: baseURL.appendingPathComponent("api/analytics/unusual"), resolvingAgainstBaseURL: true)!
        if let statementId = statementId {
            components.queryItems = [URLQueryItem(name: "statement_id", value: statementId)]
        }
        guard let url = components.url else { throw APIError.invalidURL }
        return try await performRequest(url: url)
    }

    public func fetchTransactions(statementId: String? = nil, limit: Int? = 100) async throws -> [Transaction] {
        var components = URLComponents(url: baseURL.appendingPathComponent("api/transactions"), resolvingAgainstBaseURL: true)!
        var queryItems: [URLQueryItem] = []
        if let statementId = statementId {
            queryItems.append(URLQueryItem(name: "statement_id", value: statementId))
        }
        if let limit = limit {
            queryItems.append(URLQueryItem(name: "limit", value: String(limit)))
        }
        if !queryItems.isEmpty {
            components.queryItems = queryItems
        }
        guard let url = components.url else { throw APIError.invalidURL }
        return try await performRequest(url: url)
    }

    public func fetchStatements() async throws -> [Statement] {
        let url = baseURL.appendingPathComponent("api/statements")
        return try await performRequest(url: url)
    }

    public func uploadStatement(data: Data, filename: String) async throws -> Statement {
        let url = baseURL.appendingPathComponent("api/statements/upload")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        let mimeType = filename.lowercased().hasSuffix(".pdf") ? "application/pdf" : "text/csv"
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(data)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        let (responseData, response) = try await session.data(for: request)
        guard let httpRes = response as? HTTPURLResponse else {
            throw APIError.networkError("Invalid HTTP response.")
        }

        if httpRes.statusCode == 201 || httpRes.statusCode == 200 {
            do {
                return try decoder.decode(Statement.self, from: responseData)
            } catch {
                throw APIError.decodingError(error.localizedDescription)
            }
        } else {
            let msg = String(data: responseData, encoding: .utf8) ?? "Upload failed"
            throw APIError.serverError(statusCode: httpRes.statusCode, message: msg)
        }
    }

    public func deleteStatement(id: String) async throws {
        let url = baseURL.appendingPathComponent("api/statements/\(id)")
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"

        let (responseData, response) = try await session.data(for: request)
        guard let httpRes = response as? HTTPURLResponse else {
            throw APIError.networkError("Invalid HTTP response.")
        }
        guard httpRes.statusCode == 204 || httpRes.statusCode == 200 else {
            let msg = String(data: responseData, encoding: .utf8) ?? "Delete failed"
            throw APIError.serverError(statusCode: httpRes.statusCode, message: msg)
        }
    }

    public func resetAllData() async throws -> DataResetResult {
        let url = baseURL.appendingPathComponent("api/data/reset")
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        let (responseData, response) = try await session.data(for: request)
        guard let httpRes = response as? HTTPURLResponse else {
            throw APIError.networkError("Invalid HTTP response.")
        }
        guard (200...299).contains(httpRes.statusCode) else {
            let msg = String(data: responseData, encoding: .utf8) ?? "Data reset failed"
            throw APIError.serverError(statusCode: httpRes.statusCode, message: msg)
        }
        return try decoder.decode(DataResetResult.self, from: responseData)
    }

    public func fetchPrivacyInfo() async throws -> PrivacyPolicyInfo {
        let url = baseURL.appendingPathComponent("api/data/privacy-info")
        return try await performRequest(url: url)
    }

    public func askAgent(message: String, history: [AgentHistoryItem]? = nil) async throws -> AgentQueryResult {
        let url = baseURL.appendingPathComponent("api/agent/query")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        let reqBody = AgentQueryRequest(message: message, history: history)
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        request.httpBody = try encoder.encode(reqBody)

        let (data, response) = try await session.data(for: request)
        guard let httpRes = response as? HTTPURLResponse else {
            throw APIError.networkError("Invalid HTTP response.")
        }
        guard (200...299).contains(httpRes.statusCode) else {
            let msg = String(data: data, encoding: .utf8) ?? "HTTP \(httpRes.statusCode)"
            throw APIError.serverError(statusCode: httpRes.statusCode, message: msg)
        }

        let dto = try decoder.decode(AgentResponseDTO.self, from: data)
        let toolCalls = dto.toolCalls.map { raw in
            AgentToolCall(
                toolName: raw.toolName,
                description: raw.toolName
            )
        }
        return AgentQueryResult(
            response: dto.response,
            toolCalls: toolCalls,
            grounded: dto.grounded
        )
    }

    public func fetchInsights(statementId: String? = nil) async throws -> [InsightItem] {
        var components = URLComponents(url: baseURL.appendingPathComponent("api/insights"), resolvingAgainstBaseURL: true)!
        if let sid = statementId, !sid.isEmpty {
            components.queryItems = [URLQueryItem(name: "statement_id", value: sid)]
        }
        guard let url = components.url else { throw APIError.invalidURL }
        let res: InsightListResponse = try await performRequest(url: url)
        return res.insights
    }

    public func generateInsights(statementId: String? = nil) async throws -> [InsightItem] {
        var components = URLComponents(url: baseURL.appendingPathComponent("api/insights/generate"), resolvingAgainstBaseURL: true)!
        if let sid = statementId, !sid.isEmpty {
            components.queryItems = [URLQueryItem(name: "statement_id", value: sid)]
        }
        guard let url = components.url else { throw APIError.invalidURL }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        if let sid = statementId, !sid.isEmpty {
            let body = ["statement_id": sid]
            request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        }

        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIError.networkError(error.localizedDescription)
        }

        guard let httpRes = response as? HTTPURLResponse else {
            throw APIError.networkError("Non-HTTP response received.")
        }

        guard (200...299).contains(httpRes.statusCode) else {
            let msg = String(data: data, encoding: .utf8) ?? "HTTP \(httpRes.statusCode)"
            throw APIError.serverError(statusCode: httpRes.statusCode, message: msg)
        }

        do {
            let res = try decoder.decode(InsightListResponse.self, from: data)
            return res.insights
        } catch {
            throw APIError.decodingError("\(error)")
        }
    }

    // MARK: - Private Helpers


    private func performRequest<T: Decodable>(url: URL) async throws -> T {
        var request = URLRequest(url: url)
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIError.networkError(error.localizedDescription)
        }

        guard let httpRes = response as? HTTPURLResponse else {
            throw APIError.networkError("Non-HTTP response received.")
        }

        guard (200...299).contains(httpRes.statusCode) else {
            let msg = String(data: data, encoding: .utf8) ?? "HTTP \(httpRes.statusCode)"
            throw APIError.serverError(statusCode: httpRes.statusCode, message: msg)
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError("\(error)")
        }
    }
}
