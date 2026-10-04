from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.services.document_ai.categorizer import Categorizer
from app.services.document_ai.merchant_normalizer import MerchantNormalizer
from app.services.document_ai.parser import (
    AmountParser,
    CSVParser,
    DateParser,
)


def test_merchant_normalizer():
    # Test noisy prefix and suffix stripping
    m1, conf1 = MerchantNormalizer.normalize("AMZN Mktp CA*9812487")
    assert m1 == "Amazon"
    assert conf1 > 0.9

    m2, conf2 = MerchantNormalizer.normalize("TST* TIM HORTONS #1024 VANCOUVER BC")
    assert m2 == "Tim Hortons"
    assert conf2 > 0.9

    m3, conf3 = MerchantNormalizer.normalize("UBER *EATS PENDING")
    assert m3 == "Uber Eats"
    assert conf3 > 0.9

    m4, conf4 = MerchantNormalizer.normalize("APPLE.COM/BILL")
    assert m4 == "Apple"
    assert conf4 > 0.9


def test_categorizer():
    # Coffee / Food
    cat, subcat, conf, txn_type = Categorizer.classify(
        "Tim Hortons", "TST* TIM HORTONS #1024", Decimal("-4.50")
    )
    assert cat == "Food"
    assert subcat == "Coffee & Cafe"
    assert txn_type == "expense"

    # Shopping
    cat, subcat, conf, txn_type = Categorizer.classify("Amazon", "AMZN Mktp CA", Decimal("-89.99"))
    assert cat == "Shopping"
    assert txn_type == "expense"

    # Utilities
    cat, subcat, conf, txn_type = Categorizer.classify(
        "Electric Utility", "BC HYDRO PAYMENT", Decimal("-112.40")
    )
    assert cat == "Utilities"
    assert txn_type == "expense"

    # Income
    cat, subcat, conf, txn_type = Categorizer.classify(
        "Payroll / Salary", "ACME CORP PAYROLL", Decimal("3500.00")
    )
    assert cat == "Income"
    assert subcat == "Salary"
    assert txn_type == "income"

    # Transfer
    cat, subcat, conf, txn_type = Categorizer.classify(
        "Interac e-Transfer", "INTERAC E-TRANSFER TO JOHN", Decimal("-50.00")
    )
    assert cat == "Transfer"
    assert txn_type == "transfer"


def test_amount_and_date_parsing():
    assert DateParser.parse("2026-09-18") == date(2026, 9, 18)
    assert DateParser.parse("09/18/2026") == date(2026, 9, 18)
    assert DateParser.parse("18/09/2026") == date(2026, 9, 18)

    assert AmountParser.parse("-124.30") == Decimal("-124.30")
    assert AmountParser.parse("$1,250.00") == Decimal("1250.00")
    assert AmountParser.parse("(45.60)") == Decimal("-45.60")
    assert AmountParser.parse("80.00 DR") == Decimal("-80.00")
    assert AmountParser.parse("35.00 CR") == Decimal("35.00")


def test_csv_parser_dual_columns():
    csv_data = (
        b"Date,Description,Debit,Credit\n"
        b"2026-09-01,RENT PAYMENT,1800.00,\n"
        b"2026-09-05,PAYROLL,,3200.00\n"
        b"2026-09-10,STARBUCKS #442,6.75,\n"
    )

    candidates = CSVParser.parse(csv_data)
    assert len(candidates) == 3
    assert candidates[0].amount == Decimal("-1800.00")
    assert candidates[1].amount == Decimal("3200.00")
    assert candidates[2].amount == Decimal("-6.75")


@pytest.mark.asyncio
async def test_end_to_end_statement_processing_and_analytics(client: AsyncClient):
    csv_data = (
        b"Transaction Date,Description,Amount\n"
        b"2026-09-02,TST* TIM HORTONS #1024,-4.50\n"
        b"2026-09-03,AMZN Mktp CA*9812487,-120.00\n"
        b"2026-09-04,SHELL GAS STATION,-65.00\n"
        b"2026-09-15,EMPLOYER PAYROLL DIRECT DEP,2500.00\n"
    )

    files = {"file": ("september_statement.csv", csv_data, "text/csv")}
    upload_res = await client.post("/api/statements/upload?run_sync=true", files=files)
    assert upload_res.status_code == 201
    stmt = upload_res.json()
    assert stmt["status"] == "completed"
    assert stmt["total_transactions"] == 4
    stmt_id = stmt["id"]

    # Verify extracted transactions
    txns_res = await client.get(f"/api/transactions?statement_id={stmt_id}")
    assert txns_res.status_code == 200
    txns = txns_res.json()
    assert len(txns) == 4

    merchants = {t["merchant"] for t in txns}
    assert "Tim Hortons" in merchants
    assert "Amazon" in merchants
    assert "Shell" in merchants
    assert "Direct Deposit" in merchants

    categories = {t["category"] for t in txns}
    assert "Food" in categories
    assert "Shopping" in categories
    assert "Transportation" in categories
    assert "Income" in categories

    # Verify deterministic financial calculations scoped to this statement
    analytics_res = await client.get(f"/api/analytics/categories?statement_id={stmt_id}")
    assert analytics_res.status_code == 200
    cat_breakdown = analytics_res.json()
    assert len(cat_breakdown) >= 3

    # Total expenses = 4.50 + 120.00 + 65.00 = 189.50
    summary_res = await client.get(f"/api/analytics/summary?statement_id={stmt_id}")
    summary = summary_res.json()
    assert Decimal(str(summary["total_expenses"])) == Decimal("-189.50")
    assert Decimal(str(summary["total_income"])) == Decimal("2500.00")
    assert Decimal(str(summary["net_cash_flow"])) == Decimal("2310.50")
