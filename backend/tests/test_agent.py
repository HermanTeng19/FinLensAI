import pytest
from decimal import Decimal
from datetime import date
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Transaction, Statement
from app.services.agent.tools import (
    search_transactions,
    get_transaction_details,
    get_spending_by_category,
    compare_periods,
    get_top_transactions,
    detect_recurring_transactions,
    detect_unusual_transactions,
    get_monthly_summary,
    TOOL_DEFINITIONS,
)
from app.services.agent.agent import query_financial_agent


@pytest.fixture
async def seed_agent_data(db_session: AsyncSession):
    stmt = Statement(
        id=uuid.uuid4(),
        filename="agent_test_statement.csv",
        file_hash="mock_hash_agent_12345",
        file_format="csv",
        status="completed",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 9, 30),
        total_transactions=7,
    )
    db_session.add(stmt)
    await db_session.flush()

    txns = [
        # August
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 8, 15),
            merchant="Netflix",
            original_description="NETFLIX.COM",
            amount=Decimal("-16.99"),
            currency="CAD",
            category="Entertainment",
            transaction_type="expense",
            confidence=0.99,
        ),
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 8, 20),
            merchant="Safeway",
            original_description="SAFEWAY #2104",
            amount=Decimal("-150.00"),
            currency="CAD",
            category="Food",
            transaction_type="expense",
            confidence=0.95,
        ),
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 8, 30),
            merchant="Acme Corp",
            original_description="PAYROLL DIRECT DEP",
            amount=Decimal("3000.00"),
            currency="CAD",
            category="Income",
            transaction_type="income",
            confidence=0.98,
        ),
        # September
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 9, 15),
            merchant="Netflix",
            original_description="NETFLIX.COM",
            amount=Decimal("-16.99"),
            currency="CAD",
            category="Entertainment",
            transaction_type="expense",
            confidence=0.99,
        ),
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 9, 16),
            merchant="Starbucks",
            original_description="STARBUCKS #112",
            amount=Decimal("-6.75"),
            currency="CAD",
            category="Food",
            transaction_type="expense",
            confidence=0.99,
        ),
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 9, 17),
            merchant="Starbucks",
            original_description="STARBUCKS #112",
            amount=Decimal("-6.75"),
            currency="CAD",
            category="Food",
            transaction_type="expense",
            confidence=0.99,
        ),
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 9, 20),
            merchant="Apple Store",
            original_description="APPLE.COM/BILL",
            amount=Decimal("-1299.00"),
            currency="CAD",
            category="Shopping",
            transaction_type="expense",
            confidence=0.99,
        ),
    ]

    for t in txns:
        db_session.add(t)

    await db_session.commit()
    return txns


def test_tool_definitions_schema_conformance():
    assert len(TOOL_DEFINITIONS) == 8
    tool_names = {t["function"]["name"] for t in TOOL_DEFINITIONS}
    expected = {
        "search_transactions",
        "get_transaction_details",
        "get_spending_by_category",
        "compare_periods",
        "get_top_transactions",
        "detect_recurring_transactions",
        "detect_unusual_transactions",
        "get_monthly_summary",
    }
    assert tool_names == expected
    for td in TOOL_DEFINITIONS:
        assert "description" in td["function"]
        assert "parameters" in td["function"]


@pytest.mark.asyncio
async def test_eight_individual_financial_tools(db_session: AsyncSession, seed_agent_data):
    txns = seed_agent_data
    sample_txn = txns[0]

    # 1. search_transactions
    res_search = await search_transactions(db_session, query="Netflix")
    assert len(res_search) == 2
    assert res_search[0]["merchant"] == "Netflix"

    # 2. get_transaction_details
    res_detail = await get_transaction_details(db_session, transaction_id=str(sample_txn.id))
    assert res_detail["merchant"] == "Netflix"
    assert res_detail["amount"] == "-16.99"

    # 3. get_spending_by_category
    res_cat = await get_spending_by_category(db_session, category="Food")
    assert float(res_cat["total_spending"]) > 0
    assert res_cat["requested_category"] == "Food"

    # 4. compare_periods
    res_comp = await compare_periods(
        db_session,
        curr_start="2026-09-01",
        curr_end="2026-09-30",
        prev_start="2026-08-01",
        prev_end="2026-08-31",
    )
    assert "current_expenses" in res_comp
    assert "delta_expenses" in res_comp

    # 5. get_top_transactions
    res_top = await get_top_transactions(db_session, limit=2, txn_type="expense")
    assert len(res_top) == 2
    assert res_top[0]["merchant"] == "Apple Store"

    # 6. detect_recurring_transactions
    res_rec = await detect_recurring_transactions(db_session)
    assert any(r["merchant"] == "Netflix" for r in res_rec)

    # 7. detect_unusual_transactions
    res_un = await detect_unusual_transactions(db_session)
    anomaly_types = {a["anomaly_type"] for a in res_un}
    assert "duplicate_charge" in anomaly_types
    assert "large_expense" in anomaly_types

    # 8. get_monthly_summary
    res_sum = await get_monthly_summary(db_session, month="2026-08")
    assert Decimal(res_sum["total_income"]) == Decimal("3000.00")
    assert Decimal(res_sum["total_expenses"]) == Decimal("-166.99")


@pytest.mark.asyncio
async def test_agent_grounded_natural_language_queries(db_session: AsyncSession, seed_agent_data):
    # Query 1: Recurring
    q1 = await query_financial_agent(db_session, "What recurring subscriptions do I have?")
    assert q1.grounded is True
    assert len(q1.tool_calls) == 1
    assert q1.tool_calls[0].tool_name == "detect_recurring_transactions"
    assert "Netflix" in q1.response

    # Query 2: Unusual
    q2 = await query_financial_agent(db_session, "Which transactions look unusual?")
    assert q2.grounded is True
    assert q2.tool_calls[0].tool_name == "detect_unusual_transactions"
    assert "Starbucks" in q2.response or "Apple" in q2.response

    # Query 3: Top Expenses
    q3 = await query_financial_agent(db_session, "What were my largest purchases?")
    assert q3.grounded is True
    assert q3.tool_calls[0].tool_name == "get_top_transactions"
    assert "Apple Store" in q3.response

    # Query 4: Dining spending
    q4 = await query_financial_agent(db_session, "How much did I spend on food and restaurants?")
    assert q4.grounded is True
    assert q4.tool_calls[0].tool_name == "get_spending_by_category"
    assert "Food" in q4.response


@pytest.mark.asyncio
async def test_agent_api_endpoints(client: AsyncClient, seed_agent_data):
    # 1. Tools endpoint
    tools_res = await client.get("/api/agent/tools")
    assert tools_res.status_code == 200
    tools = tools_res.json()
    assert len(tools) == 8

    # 2. Query endpoint
    query_payload = {
        "message": "What recurring bills or subscriptions do I have?",
        "history": [],
    }
    chat_res = await client.post("/api/agent/query", json=query_payload)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["grounded"] is True
    assert len(chat_data["tool_calls"]) >= 1
    assert "Netflix" in chat_data["response"]
