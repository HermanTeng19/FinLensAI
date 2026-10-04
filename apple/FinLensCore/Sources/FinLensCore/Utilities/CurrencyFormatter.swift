import Foundation

public enum CurrencyFormatter {
    /// Formats a Decimal financial amount using Apple's FormatStyle
    /// Strictly avoids string concatenation ("$" + amount) and honors locale/currency.
    public static func format(
        amount: Decimal,
        currencyCode: String = "CAD",
        locale: Locale = .current
    ) -> String {
        amount.formatted(
            .currency(code: currencyCode)
            .locale(locale)
        )
    }
}
