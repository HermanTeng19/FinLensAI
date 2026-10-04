import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import Transaction
from app.schemas.schemas import TransactionCreate, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    statement_id: uuid.UUID | None = Query(None, description="Filter by statement"),
    category: str | None = Query(None, description="Filter by category"),
    start_date: date | None = Query(None, description="Start date (inclusive)"),
    end_date: date | None = Query(None, description="End date (inclusive)"),
    merchant: str | None = Query(None, description="Search by merchant name"),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction)
    if statement_id:
        query = query.where(Transaction.statement_id == statement_id)
    if category:
        query = query.where(Transaction.category == category)
    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)
    if merchant:
        query = query.where(Transaction.merchant.ilike(f"%{merchant}%"))

    query = query.order_by(Transaction.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    return txn


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
):
    txn = Transaction(**payload.model_dump())
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return txn
