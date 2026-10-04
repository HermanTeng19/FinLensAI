from decimal import Decimal

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_financial_lifecycle_e2e(client: AsyncClient):
    """
    End-to-End full lifecycle test covering:
    1. Upload statement (CSV)
    2. Extraction & deterministic categorization
    3. Deterministic analytics & calculations
    4. AI Insight generation & transaction grounding
    5. Agent query routing & grounded answers
    6. Cascade deletion of single statement
    7. Atomic total data reset
    """
    # ----------------------------------------------------
    # Step 1: Clean slate reset
    # ----------------------------------------------------
    reset_res = await client.delete("/api/data/reset")
    assert reset_res.status_code == 200

    # ----------------------------------------------------
    # Step 2: Upload primary statement (September 2026)
    # ----------------------------------------------------
    sept_csv = (
        b"Date,Description,Amount\n"
        b"2026-09-01,PAYROLL ACME CORP DIRECT DEP,3200.00\n"
        b"2026-09-02,RENT PAYMENT PROPERTY MGMT,-1450.00\n"
        b"2026-09-03,TST* TIM HORTONS #1024,-4.85\n"
        b"2026-09-04,SHELL GAS STATION,-68.20\n"
        b"2026-09-05,WHOLE FOODS MKT 10293,-112.40\n"
        b"2026-09-10,BC HYDRO ELECTRIC UTILITY,-85.10\n"
        b"2026-09-15,NETFLIX.COM LOS GATOS,-19.99\n"
    )

    files = {"file": ("september_checking.csv", sept_csv, "text/csv")}
    upload_res = await client.post("/api/statements/upload?run_sync=true", files=files)
    assert upload_res.status_code == 201
    stmt1 = upload_res.json()
    stmt1_id = stmt1["id"]
    assert stmt1["total_transactions"] == 7
    assert stmt1["status"] == "completed"

    # ----------------------------------------------------
    # Step 3: Verify extracted transactions & categories
    # ----------------------------------------------------
    txns_res = await client.get(f"/api/transactions?statement_id={stmt1_id}")
    assert txns_res.status_code == 200
    txns = txns_res.json()
    assert len(txns) == 7

    merchants = {t["merchant"] for t in txns}
    assert "Tim Hortons" in merchants
    assert "Whole Foods" in merchants
    assert "Shell" in merchants
    assert "Netflix" in merchants
    assert "BC Hydro" in merchants

    # ----------------------------------------------------
    # Step 4: Verify deterministic financial calculations
    # ----------------------------------------------------
    # Total income: 3200.00
    # Total expenses: 1450 + 4.85 + 68.20 + 112.40 + 85.10 + 19.99 = 1740.54
    # Net cash flow: 3200.00 - 1740.54 = 1459.46
    summary_res = await client.get(f"/api/analytics/summary?statement_id={stmt1_id}")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert Decimal(str(summary["total_income"])) == Decimal("3200.00")
    assert Decimal(str(summary["total_expenses"])) == Decimal("-1740.54")
    assert Decimal(str(summary["net_cash_flow"])) == Decimal("1459.46")
    assert summary["transaction_count"] == 7

    # Category breakdown verification
    cats_res = await client.get(f"/api/analytics/categories?statement_id={stmt1_id}")
    assert cats_res.status_code == 200
    cats = cats_res.json()
    cat_names = {c["category"] for c in cats}
    assert "Housing" in cat_names
    assert "Food" in cat_names
    assert "Transportation" in cat_names
    assert "Utilities" in cat_names
    assert "Entertainment" in cat_names

    # ----------------------------------------------------
    # Step 5: Automated AI Insight Generation & Grounding
    # ----------------------------------------------------
    insight_gen_res = await client.post(f"/api/insights/generate?statement_id={stmt1_id}")
    assert insight_gen_res.status_code == 200
    insight_data = insight_gen_res.json()
    assert insight_data["total_count"] >= 2
    for insight in insight_data["insights"]:
        assert insight["statement_id"] == stmt1_id
        # Crucial grounding check: Every insight must have supporting transactions
        assert len(insight["supporting_transactions"]) > 0

    # ----------------------------------------------------
    # Step 6: Agent Question-Answering & Tool Verification
    # ----------------------------------------------------
    # Test Agent: Top expense
    q1_res = await client.post(
        "/api/agent/query", json={"message": "What was my largest purchase?"}
    )
    assert q1_res.status_code == 200
    q1_data = q1_res.json()
    assert q1_data["grounded"] is True
    assert len(q1_data["tool_calls"]) == 1
    assert q1_data["tool_calls"][0]["tool_name"] == "get_top_transactions"
    assert "1450" in q1_data["response"]

    # Test Agent: Food category spending
    q2_res = await client.post(
        "/api/agent/query", json={"message": "How much did I spend on Food?"}
    )
    assert q2_res.status_code == 200
    q2_data = q2_res.json()
    assert q2_data["grounded"] is True
    assert q2_data["tool_calls"][0]["tool_name"] == "get_spending_by_category"

    # Test Agent: Chinese query
    q3_res = await client.post("/api/agent/query", json={"message": "总结一下我的财务总览和现金流"})
    assert q3_res.status_code == 200
    q3_data = q3_res.json()
    assert q3_data["grounded"] is True
    assert q3_data["tool_calls"][0]["tool_name"] == "get_monthly_summary"

    # ----------------------------------------------------
    # Step 7: Upload secondary statement & Test Isolated Cascade
    # ----------------------------------------------------
    oct_csv = (
        b"Date,Description,Amount\n"
        b"2026-10-01,APPLE.COM/BILL,-3.99\n"
        b"2026-10-02,STARBUCKS #0492,-6.25\n"
    )
    files2 = {"file": ("october_card.csv", oct_csv, "text/csv")}
    upload2_res = await client.post("/api/statements/upload?run_sync=true", files=files2)
    assert upload2_res.status_code == 201
    stmt2 = upload2_res.json()
    stmt2_id = stmt2["id"]

    # Delete statement 1
    del_stmt1 = await client.delete(f"/api/statements/{stmt1_id}")
    assert del_stmt1.status_code in (200, 204)

    # Verify statement 1 transactions are gone
    txns_stmt1 = await client.get(f"/api/transactions?statement_id={stmt1_id}")
    assert len(txns_stmt1.json()) == 0

    # Verify statement 1 insights are gone
    insights_stmt1 = await client.get(f"/api/insights?statement_id={stmt1_id}")
    assert insights_stmt1.json()["total_count"] == 0
    assert len(insights_stmt1.json()["insights"]) == 0

    # Verify statement 2 transactions remain intact
    txns_stmt2 = await client.get(f"/api/transactions?statement_id={stmt2_id}")
    assert len(txns_stmt2.json()) == 2

    # ----------------------------------------------------
    # Step 8: Total Data Reset (Danger Zone Purge)
    # ----------------------------------------------------
    final_reset = await client.delete("/api/data/reset")
    assert final_reset.status_code == 200
    audit = final_reset.json()
    assert audit["status"] == "success"
    assert audit["deleted_statements"] >= 1
    assert audit["deleted_transactions"] >= 2

    # Verify global database is 100% clean
    all_stmts = await client.get("/api/statements")
    assert len(all_stmts.json()) == 0

    all_txns = await client.get("/api/transactions")
    assert len(all_txns.json()) == 0

    all_insights = await client.get("/api/insights")
    assert all_insights.json()["total_count"] == 0
    assert len(all_insights.json()["insights"]) == 0
