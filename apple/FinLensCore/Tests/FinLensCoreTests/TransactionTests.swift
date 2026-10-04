import XCTest
@testable import FinLensCore

final class TransactionTests: XCTestCase {
    func testCanonicalTransactionCreationAndDecimalPrecision() {
        let amount = Decimal(string: "-124.30")!
        let txn = Transaction(
            date: Date(),
            merchant: "Amazon",
            originalDescription: "AMZN Mktp CA*9812487",
            amount: amount,
            currency: "CAD",
            transactionType: .expense,
            category: "Shopping",
            subcategory: "Online Shopping",
            confidence: 0.98
        )

        XCTAssertEqual(txn.merchant, "Amazon")
        XCTAssertEqual(txn.amount, Decimal(string: "-124.30")!)
        XCTAssertEqual(txn.currency, "CAD")
        XCTAssertEqual(txn.transactionType, .expense)
        XCTAssertEqual(txn.confidence, 0.98)
    }

    func testCurrencyFormattingWithoutStringConcatenation() {
        let amount = Decimal(string: "450.50")!
        let formatted = CurrencyFormatter.format(amount: amount, currencyCode: "CAD", locale: Locale(identifier: "en_CA"))
        XCTAssertTrue(formatted.contains("450.50"))
    }
}
