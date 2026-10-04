import uuid
from decimal import Decimal
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import Transaction
from app.schemas.schemas import (
    FinancialSummary,
    CategorySpending,
    MonthlyTrend,
    RecurringItem,
    UnusualTransaction,
    PeriodComparison,
    TransactionResponse,
)
from app.services.analytics.engine import (
    calculate_summary,
    calculate_category_breakdown,
    calculate_monthly_trends,
    compare_periods,
    get_top_transactions,
)
from app.services.analytics.recurring import detect_recurring_transactions
from app.services.analytics.anomalies import detect_unusual_transactions

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=FinancialSummary)
async def get_financial_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    statement_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction)
    if statement_id:
        query = query.where(Transaction.statement_id == statement_id)
    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)

    result = await db.execute(query)
    txns = result.scalars().all()
    return calculate_summary(txns)


@router.get("/categories", response_model=List[CategorySpending])
async def get_category_spending(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    statement_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction)
    if statement_id:
        query = query.where(Transaction.statement_id == statement_id)
    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)

    result = await db.execute(query)
    txns = result.scalars().all()
    return calculate_category_breakdown(txns)


@router.get("/monthly-trends", response_model=List[MonthlyTrend])
async def get_monthly_trends(
    statement_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction)
    if statement_id:
        query = query.where(Transaction.statement_id == statement_id)

    result = await db.execute(query)
    txns = result.scalars().all()
    return calculate_monthly_trends(txns)


@router.get("/recurring", response_model=List[RecurringItem])
async def get_recurring_transactions(
    statement_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction)
    if statement_id:
        query = query.where(Transaction.statement_id == statement_id)

    result = await db.execute(query)
    txns = result.scalars().all()
    return detect_recurring_transactions(txns)


@router.get("/unusual", response_model=List[UnusualTransaction])
async def get_unusual_transactions(
    statement_id: Optional[uuid.UUID] = Query(None),
    threshold: Optional[Decimal] = Query(None, description="Optional custom threshold for large expenses"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction)
    if statement_id:
        query = query.where(Transaction.statement_id == statement_id)

    result = await db.execute(query)
    txns = result.scalars().all()

    kwargs = {}
    if threshold is not None:
        kwargs["large_expense_threshold"] = threshold

    return detect_unusual_transactions(txns, **kwargs)


@router.get("/top", response_model=List[TransactionResponse])
async def get_top_spending_transactions(
    statement_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    txn_type: str = Query("expense", description="'expense' or 'income'"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Transaction)
    if statement_id:
        query = query.where(Transaction.statement_id == statement_id)

    result = await db.execute(query)
    txns = result.scalars().all()
    return get_top_transactions(txns, limit=limit, txn_type=txn_type)


@router.get("/comparison", response_model=PeriodComparison)
async def get_period_comparison(
    curr_start: date = Query(...),
    curr_end: date = Query(...),
    prev_start: date = Query(...),
    prev_end: date = Query(...),
    statement_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if curr_start > curr_end or prev_start > prev_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date.",
        )

    curr_query = select(Transaction).where(Transaction.date >= curr_start, Transaction.date <= curr_end)
    prev_query = select(Transaction).where(Transaction.date >= prev_start, Transaction.date <= prev_end)
    if statement_id:
        curr_query = curr_query.where(Transaction.statement_id == statement_id)
        prev_query = prev_query.where(Transaction.statement_id == statement_id)

    curr_res = await db.execute(curr_query)
    curr_txns = curr_res.scalars().all()

    prev_res = await db.execute(prev_query)
    prev_txns = prev_res.scalars().all()

    return compare_periods(curr_txns, prev_txns)

