from decimal import Decimal
import math
from typing import Sequence, List, Dict
from collections import defaultdict
from app.models.models import Transaction
from app.schemas.schemas import UnusualTransaction


def detect_unusual_transactions(
    transactions: Sequence[Transaction],
    large_expense_threshold: Decimal = Decimal("500.00"),
) -> List[UnusualTransaction]:
    """
    Detects potential duplicate charges, statistical category outliers,
    and exceptionally large expenses.
    """
    anomalies: List[UnusualTransaction] = []
    seen_ids = set()

    # Filter only expenses
    expenses = [t for t in transactions if Decimal(str(t.amount)) < 0]

    # --- 1. Potential Duplicate Charges (Within 48 hours, same merchant & exact amount) ---
    merchant_map: Dict[str, List[Transaction]] = defaultdict(list)
    for t in expenses:
        m = (t.merchant or "").strip()
        if m:
            merchant_map[m].append(t)

    for merchant, txns in merchant_map.items():
        if len(txns) < 2:
            continue
        sorted_txns = sorted(txns, key=lambda x: x.date)
        for i in range(len(sorted_txns) - 1):
            t1 = sorted_txns[i]
            t2 = sorted_txns[i + 1]
            days_diff = abs((t2.date - t1.date).days)
            if days_diff <= 2 and t1.amount == t2.amount:
                if t2.id not in seen_ids:
                    seen_ids.add(t2.id)
                    anomalies.append(
                        UnusualTransaction(
                            transaction_id=t2.id,
                            date=t2.date,
                            merchant=merchant,
                            amount=t2.amount,
                            category=t2.category,
                            anomaly_type="duplicate_charge",
                            reason=f"Potential duplicate charge: identical amount of ${abs(t2.amount):.2f} charged twice within {days_diff} day(s).",
                            severity="high",
                        )
                    )

    # --- 2. Category Statistical Outliers ---
    cat_expenses: Dict[str, List[Transaction]] = defaultdict(list)
    for t in expenses:
        cat_expenses[t.category].append(t)

    for cat, txns in cat_expenses.items():
        if len(txns) < 4:
            continue
        amounts = sorted([float(abs(Decimal(str(t.amount)))) for t in txns])
        n = len(amounts)
        median = amounts[n // 2] if n % 2 == 1 else (amounts[n // 2 - 1] + amounts[n // 2]) / 2.0

        mean = sum(amounts) / n
        variance = sum((x - mean) ** 2 for x in amounts) / (n - 1)
        stddev = math.sqrt(variance)

        for t in txns:
            amt = float(abs(Decimal(str(t.amount))))
            is_outlier = False
            if stddev > 1.0 and amt > (mean + 2.0 * stddev):
                is_outlier = True
            elif median > 0 and amt > 3.0 * median and (amt - median) >= 50.0:
                is_outlier = True

            if is_outlier and t.id not in seen_ids:
                seen_ids.add(t.id)
                severity = "high" if (median > 0 and amt > 5.0 * median) or (stddev > 1.0 and amt > mean + 3.0 * stddev) else "medium"
                anomalies.append(
                    UnusualTransaction(
                        transaction_id=t.id,
                        date=t.date,
                        merchant=t.merchant,
                        amount=t.amount,
                        category=t.category,
                        anomaly_type="category_outlier",
                        reason=f"Expense of ${amt:.2f} is significantly above typical {cat} spending (typical: ${median:.2f}).",
                        severity=severity,
                    )
                )

    # --- 3. Large Single Expense (exceeding large_expense_threshold) ---
    for t in expenses:
        amt = abs(Decimal(str(t.amount)))
        if amt >= large_expense_threshold and t.id not in seen_ids:
            seen_ids.add(t.id)
            anomalies.append(
                UnusualTransaction(
                    transaction_id=t.id,
                    date=t.date,
                    merchant=t.merchant,
                    amount=t.amount,
                    category=t.category,
                    anomaly_type="large_expense",
                    reason=f"Large expense of ${amt:.2f} exceeds threshold (${large_expense_threshold:.2f}).",
                    severity="medium",
                )
            )

    return sorted(anomalies, key=lambda a: a.date, reverse=True)
