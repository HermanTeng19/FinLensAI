import Foundation

public extension KeyedDecodingContainer {
    func decodeFlexibleDecimal(forKey key: Key) throws -> Decimal {
        if let decimalValue = try? decode(Decimal.self, forKey: key) {
            return decimalValue
        }
        if let stringValue = try? decode(String.self, forKey: key),
           let decimalValue = Decimal(string: stringValue) {
            return decimalValue
        }
        if let doubleValue = try? decode(Double.self, forKey: key) {
            return Decimal(doubleValue)
        }
        throw DecodingError.dataCorruptedError(
            forKey: key,
            in: self,
            debugDescription: "Expected number or string for Decimal at key \(key.stringValue)"
        )
    }

    func decodeFlexibleDecimalIfPresent(forKey key: Key) throws -> Decimal? {
        guard contains(key) else { return nil }
        return try? decodeFlexibleDecimal(forKey: key)
    }
}

public enum FinLensJSONDecoder {
    public static func makeStandard() -> JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase

        decoder.dateDecodingStrategy = .custom { d in
            let container = try d.singleValueContainer()
            let dateStr = try container.decode(String.self)

            let isoFractional = ISO8601DateFormatter()
            isoFractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = isoFractional.date(from: dateStr) {
                return date
            }

            let isoStandard = ISO8601DateFormatter()
            isoStandard.formatOptions = [.withInternetDateTime]
            if let date = isoStandard.date(from: dateStr) {
                return date
            }

            let simpleDate = DateFormatter()
            simpleDate.dateFormat = "yyyy-MM-dd"
            simpleDate.locale = Locale(identifier: "en_US_POSIX")
            simpleDate.timeZone = TimeZone(secondsFromGMT: 0)
            if let date = simpleDate.date(from: dateStr) {
                return date
            }

            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Unsupported date format: \(dateStr)"
            )
        }

        return decoder
    }
}
