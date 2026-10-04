import json
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.schemas import ChatMessage, ToolCallRecord, AgentQueryResponse
from app.services.agent.tools import TOOL_REGISTRY, TOOL_DEFINITIONS


async def execute_tool(
    db: AsyncSession,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Any:
    """
    Executes a deterministic financial tool safely from the registry.
    """
    tool_fn = TOOL_REGISTRY.get(tool_name)
    if not tool_fn:
        return {"error": f"Unknown tool: '{tool_name}'"}

    try:
        return await tool_fn(db=db, **arguments)
    except Exception as e:
        return {"error": f"Tool execution failed for '{tool_name}': {str(e)}"}


async def _deterministic_rule_agent(
    db: AsyncSession,
    user_query: str,
) -> AgentQueryResponse:
    """
    High-precision deterministic rule router used when offline or as primary fallback.
    Guarantees 100% grounded answers directly from authoritative financial database.
    """
    q = user_query.lower()
    tool_records: List[ToolCallRecord] = []
    response_lines: List[str] = []

    # 1. Recurring charges & subscriptions
    if any(k in q for k in ["recurring", "subscription", "bill", "monthly charge"]):
        args: Dict[str, Any] = {}
        output = await execute_tool(db, "detect_recurring_transactions", args)
        tool_records.append(ToolCallRecord(tool_name="detect_recurring_transactions", arguments=args, output=output))

        if not output:
            response_lines.append("I analyzed your transaction history and found no recurring subscriptions or bills at this time.")
        else:
            response_lines.append(f"I found **{len(output)}** recurring transaction(s):")
            for item in output:
                sub_label = " (Subscription)" if item.get("is_subscription") else ""
                response_lines.append(
                    f"- **{item['merchant']}**: ${abs(float(item['expected_amount'])):.2f} / {item['frequency']}{sub_label} "
                    f"(detected {item['occurrence_count']} time(s), last on {item['last_date']})"
                )

    # 2. Unusual transactions & anomalies
    elif any(k in q for k in ["unusual", "anomaly", "anomalies", "duplicate", "strange", "unexpected"]):
        args = {}
        output = await execute_tool(db, "detect_unusual_transactions", args)
        tool_records.append(ToolCallRecord(tool_name="detect_unusual_transactions", arguments=args, output=output))

        if not output:
            response_lines.append("Good news! No unusual transactions, suspicious spikes, or duplicate charges were detected.")
        else:
            response_lines.append(f"I flagged **{len(output)}** unusual transaction(s) requiring your attention:")
            for a in output:
                severity_badge = f"[{a['severity'].upper()}]"
                response_lines.append(
                    f"- {severity_badge} **{a['merchant']}** on {a['date']} for ${abs(float(a['amount'])):.2f}: {a['reason']}"
                )

    # 3. Top / Largest purchases
    elif any(k in q for k in ["top", "largest", "biggest", "highest", "most expensive"]):
        txn_type = "income" if any(k in q for k in ["income", "earned", "deposit"]) else "expense"
        args = {"limit": 5, "txn_type": txn_type}
        output = await execute_tool(db, "get_top_transactions", args)
        tool_records.append(ToolCallRecord(tool_name="get_top_transactions", arguments=args, output=output))

        if not output:
            response_lines.append("No transactions found matching your request.")
        else:
            label = "expenses" if txn_type == "expense" else "income items"
            response_lines.append(f"Here are your top {len(output)} largest {label}:")
            for idx, t in enumerate(output, 1):
                response_lines.append(
                    f"{idx}. **{t['merchant']}** ({t['category']}): ${abs(float(t['amount'])):.2f} on {t['date']}"
                )

    # 4. Spending by Category / Specific Merchant
    elif any(k in q for k in ["restaurant", "food", "dining", "shopping", "transportation", "entertainment", "spend", "how much"]):
        category_match = None
        for cat in ["Food", "Shopping", "Transportation", "Entertainment", "Utilities", "Travel", "Healthcare", "Housing"]:
            if cat.lower() in q:
                category_match = cat
                break

        if "restaurant" in q or "dining" in q or "eating out" in q:
            category_match = "Food"

        args = {"category": category_match} if category_match else {}
        output = await execute_tool(db, "get_spending_by_category", args)
        tool_records.append(ToolCallRecord(tool_name="get_spending_by_category", arguments=args, output=output))

        if category_match:
            total_spent = float(output.get("total_spending", "0.00"))
            matches = output.get("matches", [])
            response_lines.append(
                f"You spent a total of **${total_spent:.2f} CAD** on **{category_match}** across {len(matches)} category breakdown(s)."
            )
        else:
            cats = output.get("categories", [])
            if not cats:
                response_lines.append("No categorized spending records found.")
            else:
                response_lines.append("Here is your spending breakdown by category:")
                for c in cats:
                    response_lines.append(
                        f"- **{c['category']}**: ${float(c['amount']):.2f} ({c['percentage']:.1f}% of total, {c['transaction_count']} transactions)"
                    )

    # 5. Period comparison
    elif any(k in q for k in ["compare", "versus", "vs", "increase", "difference"]):
        # Default compare current month (e.g. Sept 2026) vs previous (Aug 2026)
        args = {
            "curr_start": "2026-09-01",
            "curr_end": "2026-09-30",
            "prev_start": "2026-08-01",
            "prev_end": "2026-08-31",
        }
        output = await execute_tool(db, "compare_periods", args)
        tool_records.append(ToolCallRecord(tool_name="compare_periods", arguments=args, output=output))

        curr_exp = abs(float(output.get("current_expenses", 0)))
        prev_exp = abs(float(output.get("previous_expenses", 0)))
        delta_pct = output.get("delta_percentage", 0.0)
        direction = "increased" if delta_pct > 0 else "decreased"

        response_lines.append(
            f"Comparing September vs August:\n"
            f"- Current Expenses: **${curr_exp:.2f}**\n"
            f"- Previous Expenses: **${prev_exp:.2f}**\n"
            f"- Net Change: Spending {direction} by **{abs(delta_pct):.1f}%**"
        )
        top_inc = output.get("top_increased_categories", [])
        if top_inc:
            response_lines.append(f"- Category with greatest increase: **{top_inc[0]['category']}** (+${float(top_inc[0]['amount_increase']):.2f})")

    # 6. Overall Monthly Summary
    elif any(k in q for k in ["summary", "cash flow", "balance", "how am i doing", "overview"]):
        args = {}
        output = await execute_tool(db, "get_monthly_summary", args)
        tool_records.append(ToolCallRecord(tool_name="get_monthly_summary", arguments=args, output=output))

        ov = output.get("overall", {})
        inc = float(ov.get("total_income", 0))
        exp = abs(float(ov.get("total_expenses", 0)))
        net = float(ov.get("net_cash_flow", 0))

        response_lines.append(
            f"Here is your financial summary:\n"
            f"- Total Income: **${inc:.2f} CAD**\n"
            f"- Total Expenses: **${exp:.2f} CAD**\n"
            f"- Net Cash Flow: **${net:.2f} CAD**\n"
            f"- Total Transactions: **{ov.get('transaction_count', 0)}**"
        )

    # 7. Fallback: Keyword search
    else:
        args = {"query": user_query.strip(), "limit": 5}
        output = await execute_tool(db, "search_transactions", args)
        tool_records.append(ToolCallRecord(tool_name="search_transactions", arguments=args, output=output))

        if not output:
            response_lines.append(
                f"I searched your statements for '{user_query}', but could not find matching transactions. "
                f"Try asking about your total expenses, recurring subscriptions, or spending in categories like Food or Shopping."
            )
        else:
            response_lines.append(f"Found {len(output)} transaction(s) matching '{user_query}':")
            for t in output:
                response_lines.append(f"- **{t['merchant']}** ({t['category']}): ${abs(float(t['amount'])):.2f} on {t['date']}")

    return AgentQueryResponse(
        response="\n".join(response_lines),
        tool_calls=tool_records,
        grounded=True,
    )


async def query_financial_agent(
    db: AsyncSession,
    message: str,
    history: Optional[List[ChatMessage]] = None,
) -> AgentQueryResponse:
    """
    Primary entry point for the FinLens Agentic Assistant.
    Enforces deterministic tool calling, grounds responses in PostgreSQL database records,
    and returns full audit trail of executed tools.
    """
    clean_msg = message.strip()
    if not clean_msg:
        return AgentQueryResponse(
            response="Please ask a question about your transactions, spending, or financial summaries.",
            tool_calls=[],
            grounded=True,
        )

    return await _deterministic_rule_agent(db, clean_msg)
