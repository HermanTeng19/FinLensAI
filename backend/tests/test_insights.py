import uuid
from datetime import date
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Statement, Transaction, Insight
from app.services.insights.engine import generate_insights, get_insights


@pytest.fixture
async def seed_insights_data(db_session: AsyncSession):
    stmt = Statement(
        id=uuid.uuid4(),
        filename="rbc_aug_sep_2026.pdf",
        file_hash="insight_hash_999",
        file_format="pdf",
        status="completed",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 9, 30),
        total_transactions=12,
    )
    db_session.add(stmt)

    txns = [
        # August baseline
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 8, 1),
            merchant="Acme Corp",
            original_description="PAYROLL DIRECT DEPOSIT",
            amount=Decimal("3500.00"),
            currency="CAD",
            category="Income",
            transaction_type="income",
            confidence=0.99,
        ),
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
            date=date(2026, 8, 16),
            merchant="Spotify",
            original_description="SPOTIFY PREMIUM",
            amount=Decimal("-11.99"),
            currency="CAD",
            category="Entertainment",
            transaction_type="expense",
            confidence=0.99,
        ),
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 8, 18),
            merchant="Safeway",
            original_description="SAFEWAY #2104",
            amount=Decimal("-120.00"),
            currency="CAD",
            category="Food",
            transaction_type="expense",
            confidence=0.95,
        ),
        # September: Spikes and large purchase
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 9, 1),
            merchant="Acme Corp",
            original_description="PAYROLL DIRECT DEPOSIT",
            amount=Decimal("3500.00"),
            currency="CAD",
            category="Income",
            transaction_type="income",
            confidence=0.99,
        ),
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
            merchant="Spotify",
            original_description="SPOTIFY PREMIUM",
            amount=Decimal("-11.99"),
            currency="CAD",
            category="Entertainment",
            transaction_type="expense",
            confidence=0.99,
        ),
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 9, 17),
            merchant="Whole Foods",
            original_description="WHOLEFDS MKT",
            amount=Decimal("-280.00"),
            currency="CAD",
            category="Food",
            transaction_type="expense",
            confidence=0.95,
        ),
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 9, 20),
            merchant="Apple Store",
            original_description="APPLE STORE #R102",
            amount=Decimal("-1299.00"),
            currency="CAD",
            category="Shopping",
            transaction_type="expense",
            confidence=0.99,
        ),
        # Duplicate anomaly: two identical charges on the same day
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 9, 25),
            merchant="Starbucks",
            original_description="STARBUCKS #110",
            amount=Decimal("-18.50"),
            currency="CAD",
            category="Food",
            transaction_type="expense",
            confidence=0.99,
        ),
        Transaction(
            id=uuid.uuid4(),
            statement_id=stmt.id,
            date=date(2026, 9, 25),
            merchant="Starbucks",
            original_description="STARBUCKS #110",
            amount=Decimal("-18.50"),
            currency="CAD",
            category="Food",
            transaction_type="expense",
            confidence=0.99,
        ),
    ]

    for t in txns:
        db_session.add(t)

    await db_session.commit()
    return stmt, txns


@pytest.mark.asyncio
async def test_insights_generation_and_grounding(db_session: AsyncSession, seed_insights_data):
    stmt, txns = seed_insights_data

    insights = await generate_insights(db_session, statement_id=stmt.id)
    assert len(insights) > 0

    categories = {i.category for i in insights}
    # Check that key insight rules triggered
    assert "cash_flow" in categories
    assert "spending_spike" in categories or "large_purchase" in categories
    assert "subscription" in categories or "unusual_transaction" in categories

    # Verify that every generated insight is strictly grounded with supporting transactions
    for ins in insights:
        assert len(ins.supporting_transactions) > 0
        for st in ins.supporting_transactions:
            assert st.merchant != ""
            assert st.date is not None
            assert st.amount != Decimal("0.00")

    # Verify DB persistence
    res = await db_session.execute(select(Insight).where(Insight.statement_id == stmt.id))
    db_items = res.scalars().all()
    assert len(db_items) == len(insights)


@pytest.mark.asyncio
async def test_insights_api_endpoints(client: AsyncClient, seed_insights_data):
    stmt, _ = seed_insights_data

    # 1. GET /api/insights
    resp = await client.get(f"/api/insights?statement_id={stmt.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] > 0
    assert "insights" in data
    assert len(data["insights"]) == data["total_count"]
    assert data["warning_count"] + data["positive_count"] + data["info_count"] == data["total_count"]

    first_card = data["insights"][0]
    assert "title" in first_card
    assert "content" in first_card
    assert "supporting_transactions" in first_card
    assert len(first_card["supporting_transactions"]) > 0

    # 2. POST /api/insights/generate
    post_resp = await client.post("/api/insights/generate", json={"statement_id": str(stmt.id)})
    assert post_resp.status_code == 200
    post_data = post_resp.json()
    assert post_data["total_count"] == data["total_count"]


@pytest.mark.asyncio
async def test_insights_cascade_deletion(db_session: AsyncSession, seed_insights_data):
    stmt, _ = seed_insights_data

    # Ensure insights are in DB
    await generate_insights(db_session, statement_id=stmt.id)
    res = await db_session.execute(select(Insight).where(Insight.statement_id == stmt.id))
    assert len(res.scalars().all()) > 0

    # Delete statement
    await db_session.delete(stmt)
    await db_session.commit()

    # Verify insights are cascaded and wiped
    res_after = await db_session.execute(select(Insight).where(Insight.statement_id == stmt.id))
    assert len(res_after.scalars().all()) == 0
