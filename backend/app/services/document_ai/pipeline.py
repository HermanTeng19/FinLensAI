import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ProcessingJob, Statement, Transaction
from app.services.document_ai.categorizer import Categorizer
from app.services.document_ai.merchant_normalizer import MerchantNormalizer
from app.services.document_ai.parser import (
    CSVParser,
    ExtractedTransactionCandidate,
    PDFParser,
)


async def process_statement_pipeline(
    db: AsyncSession,
    statement_id: uuid.UUID,
    file_bytes: bytes,
    file_format: str,
) -> int:
    """
    Executes Document AI pipeline:
    Extraction -> Validation -> Merchant Normalization -> AI Categorization -> Persistence
    """
    # 1. Fetch statement
    stmt_result = await db.execute(select(Statement).where(Statement.id == statement_id))
    statement = stmt_result.scalar_one_or_none()
    if not statement:
        raise ValueError(f"Statement {statement_id} not found.")

    statement.status = "processing"
    job = ProcessingJob(
        statement_id=statement_id,
        status="processing",
        started_at=datetime.now(UTC),
    )
    db.add(job)
    await db.commit()

    try:
        # 2. Document extraction
        candidates: list[ExtractedTransactionCandidate] = []
        if file_format.lower() == "pdf":
            candidates = PDFParser.parse(file_bytes)
        elif file_format.lower() == "csv":
            candidates = CSVParser.parse(file_bytes)
        else:
            raise ValueError(f"Unsupported format {file_format}")

        created_txns: list[Transaction] = []

        # 3 & 4. Normalization and Categorization
        for c in candidates:
            norm_merchant, m_conf = MerchantNormalizer.normalize(c.original_description)
            cat, subcat, c_conf, txn_type = Categorizer.classify(
                merchant=norm_merchant,
                original_description=c.original_description,
                amount=c.amount,
            )

            # Combined confidence score
            overall_confidence = round((m_conf + c_conf) / 2.0, 2)

            txn = Transaction(
                statement_id=statement.id,
                user_id=statement.user_id,
                date=c.date,
                merchant=norm_merchant,
                original_description=c.original_description,
                amount=c.amount,
                currency=c.currency,
                transaction_type=txn_type,
                category=cat,
                subcategory=subcat,
                confidence=overall_confidence,
                source_page=c.source_page,
            )
            created_txns.append(txn)
            db.add(txn)

        # 5. Update statement metadata
        statement.total_transactions = len(created_txns)
        statement.status = "completed"
        if created_txns:
            statement.period_start = min(t.date for t in created_txns)
            statement.period_end = max(t.date for t in created_txns)

        job.status = "completed"
        job.completed_at = datetime.now(UTC)

        await db.commit()

        # Phase 9: Automatically generate insights for the newly ingested statement
        try:
            from app.services.insights.engine import generate_insights

            await generate_insights(db, statement_id=statement.id)
        except Exception:
            pass  # Non-blocking for ingestion pipeline

        return len(created_txns)

    except Exception as e:
        await db.rollback()
        statement.status = "failed"
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.now(UTC)
        await db.commit()
        raise e
