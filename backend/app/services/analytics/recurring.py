from decimal import Decimal
from datetime import date, timedelta
from typing import Sequence, List, Dict
from collections import defaultdict
import uuid

from app.models.models import Transaction
from app.schemas.schemas import RecurringItem

KNOWN_SUBSCRIPTION_MERCHANTS = {
    "netflix",
    "spotify",
    "apple",
    "disney+",
    "youtube",
    "amazon prime",
    "openai",
    "chatgpt",
    "github",
    "dropbox",
    "icloud",
    "google storage",
    "anytime fitness",
    "goodlife",
    "fit4less",
    "equinox",
    "planet fitness",
    "telus",
    "rogers",
    "bell",
    "fido",
    "koodo",
    "freedom mobile",
    "bc hydro",
    "toronto hydro",
    "enbridge gas",
}


def _classify_frequency(avg_days: float) -> str:
    if 5.0 <= avg_days <= 9.0:
        return "weekly"
    elif 12.0 <= avg_days <= 17.0:
        return "bi-weekly"
    elif 25.0 <= avg_days <= 35.0:
        return "monthly"
    elif 80.0 <= avg_days <= 100.0:
        return "quarterly"
    elif 340.0 <= avg_days <= 390.0:
        return "annual"
    return "irregular"


def _estimate_next_date(last_date: date, frequency: str, avg_days: float) -> date:
    if frequency == "weekly":
        return last_date + timedelta(days=7)
    elif frequency == "bi-weekly":
        return last_date + timedelta(days=14)
    elif frequency == "monthly":
        # Approximate 30 days or next month same day
        return last_date + timedelta(days=round(avg_days if 28 <= avg_days <= 31 else 30))
    elif frequency == "quarterly":
        return last_date + timedelta(days=91)
    elif frequency == "annual":
        return last_date + timedelta(days=365)
    return last_date + timedelta(days=round(avg_days))


def detect_recurring_transactions(
    transactions: Sequence[Transaction],
    amount_tolerance: float = 0.08,
) -> List[RecurringItem]:
    """
    Detects recurring subscriptions, utilities, payroll, and periodic charges
    using deterministic interval and amount tolerance analysis.
    """
    # Group by merchant
    merchant_txns: Dict[str, List[Transaction]] = defaultdict(list)
    for t in transactions:
        m = (t.merchant or "").strip()
        if m:
            merchant_txns[m].append(t)

    recurring_items: List[RecurringItem] = []

    for merchant, txns in merchant_txns.items():
        if len(txns) < 2:
            continue

        # Sort chronologically
        sorted_txns = sorted(txns, key=lambda x: x.date)

        # Check intervals
        intervals: List[int] = []
        for i in range(len(sorted_txns) - 1):
            delta_days = (sorted_txns[i + 1].date - sorted_txns[i].date).days
            if delta_days > 0:
                intervals.append(delta_days)

        if not intervals:
            continue

        avg_interval = sum(intervals) / len(intervals)
        freq = _classify_frequency(avg_interval)

        # If irregular, skip unless known subscription merchant
        is_known_sub = merchant.lower() in KNOWN_SUBSCRIPTION_MERCHANTS
        if freq == "irregular" and not is_known_sub:
            continue

        if freq == "irregular" and is_known_sub:
            freq = "monthly"
            avg_interval = 30.0

        # Amount consistency check
        amounts = [abs(Decimal(str(t.amount))) for t in sorted_txns]
        avg_amount = sum(amounts) / Decimal(str(len(amounts)))

        # Verify amounts are within tolerance
        within_tolerance = True
        for a in amounts:
            if avg_amount > 0:
                rel_diff = abs(float((a - avg_amount) / avg_amount))
                if rel_diff > amount_tolerance and not is_known_sub:
                    within_tolerance = False
                    break

        if not within_tolerance:
            continue

        # Base confidence calculation
        confidence = 0.85
        if len(sorted_txns) >= 3:
            confidence += 0.08
        if is_known_sub:
            confidence += 0.05
        confidence = min(0.99, confidence)

        last_txn = sorted_txns[-1]
        next_date = _estimate_next_date(last_txn.date, freq, avg_interval)

        # Category from most recent transaction
        category = last_txn.category or "Other"

        recurring_items.append(
            RecurringItem(
                merchant=merchant,
                category=category,
                frequency=freq,
                expected_amount=round(avg_amount, 2),
                last_date=last_txn.date,
                next_expected_date=next_date,
                occurrence_count=len(sorted_txns),
                confidence=round(confidence, 2),
                is_subscription=is_known_sub or category in ("Entertainment", "Utilities"),
                transaction_ids=[t.id for t in sorted_txns if t.id is not None],
            )
        )

    return sorted(recurring_items, key=lambda x: x.expected_amount, reverse=True)
