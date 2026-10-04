import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Insight, Transaction
from app.schemas.schemas import (
    InsightCardSchema,
    SupportingTransactionSchema,
)
from app.services.analytics.anomalies import detect_unusual_transactions
from app.services.analytics.engine import (
    calculate_category_breakdown,
    calculate_summary,
    compare_periods,
)
from app.services.analytics.recurring import detect_recurring_transactions


def _to_supporting_schema(t: Transaction) -> SupportingTransactionSchema:
    return SupportingTransactionSchema(
        id=t.id,
        date=t.date,
        merchant=t.merchant,
        amount=Decimal(str(t.amount)),
        category=t.category,
    )


async def generate_insights(
    db: AsyncSession, statement_id: uuid.UUID | None = None
) -> list[InsightCardSchema]:
    """
    Deterministically generates grounded financial insights for a given statement
    (or across all transactions if statement_id is None).
    Persists generated insights into PostgreSQL.
    """
    stmt_q = select(Transaction).order_by(Transaction.date.desc())
    if statement_id:
        stmt_q = stmt_q.where(Transaction.statement_id == statement_id)

    res = await db.execute(stmt_q)
    transactions: Sequence[Transaction] = res.scalars().all()

    if not transactions:
        return []

    # Map transaction lookup by id for quick retrieval
    txn_map: dict[uuid.UUID, Transaction] = {t.id: t for t in transactions}

    generated: list[InsightCardSchema] = []
    now = datetime.now(UTC)

    # 1. Cash Flow & Savings Insight
    summary = calculate_summary(transactions)
    income = summary.total_income
    expenses = abs(summary.total_expenses)
    net = summary.net_cash_flow

    expense_txns = sorted(
        [t for t in transactions if Decimal(str(t.amount)) < 0],
        key=lambda x: abs(Decimal(str(x.amount))),
        reverse=True,
    )
    income_txns = sorted(
        [t for t in transactions if Decimal(str(t.amount)) > 0],
        key=lambda x: Decimal(str(x.amount)),
        reverse=True,
    )

    if net < Decimal("0.00"):
        supporting = [_to_supporting_schema(t) for t in expense_txns[:3]]
        generated.append(
            InsightCardSchema(
                id=uuid.uuid4(),
                statement_id=statement_id,
                insight_type="warning",
                category="cash_flow",
                title="Deficit Alert: Expenses Exceeded Income",
                content=(
                    f"During this period, your total expenses (${expenses:,.2f}) exceeded your income "
                    f"(${income:,.2f}) by ${abs(net):,.2f}. Review high-discretionary expenses to restore positive cash flow."
                ),
                severity="high",
                metric=f"-${abs(net):,.2f}",
                supporting_transactions=supporting,
                metadata={
                    "total_income": str(income),
                    "total_expenses": str(expenses),
                    "net_cash_flow": str(net),
                },
                generated_at=now,
            )
        )
    elif income > Decimal("0.00"):
        savings_rate = float((net / income) * 100)
        supporting = [_to_supporting_schema(t) for t in (income_txns[:2] + expense_txns[:1])]
        generated.append(
            InsightCardSchema(
                id=uuid.uuid4(),
                statement_id=statement_id,
                insight_type="positive",
                category="cash_flow",
                title=f"Positive Cash Flow: Saved ${net:,.2f}",
                content=(
                    f"You achieved a healthy net surplus of ${net:,.2f} with an effective savings rate "
                    f"of {savings_rate:.1f}%. Total income was ${income:,.2f} against ${expenses:,.2f} in expenses."
                ),
                severity="low",
                metric=f"+{savings_rate:.1f}% Saved",
                supporting_transactions=supporting,
                metadata={
                    "total_income": str(income),
                    "total_expenses": str(expenses),
                    "net_cash_flow": str(net),
                    "savings_rate": savings_rate,
                },
                generated_at=now,
            )
        )

    # 2. Category Spending Spikes & Significant Changes
    # Group transactions by month
    by_month: dict[str, list[Transaction]] = defaultdict(list)
    for t in transactions:
        m_key = t.date.strftime("%Y-%m")
        by_month[m_key].append(t)

    sorted_months = sorted(by_month.keys())
    if len(sorted_months) >= 2:
        curr_m = sorted_months[-1]
        prev_m = sorted_months[-2]
        comparison = compare_periods(by_month[curr_m], by_month[prev_m])

        # Check for category spikes
        if comparison.top_increased_categories:
            top_spike = comparison.top_increased_categories[0]
            # Find matching transactions for top spike category in current month
            spike_txns = [
                t
                for t in by_month[curr_m]
                if t.category == top_spike.category and Decimal(str(t.amount)) < 0
            ]
            spike_txns = sorted(spike_txns, key=lambda x: abs(Decimal(str(x.amount))), reverse=True)

            if top_spike.percentage >= 15.0 or top_spike.amount >= Decimal("50.00"):
                generated.append(
                    InsightCardSchema(
                        id=uuid.uuid4(),
                        statement_id=statement_id,
                        insight_type="warning",
                        category="spending_spike",
                        title=f"{top_spike.category} Spending Increased by {top_spike.percentage:.1f}%",
                        content=(
                            f"Spending in '{top_spike.category}' totaled ${top_spike.amount:,.2f} in {curr_m}, "
                            f"representing a significant increase over the previous period."
                        ),
                        severity="medium",
                        metric=f"+{top_spike.percentage:.1f}%",
                        supporting_transactions=[_to_supporting_schema(t) for t in spike_txns[:3]],
                        metadata={
                            "category": top_spike.category,
                            "current_amount": str(top_spike.amount),
                            "percentage": top_spike.percentage,
                        },
                        generated_at=now,
                    )
                )

    # 3. Unusual & Outlier Transactions
    unusual_alerts = detect_unusual_transactions(transactions)
    if unusual_alerts:
        supporting_unusual: list[SupportingTransactionSchema] = []
        for alert in unusual_alerts[:5]:
            matched = txn_map.get(alert.transaction_id)
            if matched:
                supporting_unusual.append(_to_supporting_schema(matched))

        high_count = sum(1 for a in unusual_alerts if a.severity == "high")
        severity_label = "high" if high_count > 0 else "medium"
        primary_reason = unusual_alerts[0].reason

        generated.append(
            InsightCardSchema(
                id=uuid.uuid4(),
                statement_id=statement_id,
                insight_type="warning",
                category="unusual_transaction",
                title=f"Unusual Activity Detected ({len(unusual_alerts)} Transactions)",
                content=(
                    f"FinLens AI detected {len(unusual_alerts)} unusual transaction(s) deviating from typical behavior. "
                    f"Primary flag: {primary_reason}."
                ),
                severity=severity_label,
                metric=f"{len(unusual_alerts)} Flagged",
                supporting_transactions=supporting_unusual,
                metadata={
                    "unusual_count": len(unusual_alerts),
                    "high_severity_count": high_count,
                },
                generated_at=now,
            )
        )

    # 4. Recurring Subscriptions & Monthly Bills
    all_recurring = detect_recurring_transactions(transactions)
    recurring_items = [r for r in all_recurring if r.category != "Income"]
    if recurring_items:
        monthly_total = sum(
            (
                r.expected_amount
                for r in recurring_items
                if r.is_subscription or r.frequency == "monthly"
            ),
            Decimal("0.00"),
        )
        supporting_recurring: list[SupportingTransactionSchema] = []
        for rec in recurring_items:
            # find latest transaction for this merchant
            merchant_txns = [t for t in transactions if t.merchant.lower() == rec.merchant.lower()]
            if merchant_txns:
                supporting_recurring.append(_to_supporting_schema(merchant_txns[0]))

        generated.append(
            InsightCardSchema(
                id=uuid.uuid4(),
                statement_id=statement_id,
                insight_type="info",
                category="subscription",
                title=f"{len(recurring_items)} Active Subscriptions & Bills Detected",
                content=(
                    f"You have {len(recurring_items)} active recurring payment(s) "
                    f"totaling approximately ${monthly_total:,.2f}/month. Review these to cancel unused subscriptions."
                ),
                severity="low",
                metric=f"${monthly_total:,.2f}/mo",
                supporting_transactions=supporting_recurring[:4],
                metadata={
                    "count": len(recurring_items),
                    "monthly_total": str(monthly_total),
                },
                generated_at=now,
            )
        )

    # 5. Large Single Purchase Insights
    if expense_txns:
        top_expense = expense_txns[0]
        top_amt = abs(Decimal(str(top_expense.amount)))
        if expenses > Decimal("0.00"):
            top_pct = float((top_amt / expenses) * 100)
        else:
            top_pct = 0.0

        if top_amt >= Decimal("150.00") or top_pct >= 20.0:
            generated.append(
                InsightCardSchema(
                    id=uuid.uuid4(),
                    statement_id=statement_id,
                    insight_type="warning" if top_amt >= Decimal("500.00") else "info",
                    category="large_purchase",
                    title=f"Significant Purchase: ${top_amt:,.2f} at {top_expense.merchant}",
                    content=(
                        f"A single transaction of ${top_amt:,.2f} at {top_expense.merchant} on {top_expense.date} "
                        f"accounted for {top_pct:.1f}% of total period spending."
                    ),
                    severity="high" if top_amt >= Decimal("500.00") else "medium",
                    metric=f"${top_amt:,.2f}",
                    supporting_transactions=[_to_supporting_schema(top_expense)],
                    metadata={
                        "merchant": top_expense.merchant,
                        "amount": str(top_amt),
                        "percentage_of_expenses": round(top_pct, 2),
                    },
                    generated_at=now,
                )
            )

    # 6. Category Concentration Risk (Dominance)
    breakdown = calculate_category_breakdown(transactions)
    if breakdown and expenses > Decimal("0.00"):
        top_cat = breakdown[0]
        if top_cat.percentage >= 35.0:
            dominant_txns = [
                t
                for t in transactions
                if t.category == top_cat.category and Decimal(str(t.amount)) < 0
            ]
            dominant_txns = sorted(
                dominant_txns, key=lambda x: abs(Decimal(str(x.amount))), reverse=True
            )

            generated.append(
                InsightCardSchema(
                    id=uuid.uuid4(),
                    statement_id=statement_id,
                    insight_type="info",
                    category="category_dominance",
                    title=f"Concentration Risk: {top_cat.category} ({top_cat.percentage:.1f}%)",
                    content=(
                        f"{top_cat.percentage:.1f}% of total period expenditure (${top_cat.amount:,.2f}) "
                        f"occurred in the '{top_cat.category}' category across {top_cat.transaction_count} transaction(s)."
                    ),
                    severity="medium",
                    metric=f"{top_cat.percentage:.1f}% of Total",
                    supporting_transactions=[_to_supporting_schema(t) for t in dominant_txns[:3]],
                    metadata={
                        "category": top_cat.category,
                        "amount": str(top_cat.amount),
                        "percentage": top_cat.percentage,
                    },
                    generated_at=now,
                )
            )

    # Persist into database: clear existing insights for this statement (or user scope)
    del_stmt = delete(Insight)
    if statement_id:
        del_stmt = del_stmt.where(Insight.statement_id == statement_id)
    await db.execute(del_stmt)

    for item in generated:
        # Serialise supporting transactions to json
        supporting_json = [st.model_dump(mode="json") for st in item.supporting_transactions]
        db_insight = Insight(
            id=item.id,
            statement_id=item.statement_id,
            insight_type=item.insight_type,
            title=item.title,
            content=item.content,
            supporting_data={
                "category": item.category,
                "severity": item.severity,
                "metric": item.metric,
                "supporting_transactions": supporting_json,
                "metadata": item.metadata,
            },
            generated_at=item.generated_at,
        )
        db.add(db_insight)

    await db.commit()
    return generated


async def get_insights(
    db: AsyncSession, statement_id: uuid.UUID | None = None
) -> list[InsightCardSchema]:
    """
    Fetches persisted insights from PostgreSQL. If none exist, automatically generates them.
    """
    q = select(Insight).order_by(Insight.generated_at.desc())
    if statement_id:
        q = q.where(Insight.statement_id == statement_id)

    res = await db.execute(q)
    db_insights = res.scalars().all()

    if not db_insights:
        # Automatically generate on the fly
        return await generate_insights(db, statement_id=statement_id)

    results: list[InsightCardSchema] = []
    for d in db_insights:
        supp_data = d.supporting_data or {}
        raw_supp_txns = supp_data.get("supporting_transactions", [])
        supp_txns = [
            SupportingTransactionSchema(
                id=uuid.UUID(st["id"]),
                date=date.fromisoformat(st["date"]) if isinstance(st["date"], str) else st["date"],
                merchant=st["merchant"],
                amount=Decimal(str(st["amount"])),
                category=st["category"],
            )
            for st in raw_supp_txns
        ]

        results.append(
            InsightCardSchema(
                id=d.id,
                statement_id=d.statement_id,
                insight_type=d.insight_type,
                category=supp_data.get("category", "general"),
                title=d.title,
                content=d.content,
                severity=supp_data.get("severity", "medium"),
                metric=supp_data.get("metric"),
                supporting_transactions=supp_txns,
                metadata=supp_data.get("metadata", {}),
                generated_at=d.generated_at,
            )
        )

    return results
