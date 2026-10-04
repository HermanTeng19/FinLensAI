from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal

from app.models.models import Transaction
from app.schemas.schemas import (
    CategorySpending,
    FinancialSummary,
    MonthlyTrend,
    PeriodComparison,
)


def calculate_summary(
    transactions: Sequence[Transaction], currency: str = "CAD"
) -> FinancialSummary:
    income = Decimal("0.00")
    expenses = Decimal("0.00")

    for t in transactions:
        amt = Decimal(str(t.amount))
        if amt > 0:
            income += amt
        else:
            expenses += amt

    net = income + expenses  # expenses is negative

    return FinancialSummary(
        total_income=income,
        total_expenses=expenses,
        net_cash_flow=net,
        currency=currency,
        transaction_count=len(transactions),
    )


def calculate_category_breakdown(transactions: Sequence[Transaction]) -> list[CategorySpending]:
    cat_totals = defaultdict(lambda: Decimal("0.00"))
    cat_counts = defaultdict(int)

    for t in transactions:
        amt = Decimal(str(t.amount))
        if amt < 0:  # expenses only
            cat_totals[t.category] += abs(amt)
            cat_counts[t.category] += 1

    total_expense = sum(cat_totals.values()) if cat_totals else Decimal("0.00")

    breakdown: list[CategorySpending] = []
    for cat, total in cat_totals.items():
        pct = float((total / total_expense) * 100) if total_expense > 0 else 0.0
        breakdown.append(
            CategorySpending(
                category=cat,
                amount=total,
                percentage=round(pct, 2),
                transaction_count=cat_counts[cat],
            )
        )

    return sorted(breakdown, key=lambda x: x.amount, reverse=True)


def calculate_monthly_trends(transactions: Sequence[Transaction]) -> list[MonthlyTrend]:
    monthly_data = defaultdict(lambda: {"income": Decimal("0.00"), "expenses": Decimal("0.00")})

    for t in transactions:
        month_key = t.date.strftime("%Y-%m")
        amt = Decimal(str(t.amount))
        if amt > 0:
            monthly_data[month_key]["income"] += amt
        else:
            monthly_data[month_key]["expenses"] += amt

    trends: list[MonthlyTrend] = []
    for month_key in sorted(monthly_data.keys()):
        inc = monthly_data[month_key]["income"]
        exp = monthly_data[month_key]["expenses"]
        net = inc + exp
        trends.append(
            MonthlyTrend(
                month=month_key,
                total_income=inc,
                total_expenses=exp,
                net_cash_flow=net,
            )
        )

    return trends


def compare_periods(
    current_txns: Sequence[Transaction],
    previous_txns: Sequence[Transaction],
) -> PeriodComparison:
    curr_summary = calculate_summary(current_txns)
    prev_summary = calculate_summary(previous_txns)

    curr_exp = abs(curr_summary.total_expenses)
    prev_exp = abs(prev_summary.total_expenses)
    delta_exp = curr_exp - prev_exp

    if prev_exp > 0:
        delta_exp_pct = float(((curr_exp - prev_exp) / prev_exp) * 100)
    else:
        delta_exp_pct = 100.0 if curr_exp > 0 else 0.0

    curr_inc = curr_summary.total_income
    prev_inc = prev_summary.total_income
    delta_inc = curr_inc - prev_inc

    # Determine which categories increased the most
    curr_cats = {c.category: c.amount for c in calculate_category_breakdown(current_txns)}
    prev_cats = {c.category: c.amount for c in calculate_category_breakdown(previous_txns)}

    increased_cats: list[CategorySpending] = []
    all_cat_names = set(curr_cats.keys()).union(set(prev_cats.keys()))

    for cat_name in all_cat_names:
        c_amt = curr_cats.get(cat_name, Decimal("0.00"))
        p_amt = prev_cats.get(cat_name, Decimal("0.00"))
        diff = c_amt - p_amt
        if diff > 0:
            pct = float((diff / p_amt) * 100) if p_amt > 0 else 100.0
            increased_cats.append(
                CategorySpending(
                    category=cat_name,
                    amount=diff,
                    percentage=round(pct, 2),
                    transaction_count=0,
                )
            )

    increased_cats.sort(key=lambda x: x.amount, reverse=True)

    return PeriodComparison(
        current_expenses=curr_summary.total_expenses,
        previous_expenses=prev_summary.total_expenses,
        delta_expenses=delta_exp,
        delta_percentage=round(delta_exp_pct, 2),
        current_income=curr_inc,
        previous_income=prev_inc,
        delta_income=delta_inc,
        top_increased_categories=increased_cats[:5],
    )


def get_top_transactions(
    transactions: Sequence[Transaction],
    limit: int = 10,
    txn_type: str = "expense",
) -> list[Transaction]:
    if txn_type == "expense":
        # Expenses are negative numbers, top expenses are those with greatest absolute value
        filtered = [t for t in transactions if Decimal(str(t.amount)) < 0]
        return sorted(filtered, key=lambda t: abs(Decimal(str(t.amount))), reverse=True)[:limit]
    elif txn_type == "income":
        filtered = [t for t in transactions if Decimal(str(t.amount)) > 0]
        return sorted(filtered, key=lambda t: Decimal(str(t.amount)), reverse=True)[:limit]
    else:
        return sorted(transactions, key=lambda t: abs(Decimal(str(t.amount))), reverse=True)[:limit]
