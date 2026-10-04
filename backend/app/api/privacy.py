"""FinLens AI Privacy & Data Purge Endpoints.

Provides:
- POST /api/data/reset and DELETE /api/data/reset: Irreversible, atomic cascade purge of all financial data.
- GET /api/data/privacy-info: Returns privacy architectural status, in-memory processing guarantees, and audit details.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import Insight, ProcessingJob, Statement, Transaction

router = APIRouter(prefix="/data", tags=["Privacy & Data Management"])


class DataResetAuditResponse(BaseModel):
    status: str = "success"
    deleted_statements: int
    deleted_transactions: int
    deleted_insights: int
    deleted_jobs: int
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PrivacyPolicyInfoResponse(BaseModel):
    architecture: str = "Zero-Retention & In-Memory Extraction"
    bank_credentials_required: bool = False
    in_memory_pdf_processing: bool = True
    unencrypted_files_stored_on_disk: bool = False
    log_redaction_enabled: bool = True
    cascade_deletion_supported: bool = True
    guarantee: str = (
        "FinLens AI does not require, store, or transmit your online banking credentials. "
        "Bank statements are analyzed in-memory and all derived financial intelligence can be "
        "completely and irreversibly wiped with one tap."
    )


async def execute_atomic_purge(db: AsyncSession) -> DataResetAuditResponse:
    """Executes an atomic purge of all statements, transactions, insights, and processing jobs."""
    # 1. Audit current counts before deletion
    stmt_count = (await db.execute(select(func.count(Statement.id)))).scalar_one() or 0
    txn_count = (await db.execute(select(func.count(Transaction.id)))).scalar_one() or 0
    insight_count = (await db.execute(select(func.count(Insight.id)))).scalar_one() or 0
    job_count = (await db.execute(select(func.count(ProcessingJob.id)))).scalar_one() or 0

    # 2. Delete all records within an atomic transaction
    # Deleting all Statements triggers cascade deletions on transactions, processing_jobs, and insights.
    # To guarantee clean tables even if unlinked records exist, explicitly purge each table.
    await db.execute(delete(Insight))
    await db.execute(delete(ProcessingJob))
    await db.execute(delete(Transaction))
    await db.execute(delete(Statement))

    await db.commit()

    return DataResetAuditResponse(
        status="success",
        deleted_statements=stmt_count,
        deleted_transactions=txn_count,
        deleted_insights=insight_count,
        deleted_jobs=job_count,
        message="All financial records, transactions, AI insights, and jobs have been permanently and irreversibly purged.",
        timestamp=datetime.now(UTC),
    )


@router.delete("/reset", response_model=DataResetAuditResponse)
async def reset_all_data_delete(db: AsyncSession = Depends(get_db)):
    """Permanently and irreversibly purges all uploaded statements, transactions, insights, and jobs."""
    return await execute_atomic_purge(db)


@router.post("/reset", response_model=DataResetAuditResponse)
async def reset_all_data_post(db: AsyncSession = Depends(get_db)):
    """Permanently and irreversibly purges all uploaded statements, transactions, insights, and jobs."""
    return await execute_atomic_purge(db)


@router.get("/privacy-info", response_model=PrivacyPolicyInfoResponse)
async def get_privacy_info():
    """Returns the privacy architectural principles and data security status of FinLens AI."""
    return PrivacyPolicyInfoResponse()
