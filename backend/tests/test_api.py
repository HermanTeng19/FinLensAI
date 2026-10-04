from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.schemas.schemas import FinancialSummary


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "FinLens AI Backend"
    assert data["tagline"] == "Understand Your Spending with AI"
    assert data["status"] == "online"


@pytest.mark.asyncio
async def test_health_check_live_database(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_deterministic_decimal_precision():
    amount1 = Decimal("124.30")
    amount2 = Decimal("0.70")
    total = amount1 + amount2
    assert total == Decimal("125.00")
    assert str(total) == "125.00"

    income = Decimal("3500.50")
    expenses = Decimal("-1250.25")
    net = income + expenses
    summary = FinancialSummary(
        total_income=income,
        total_expenses=expenses,
        net_cash_flow=net,
        currency="CAD",
        transaction_count=2,
    )
    assert summary.net_cash_flow == Decimal("2250.25")


@pytest.mark.asyncio
async def test_statement_lifecycle_and_cascade_deletion(client: AsyncClient):
    # 1. Invalid file format rejection
    bad_file = {"file": ("test.txt", b"invalid content", "text/plain")}
    res = await client.post("/api/statements/upload", files=bad_file)
    assert res.status_code == 400

    # 2. Valid CSV Statement Upload
    csv_content = (
        b"Date,Description,Amount\n2026-09-18,AMZN Mktp,-124.30\n2026-09-19,Payroll,3000.00\n"
    )
    valid_file = {"file": ("statement_sept.csv", csv_content, "text/csv")}
    res = await client.post("/api/statements/upload", files=valid_file)
    assert res.status_code == 201
    stmt = res.json()
    statement_id = stmt["id"]
    assert stmt["filename"] == "statement_sept.csv"
    assert stmt["file_format"] == "csv"
    assert stmt["status"] in ("pending", "completed")

    # 3. Duplicate Statement Conflict
    res_dup = await client.post("/api/statements/upload", files=valid_file)
    assert res_dup.status_code == 409

    # 4. Verify auto-extracted transactions linked to statement
    res_txns = await client.get(f"/api/transactions?statement_id={statement_id}")
    assert res_txns.status_code == 200
    txns = res_txns.json()
    assert len(txns) == 2
    txn_id = txns[0]["id"]

    # 5. Deterministic Analytics Query for this statement
    res_summary = await client.get(f"/api/analytics/summary?statement_id={statement_id}")
    assert res_summary.status_code == 200
    summary_data = res_summary.json()
    assert Decimal(str(summary_data["total_expenses"])) == Decimal("-124.30")
    assert Decimal(str(summary_data["total_income"])) == Decimal("3000.00")
    assert Decimal(str(summary_data["net_cash_flow"])) == Decimal("2875.70")

    # 6. Cascade Delete Statement
    res_del = await client.delete(f"/api/statements/{statement_id}")
    assert res_del.status_code == 204

    # 7. Verify Transaction was deleted via foreign key cascade
    res_check_txn = await client.get(f"/api/transactions/{txn_id}")
    assert res_check_txn.status_code == 404
