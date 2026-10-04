import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Transaction
from app.services.analytics.anomalies import (
    detect_unusual_transactions as engine_detect_anomalies,
)
from app.services.analytics.engine import (
    calculate_category_breakdown,
    calculate_monthly_trends,
    calculate_summary,
)
from app.services.analytics.engine import (
    compare_periods as engine_compare_periods,
)
from app.services.analytics.engine import (
    get_top_transactions as engine_get_top_transactions,
)
from app.services.analytics.recurring import (
    detect_recurring_transactions as engine_detect_recurring,
)


def _parse_date(val: Any) -> date | None:
    if isinstance(val, date):
        return val
    if isinstance(val, str) and val.strip():
        try:
            return datetime.strptime(val.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _format_txn(t: Transaction) -> dict[str, Any]:
    return {
        "id": str(t.id),
        "date": t.date.isoformat(),
        "merchant": t.merchant,
        "original_description": t.original_description,
        "amount": str(t.amount),
        "currency": t.currency,
        "category": t.category,
        "subcategory": t.subcategory,
        "transaction_type": t.transaction_type,
    }


# ==========================================
# 1. search_transactions
# ==========================================
async def search_transactions(
    db: AsyncSession,
    query: str | None = None,
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search and filter user transactions by keyword, category, date range, or amount range.
    """
    stmt = select(Transaction)

    if query:
        pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                Transaction.merchant.ilike(pattern),
                Transaction.original_description.ilike(pattern),
                Transaction.category.ilike(pattern),
            )
        )

    if category:
        stmt = stmt.where(Transaction.category.ilike(f"%{category}%"))

    s_date = _parse_date(start_date)
    if s_date:
        stmt = stmt.where(Transaction.date >= s_date)

    e_date = _parse_date(end_date)
    if e_date:
        stmt = stmt.where(Transaction.date <= e_date)

    if min_amount is not None:
        stmt = stmt.where(Transaction.amount >= Decimal(str(min_amount)))

    if max_amount is not None:
        stmt = stmt.where(Transaction.amount <= Decimal(str(max_amount)))

    stmt = stmt.order_by(Transaction.date.desc()).limit(limit)
    result = await db.execute(stmt)
    txns = result.scalars().all()
    return [_format_txn(t) for t in txns]


# ==========================================
# 2. get_transaction_details
# ==========================================
async def get_transaction_details(
    db: AsyncSession,
    transaction_id: str,
) -> dict[str, Any]:
    """
    Retrieve comprehensive details for a specific transaction by its ID.
    """
    try:
        t_uuid = uuid.UUID(transaction_id)
    except ValueError:
        return {"error": f"Invalid UUID: {transaction_id}"}

    result = await db.execute(select(Transaction).where(Transaction.id == t_uuid))
    txn = result.scalar_one_or_none()
    if not txn:
        return {"error": f"Transaction not found: {transaction_id}"}

    return {
        **_format_txn(txn),
        "confidence": txn.confidence,
        "source_page": txn.source_page,
        "statement_id": str(txn.statement_id) if txn.statement_id else None,
        "created_at": txn.created_at.isoformat() if txn.created_at else None,
    }


# ==========================================
# 3. get_spending_by_category
# ==========================================
async def get_spending_by_category(
    db: AsyncSession,
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """
    Calculate deterministic total spending and breakdown by category over a date range.
    """
    stmt = select(Transaction)
    s_date = _parse_date(start_date)
    if s_date:
        stmt = stmt.where(Transaction.date >= s_date)
    e_date = _parse_date(end_date)
    if e_date:
        stmt = stmt.where(Transaction.date <= e_date)

    result = await db.execute(stmt)
    txns = result.scalars().all()

    breakdown = calculate_category_breakdown(txns)

    if category:
        cat_lower = category.strip().lower()
        matched = [c for c in breakdown if cat_lower in c.category.lower()]
        total_for_cat = sum(c.amount for c in matched)
        return {
            "requested_category": category,
            "total_spending": str(total_for_cat),
            "matches": [
                {
                    "category": c.category,
                    "amount": str(c.amount),
                    "percentage": c.percentage,
                    "transaction_count": c.transaction_count,
                }
                for c in matched
            ],
        }

    return {
        "categories": [
            {
                "category": c.category,
                "amount": str(c.amount),
                "percentage": c.percentage,
                "transaction_count": c.transaction_count,
            }
            for c in breakdown
        ]
    }


# ==========================================
# 4. compare_periods
# ==========================================
async def compare_periods(
    db: AsyncSession,
    curr_start: str,
    curr_end: str,
    prev_start: str,
    prev_end: str,
) -> dict[str, Any]:
    """
    Compare financial metrics and category spending between two distinct time periods.
    """
    cs, ce = _parse_date(curr_start), _parse_date(curr_end)
    ps, pe = _parse_date(prev_start), _parse_date(prev_end)

    if not cs or not ce or not ps or not pe:
        return {"error": "Invalid date format. Expected YYYY-MM-DD for all date parameters."}

    curr_res = await db.execute(
        select(Transaction).where(Transaction.date >= cs, Transaction.date <= ce)
    )
    prev_res = await db.execute(
        select(Transaction).where(Transaction.date >= ps, Transaction.date <= pe)
    )

    comp = engine_compare_periods(curr_res.scalars().all(), prev_res.scalars().all())

    return {
        "current_period": {"start": curr_start, "end": curr_end},
        "previous_period": {"start": prev_start, "end": prev_end},
        "current_expenses": str(comp.current_expenses),
        "previous_expenses": str(comp.previous_expenses),
        "delta_expenses": str(comp.delta_expenses),
        "delta_percentage": comp.delta_percentage,
        "current_income": str(comp.current_income),
        "previous_income": str(comp.previous_income),
        "delta_income": str(comp.delta_income),
        "top_increased_categories": [
            {
                "category": c.category,
                "amount_increase": str(c.amount),
                "percentage_increase": c.percentage,
            }
            for c in comp.top_increased_categories
        ],
    }


# ==========================================
# 5. get_top_transactions
# ==========================================
async def get_top_transactions(
    db: AsyncSession,
    limit: int = 5,
    txn_type: str = "expense",
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve the largest transactions (highest spending expenses or highest income).
    """
    stmt = select(Transaction)
    s_date = _parse_date(start_date)
    if s_date:
        stmt = stmt.where(Transaction.date >= s_date)
    e_date = _parse_date(end_date)
    if e_date:
        stmt = stmt.where(Transaction.date <= e_date)

    result = await db.execute(stmt)
    txns = result.scalars().all()
    top_txns = engine_get_top_transactions(txns, limit=limit, txn_type=txn_type)
    return [_format_txn(t) for t in top_txns]


# ==========================================
# 6. detect_recurring_transactions
# ==========================================
async def detect_recurring_transactions(
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """
    Analyze all transaction history to detect recurring subscriptions, bills, payroll, and periodic charges.
    """
    result = await db.execute(select(Transaction))
    txns = result.scalars().all()
    items = engine_detect_recurring(txns)

    return [
        {
            "merchant": item.merchant,
            "category": item.category,
            "frequency": item.frequency,
            "expected_amount": str(item.expected_amount),
            "last_date": item.last_date.isoformat(),
            "next_expected_date": item.next_expected_date.isoformat()
            if item.next_expected_date
            else None,
            "occurrence_count": item.occurrence_count,
            "confidence": item.confidence,
            "is_subscription": item.is_subscription,
        }
        for item in items
    ]


# ==========================================
# 7. detect_unusual_transactions
# ==========================================
async def detect_unusual_transactions(
    db: AsyncSession,
    threshold: float | None = None,
) -> list[dict[str, Any]]:
    """
    Detect financial anomalies including duplicate charges within 48h, statistical category outliers, and large spikes.
    """
    result = await db.execute(select(Transaction))
    txns = result.scalars().all()

    kwargs = {}
    if threshold is not None:
        kwargs["large_expense_threshold"] = Decimal(str(threshold))

    anomalies = engine_detect_anomalies(txns, **kwargs)

    return [
        {
            "transaction_id": str(a.transaction_id),
            "date": a.date.isoformat(),
            "merchant": a.merchant,
            "amount": str(a.amount),
            "category": a.category,
            "anomaly_type": a.anomaly_type,
            "reason": a.reason,
            "severity": a.severity,
        }
        for a in anomalies
    ]


# ==========================================
# 8. get_monthly_summary
# ==========================================
async def get_monthly_summary(
    db: AsyncSession,
    month: str | None = None,
) -> dict[str, Any]:
    """
    Get authoritative total income, expenses, and net cash flow for a specific month (e.g. '2026-09') or overall.
    """
    stmt = select(Transaction)
    result = await db.execute(stmt)
    txns = result.scalars().all()

    if month:
        target_month = month.strip()
        filtered = [t for t in txns if t.date.strftime("%Y-%m") == target_month]
        summary = calculate_summary(filtered)
        return {
            "month": target_month,
            "total_income": str(summary.total_income),
            "total_expenses": str(summary.total_expenses),
            "net_cash_flow": str(summary.net_cash_flow),
            "currency": summary.currency,
            "transaction_count": summary.transaction_count,
        }

    # Overall summary and monthly trends
    overall = calculate_summary(txns)
    trends = calculate_monthly_trends(txns)
    return {
        "overall": {
            "total_income": str(overall.total_income),
            "total_expenses": str(overall.total_expenses),
            "net_cash_flow": str(overall.net_cash_flow),
            "currency": overall.currency,
            "transaction_count": overall.transaction_count,
        },
        "trends": [
            {
                "month": t.month,
                "income": str(t.total_income),
                "expenses": str(t.total_expenses),
                "net_cash_flow": str(t.net_cash_flow),
            }
            for t in trends
        ],
    }


# ==========================================
# Tool Registry & JSON Schema Definitions
# ==========================================
TOOL_REGISTRY = {
    "search_transactions": search_transactions,
    "get_transaction_details": get_transaction_details,
    "get_spending_by_category": get_spending_by_category,
    "compare_periods": compare_periods,
    "get_top_transactions": get_top_transactions,
    "detect_recurring_transactions": detect_recurring_transactions,
    "detect_unusual_transactions": detect_unusual_transactions,
    "get_monthly_summary": get_monthly_summary,
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_transactions",
            "description": "Search and filter user transactions by keyword, merchant name, category, date range, or amount range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword for merchant or description.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category name filter (e.g. 'Food', 'Shopping').",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format.",
                    },
                    "end_date": {"type": "string", "description": "End date in YYYY-MM-DD format."},
                    "min_amount": {"type": "number", "description": "Minimum amount filter."},
                    "max_amount": {"type": "number", "description": "Maximum amount filter."},
                    "limit": {
                        "type": "integer",
                        "description": "Max number of transactions to return (default 20).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transaction_details",
            "description": "Retrieve comprehensive details for a specific transaction by its unique ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "The UUID of the transaction.",
                    },
                },
                "required": ["transaction_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_spending_by_category",
            "description": "Calculate deterministic total spending and breakdown by category over a date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional category name to filter (e.g. 'Food', 'Shopping', 'Travel').",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format.",
                    },
                    "end_date": {"type": "string", "description": "End date in YYYY-MM-DD format."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_periods",
            "description": "Compare financial metrics and category spending between two distinct time periods (e.g. this month vs last month).",
            "parameters": {
                "type": "object",
                "properties": {
                    "curr_start": {
                        "type": "string",
                        "description": "Current period start date (YYYY-MM-DD).",
                    },
                    "curr_end": {
                        "type": "string",
                        "description": "Current period end date (YYYY-MM-DD).",
                    },
                    "prev_start": {
                        "type": "string",
                        "description": "Previous period start date (YYYY-MM-DD).",
                    },
                    "prev_end": {
                        "type": "string",
                        "description": "Previous period end date (YYYY-MM-DD).",
                    },
                },
                "required": ["curr_start", "curr_end", "prev_start", "prev_end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_transactions",
            "description": "Retrieve the largest transactions (highest spending expenses or highest income) sorted deterministically by amount.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of transactions to return (default 5).",
                    },
                    "txn_type": {
                        "type": "string",
                        "enum": ["expense", "income"],
                        "description": "'expense' or 'income'.",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format.",
                    },
                    "end_date": {"type": "string", "description": "End date in YYYY-MM-DD format."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_recurring_transactions",
            "description": "Analyze transaction history to detect recurring subscriptions, bills, payroll, and periodic charges.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_unusual_transactions",
            "description": "Detect financial anomalies including duplicate charges within 48h, statistical category outliers, and large spikes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "number",
                        "description": "Optional custom dollar threshold for large expenses (default $500).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_summary",
            "description": "Get authoritative total income, expenses, and net cash flow for a specific month or overall.",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {
                        "type": "string",
                        "description": "Specific month in YYYY-MM format (e.g. '2026-09').",
                    },
                },
            },
        },
    },
]
