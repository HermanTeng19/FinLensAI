import uuid
from decimal import Decimal
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from app.core.database import get_db
from app.models.models import Transaction
from app.schemas.schemas import FinancialSummary, CategorySpending, MonthlyTrend

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

    income = Decimal("0.00")
    expenses = Decimal("0.00")

    for t in txns:
        if t.amount > 0:
            income += t.amount
        else:
            expenses += t.amount

    net_cash_flow = income + expenses  # expenses is negative

    return FinancialSummary(
        total_income=income,
        total_expenses=expenses,
        net_cash_flow=net_cash_flow,
        currency="CAD",
        transaction_count=len(txns),
    )


@router.get("/categories", response_model=List[CategorySpending])
async def get_category_spending(
    statement_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # Only calculate expenses for spending breakdown
    query = select(
        Transaction.category,
        func.sum(Transaction.amount).label("total_amount"),
        func.count(Transaction.id).label("txn_count"),
    ).where(Transaction.amount < 0)

    if statement_id:
        query = query.where(Transaction.statement_id == statement_id)

    query = query.group_by(Transaction.category)

    result = await db.execute(query)
    rows = result.all()

    total_expense = sum(abs(row.total_amount) for row in rows) if rows else Decimal("0.00")

    breakdown = []
    for row in rows:
        cat_amount = abs(row.total_amount)
        pct = float((cat_amount / total_expense) * 100) if total_expense > 0 else 0.0
        breakdown.append(
            CategorySpending(
                category=row.category,
                amount=cat_amount,
                percentage=round(pct, 2),
                transaction_count=row.txn_count,
            )
        )

    return sorted(breakdown, key=lambda x: x.amount, reverse=True)
