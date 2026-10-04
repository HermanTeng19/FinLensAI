import logging
import uuid
from datetime import date
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.privacy import redact_sensitive_text, SensitiveDataFilter
from app.models.models import Insight, ProcessingJob, Statement, Transaction


def test_redact_sensitive_text_credit_cards():
    """Verify that credit card numbers in multiple formats are redacted."""
    # Standard 16-digit card with dashes
    text1 = "Payment made with card 4532-1234-5678-9012 at Starbucks"
    assert redact_sensitive_text(text1) == "Payment made with card [REDACTED_CARD] at Starbucks"

    # 16-digit card with spaces
    text2 = "Card ending in 5500 1234 5678 9010"
    assert redact_sensitive_text(text2) == "Card ending in [REDACTED_CARD]"

    # 15-digit Amex
    text3 = "Amex 3782-822463-10005 charged"
    assert redact_sensitive_text(text3) == "Amex [REDACTED_CARD] charged"

    # Plain non-card text should remain unaffected
    plain = "Uber trip on 2026-09-15 for $42.50"
    assert redact_sensitive_text(plain) == plain


def test_redact_sensitive_text_ssn_and_sin():
    """Verify that Canadian SINs and US SSNs are redacted."""
    # Canadian SIN
    sin_text = "Client SIN: 987-654-321 on tax document"
    assert redact_sensitive_text(sin_text) == "Client SIN: [REDACTED_ID] on tax document"

    # US SSN
    ssn_text = "SSN: 123-45-6789 verified"
    assert redact_sensitive_text(ssn_text) == "SSN: [REDACTED_ID] verified"


def test_redact_sensitive_text_bank_accounts():
    """Verify bank account numbers and transit codes are redacted."""
    bank_text = "Direct deposit from transit: 12345 account: 9876543210"
    redacted = redact_sensitive_text(bank_text)
    assert "[REDACTED_ACCOUNT]" in redacted
    assert "9876543210" not in redacted


def test_sensitive_data_logging_filter():
    """Verify that SensitiveDataFilter intercepts and redacts log messages and args."""
    filter_instance = SensitiveDataFilter()

    # Test record message redaction
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Transaction for card 4111-2222-3333-4444 completed",
        args=(),
        exc_info=None,
    )
    filter_instance.filter(record)
    assert record.msg == "Transaction for card [REDACTED_CARD] completed"

    # Test record args redaction
    record_with_args = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=12,
        msg="User %s with card %s",
        args=("Alice", "4111-2222-3333-4444"),
        exc_info=None,
    )
    filter_instance.filter(record_with_args)
    assert record_with_args.args[1] == "[REDACTED_CARD]"


@pytest.mark.asyncio
async def test_privacy_and_security_headers(client: AsyncClient):
    """Verify that zero-retention and security headers are injected into every response."""
    response = await client.get("/health")
    assert response.status_code == 200

    headers = response.headers
    assert "no-store" in headers.get("cache-control", "")
    assert "no-cache" in headers.get("pragma", "")
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("referrer-policy") == "no-referrer"
    assert "geolocation=()" in headers.get("permissions-policy", "")


@pytest.mark.asyncio
async def test_privacy_info_endpoint(client: AsyncClient):
    """Verify GET /api/data/privacy-info returns architectural privacy assertions."""
    response = await client.get("/api/data/privacy-info")
    assert response.status_code == 200
    data = response.json()
    assert data["bank_credentials_required"] is False
    assert data["in_memory_pdf_processing"] is True
    assert data["cascade_deletion_supported"] is True
    assert "Zero-Retention" in data["architecture"]


@pytest.mark.asyncio
async def test_statement_cascade_deletion(client: AsyncClient, db_session: AsyncSession):
    """Verify that deleting a single statement atomically cascades to transactions, insights, and jobs."""
    # 1. Create a Statement
    stmt = Statement(
        id=uuid.uuid4(),
        filename="cascade_test.pdf",
        file_hash="cascade_hash_001",
        file_format="pdf",
        status="completed",
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
        total_transactions=2,
    )
    db_session.add(stmt)

    # 2. Add Transactions
    t1 = Transaction(
        id=uuid.uuid4(),
        statement_id=stmt.id,
        date=date(2026, 9, 10),
        merchant="Cascade Merchant A",
        original_description="CASCADE TXN 1",
        amount=Decimal("-50.00"),
        currency="CAD",
        category="Dining",
        transaction_type="expense",
        confidence=0.99,
    )
    t2 = Transaction(
        id=uuid.uuid4(),
        statement_id=stmt.id,
        date=date(2026, 9, 15),
        merchant="Cascade Merchant B",
        original_description="CASCADE TXN 2",
        amount=Decimal("200.00"),
        currency="CAD",
        category="Income",
        transaction_type="income",
        confidence=0.99,
    )
    db_session.add_all([t1, t2])

    # 3. Add Insight
    insight = Insight(
        id=uuid.uuid4(),
        statement_id=stmt.id,
        insight_type="observation",
        title="Cascade Test Insight",
        content="Testing cascade removal",
    )
    db_session.add(insight)

    # 4. Add Job
    job = ProcessingJob(
        id=uuid.uuid4(),
        statement_id=stmt.id,
        status="completed",
    )
    db_session.add(job)

    await db_session.commit()

    # Verify records exist
    res_txns = (await db_session.execute(select(Transaction).where(Transaction.statement_id == stmt.id))).scalars().all()
    assert len(res_txns) == 2

    # 5. Call DELETE /api/statements/{stmt.id}
    del_res = await client.delete(f"/api/statements/{stmt.id}")
    assert del_res.status_code == 204

    # 6. Verify statement, transactions, insights, and jobs are all deleted
    chk_stmt = (await db_session.execute(select(Statement).where(Statement.id == stmt.id))).scalar_one_or_none()
    assert chk_stmt is None

    chk_txns = (await db_session.execute(select(Transaction).where(Transaction.statement_id == stmt.id))).scalars().all()
    assert len(chk_txns) == 0

    chk_insights = (await db_session.execute(select(Insight).where(Insight.statement_id == stmt.id))).scalars().all()
    assert len(chk_insights) == 0

    chk_jobs = (await db_session.execute(select(ProcessingJob).where(ProcessingJob.statement_id == stmt.id))).scalars().all()
    assert len(chk_jobs) == 0


@pytest.mark.asyncio
async def test_full_data_reset_purge(client: AsyncClient, db_session: AsyncSession):
    """Verify that DELETE /api/data/reset purges all records and returns audit metrics."""
    # Seed a batch of records
    s1 = Statement(
        id=uuid.uuid4(),
        filename="reset_test_1.pdf",
        file_hash="reset_hash_1",
        file_format="pdf",
        status="completed",
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
        total_transactions=1,
    )
    db_session.add(s1)

    t1 = Transaction(
        id=uuid.uuid4(),
        statement_id=s1.id,
        date=date(2026, 9, 5),
        merchant="Purge Store",
        original_description="PURGE TRANSACTION",
        amount=Decimal("-99.00"),
        currency="CAD",
        category="Shopping",
        transaction_type="expense",
        confidence=0.99,
    )
    db_session.add(t1)

    ins1 = Insight(
        id=uuid.uuid4(),
        statement_id=s1.id,
        insight_type="warning",
        title="Purge Warning",
        content="Will be erased",
    )
    db_session.add(ins1)

    job1 = ProcessingJob(
        id=uuid.uuid4(),
        statement_id=s1.id,
        status="completed",
    )
    db_session.add(job1)
    await db_session.commit()

    # Call DELETE /api/data/reset
    reset_res = await client.delete("/api/data/reset")
    assert reset_res.status_code == 200
    audit = reset_res.json()

    assert audit["status"] == "success"
    assert audit["deleted_statements"] >= 1
    assert audit["deleted_transactions"] >= 1
    assert audit["deleted_insights"] >= 1
    assert "permanently and irreversibly purged" in audit["message"]

    # Verify tables are completely empty
    all_stmts = (await db_session.execute(select(Statement))).scalars().all()
    all_txns = (await db_session.execute(select(Transaction))).scalars().all()
    all_insights = (await db_session.execute(select(Insight))).scalars().all()
    all_jobs = (await db_session.execute(select(ProcessingJob))).scalars().all()

    assert len(all_stmts) == 0
    assert len(all_txns) == 0
    assert len(all_insights) == 0
    assert len(all_jobs) == 0
