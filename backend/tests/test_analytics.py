import uuid
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.models import Transaction
from app.services.analytics.anomalies import detect_unusual_transactions
from app.services.analytics.engine import (
    calculate_category_breakdown,
    calculate_monthly_trends,
    calculate_summary,
    compare_periods,
    get_top_transactions,
)
from app.services.analytics.recurring import detect_recurring_transactions


def _mock_txn(
    merchant: str,
    amount: str,
    date_val: str,
    category: str = "Food",
    txn_type: str = "expense",
) -> Transaction:
    y, m, d = [int(x) for x in date_val.split("-")]
    return Transaction(
        id=uuid.uuid4(),
        merchant=merchant,
        original_description=f"{merchant} DESC",
        amount=Decimal(amount),
        currency="CAD",
        date=date(y, m, d),
        category=category,
        transaction_type=txn_type,
        confidence=0.99,
    )


def test_deterministic_summary_and_categories():
    txns = [
        _mock_txn("Tim Hortons", "-4.50", "2026-08-01", "Food"),
        _mock_txn("Starbucks", "-6.75", "2026-08-02", "Food"),
        _mock_txn("Shell", "-60.00", "2026-08-03", "Transportation"),
        _mock_txn("Employer", "3000.00", "2026-08-15", "Income", "income"),
    ]

    summary = calculate_summary(txns)
    assert summary.total_income == Decimal("3000.00")
    assert summary.total_expenses == Decimal("-71.25")
    assert summary.net_cash_flow == Decimal("2928.75")
    assert summary.transaction_count == 4

    breakdown = calculate_category_breakdown(txns)
    assert len(breakdown) == 2
    # Transportation: 60 / 71.25 = 84.21%
    assert breakdown[0].category == "Transportation"
    assert breakdown[0].amount == Decimal("60.00")
    assert breakdown[0].percentage == 84.21

    # Food: 11.25 / 71.25 = 15.79%
    assert breakdown[1].category == "Food"
    assert breakdown[1].amount == Decimal("11.25")
    assert breakdown[1].percentage == 15.79


def test_monthly_trends_and_period_comparison():
    july_txns = [
        _mock_txn("Supermarket", "-200.00", "2026-07-05", "Food"),
        _mock_txn("Payroll", "2500.00", "2026-07-15", "Income", "income"),
    ]
    august_txns = [
        _mock_txn("Supermarket", "-350.00", "2026-08-05", "Food"),
        _mock_txn("Electronics", "-400.00", "2026-08-10", "Shopping"),
        _mock_txn("Payroll", "2500.00", "2026-08-15", "Income", "income"),
    ]

    all_txns = july_txns + august_txns
    trends = calculate_monthly_trends(all_txns)
    assert len(trends) == 2
    assert trends[0].month == "2026-07"
    assert trends[0].total_expenses == Decimal("-200.00")
    assert trends[0].net_cash_flow == Decimal("2300.00")

    assert trends[1].month == "2026-08"
    assert trends[1].total_expenses == Decimal("-750.00")
    assert trends[1].net_cash_flow == Decimal("1750.00")

    # Compare August (current) vs July (previous)
    comparison = compare_periods(august_txns, july_txns)
    assert comparison.current_expenses == Decimal("-750.00")
    assert comparison.previous_expenses == Decimal("-200.00")
    assert comparison.delta_expenses == Decimal("550.00")
    # Increase from 200 to 750 is +275%
    assert comparison.delta_percentage == 275.0
    assert len(comparison.top_increased_categories) >= 1
    top_inc = comparison.top_increased_categories[0]
    assert top_inc.category in ("Shopping", "Food")


def test_top_transactions_selection():
    txns = [
        _mock_txn("Coffee", "-4.50", "2026-08-01", "Food"),
        _mock_txn("MacBook", "-1899.99", "2026-08-02", "Shopping"),
        _mock_txn("Dinner", "-85.50", "2026-08-03", "Food"),
        _mock_txn("Bonus", "5000.00", "2026-08-05", "Income", "income"),
    ]

    top_exp = get_top_transactions(txns, limit=2, txn_type="expense")
    assert len(top_exp) == 2
    assert top_exp[0].merchant == "MacBook"
    assert top_exp[1].merchant == "Dinner"

    top_inc = get_top_transactions(txns, limit=1, txn_type="income")
    assert len(top_inc) == 1
    assert top_inc[0].merchant == "Bonus"


def test_recurring_transaction_detection():
    txns = [
        # Netflix: monthly ~30 days
        _mock_txn("Netflix", "-16.99", "2026-06-15", "Entertainment"),
        _mock_txn("Netflix", "-16.99", "2026-07-15", "Entertainment"),
        _mock_txn("Netflix", "-16.99", "2026-08-15", "Entertainment"),
        # Gym: bi-weekly ~14 days
        _mock_txn("GoodLife", "-29.99", "2026-08-01", "Healthcare"),
        _mock_txn("GoodLife", "-29.99", "2026-08-15", "Healthcare"),
        _mock_txn("GoodLife", "-29.99", "2026-08-29", "Healthcare"),
        # One-off coffee
        _mock_txn("Local Cafe", "-5.50", "2026-08-10", "Food"),
    ]

    recurring = detect_recurring_transactions(txns)
    assert len(recurring) == 2

    merchants = {r.merchant: r for r in recurring}
    assert "Netflix" in merchants
    assert merchants["Netflix"].frequency == "monthly"
    assert merchants["Netflix"].expected_amount == Decimal("16.99")
    assert merchants["Netflix"].is_subscription is True
    assert merchants["Netflix"].occurrence_count == 3
    assert merchants["Netflix"].next_expected_date == date(2026, 9, 14)

    assert "GoodLife" in merchants
    assert merchants["GoodLife"].frequency == "bi-weekly"
    assert merchants["GoodLife"].expected_amount == Decimal("29.99")
    assert merchants["GoodLife"].occurrence_count == 3


def test_unusual_transaction_detection():
    txns = [
        # Duplicate charge within 24 hours
        _mock_txn("Bistro Paris", "-68.50", "2026-08-10", "Food"),
        _mock_txn("Bistro Paris", "-68.50", "2026-08-11", "Food"),
        # Normal food expenses
        _mock_txn("Subway", "-12.00", "2026-08-01", "Food"),
        _mock_txn("McDonalds", "-11.50", "2026-08-03", "Food"),
        _mock_txn("Wendy's", "-14.00", "2026-08-05", "Food"),
        _mock_txn("Taco Bell", "-10.50", "2026-08-07", "Food"),
        # Statistical outlier in food category
        _mock_txn("Luxury Steakhouse", "-450.00", "2026-08-20", "Food"),
        # Large expense exceeding threshold
        _mock_txn("Apple Store", "-1299.00", "2026-08-25", "Shopping"),
    ]

    anomalies = detect_unusual_transactions(txns, large_expense_threshold=Decimal("500.00"))
    types = {a.anomaly_type for a in anomalies}

    assert "duplicate_charge" in types
    assert "category_outlier" in types
    assert "large_expense" in types

    dup = [a for a in anomalies if a.anomaly_type == "duplicate_charge"][0]
    assert dup.merchant == "Bistro Paris"
    assert dup.severity == "high"

    large = [a for a in anomalies if a.anomaly_type == "large_expense"][0]
    assert large.merchant == "Apple Store"


@pytest.mark.asyncio
async def test_analytics_api_endpoints(client: AsyncClient):
    csv_content = (
        b"Date,Description,Amount\n"
        b"2026-07-01,Netflix,-16.99\n"
        b"2026-08-01,Netflix,-16.99\n"
        b"2026-08-02,Starbucks,-5.25\n"
        b"2026-08-03,Starbucks,-5.25\n"
        b"2026-08-15,Electronics Superstore,-899.00\n"
        b"2026-08-20,Employer Direct Deposit,3500.00\n"
    )

    valid_file = {"file": ("analytics_statement.csv", csv_content, "text/csv")}
    upload_res = await client.post("/api/statements/upload?run_sync=true", files=valid_file)
    assert upload_res.status_code == 201
    stmt_id = upload_res.json()["id"]

    # 1. Monthly Trends API
    trends_res = await client.get(f"/api/analytics/monthly-trends?statement_id={stmt_id}")
    assert trends_res.status_code == 200
    trends = trends_res.json()
    assert len(trends) == 2
    assert trends[0]["month"] == "2026-07"
    assert trends[1]["month"] == "2026-08"

    # 2. Recurring Transactions API
    recurring_res = await client.get(f"/api/analytics/recurring?statement_id={stmt_id}")
    assert recurring_res.status_code == 200
    recurring = recurring_res.json()
    assert any(r["merchant"] == "Netflix" for r in recurring)

    # 3. Unusual Transactions API
    unusual_res = await client.get(f"/api/analytics/unusual?statement_id={stmt_id}")
    assert unusual_res.status_code == 200
    unusual = unusual_res.json()
    assert any(
        u["merchant"] == "Starbucks" and u["anomaly_type"] == "duplicate_charge" for u in unusual
    )
    assert any(u["anomaly_type"] == "large_expense" for u in unusual)

    # 4. Top Spending Transactions API
    top_res = await client.get(f"/api/analytics/top?statement_id={stmt_id}&limit=2")
    assert top_res.status_code == 200
    top_txns = top_res.json()
    assert len(top_txns) == 2
    assert Decimal(str(top_txns[0]["amount"])) == Decimal("-899.00")

    # 5. Period Comparison API
    comp_res = await client.get(
        f"/api/analytics/comparison?curr_start=2026-08-01&curr_end=2026-08-31&prev_start=2026-07-01&prev_end=2026-07-31&statement_id={stmt_id}"
    )
    assert comp_res.status_code == 200
    comp = comp_res.json()
    assert Decimal(str(comp["current_income"])) == Decimal("3500.00")
