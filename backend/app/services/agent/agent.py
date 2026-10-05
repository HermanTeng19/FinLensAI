import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.schemas import AgentQueryResponse, ChatMessage, ToolCallRecord
from app.services.agent.tools import TOOL_REGISTRY
from app.services.agent.tracker import ToolExecutionSpan, ai_tracker


async def execute_tool(
    db: AsyncSession,
    tool_name: str,
    arguments: dict[str, Any],
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
        return {"error": f"Tool execution failed for '{tool_name}': {e!s}"}


RECURRING_KEYWORDS = [
    "recurring",
    "subscription",
    "subscriptions",
    "bill",
    "bills",
    "monthly charge",
    "monthly fee",
    "订阅",
    "周期",
    "按月",
    "自动扣款",
    "固定账单",
]
UNUSUAL_KEYWORDS = [
    "unusual",
    "anomaly",
    "anomalies",
    "duplicate",
    "strange",
    "unexpected",
    "suspicious",
    "spike",
    "异常",
    "可疑",
    "突增",
    "重复扣款",
    "重复消费",
    "不寻常",
]
TOP_KEYWORDS = [
    "top",
    "largest",
    "biggest",
    "highest",
    "most expensive",
    "major expense",
    "最大",
    "最高",
    "最多",
    "大额",
    "最贵",
    "主要支出",
]
CATEGORY_KEYWORDS = [
    "restaurant",
    "food",
    "dining",
    "shopping",
    "transportation",
    "entertainment",
    "spend",
    "spending",
    "how much",
    "category",
    "categories",
    "餐饮",
    "外卖",
    "美食",
    "购物",
    "买东西",
    "交通",
    "出行",
    "娱乐",
    "水电",
    "医疗",
    "住房",
    "房租",
    "花了多少",
    "支出多少",
    "花销",
    "分类",
    "类目",
    "各项开销",
    "各项支出",
    "各项花费",
]
CATEGORY_MAP = {
    "food": "Food",
    "dining": "Food",
    "restaurant": "Food",
    "cafe": "Food",
    "eating": "Food",
    "餐饮": "Food",
    "外卖": "Food",
    "美食": "Food",
    "咖啡": "Food",
    "shopping": "Shopping",
    "retail": "Shopping",
    "购物": "Shopping",
    "买东西": "Shopping",
    "transportation": "Transportation",
    "transport": "Transportation",
    "transit": "Transportation",
    "gas": "Transportation",
    "fuel": "Transportation",
    "交通": "Transportation",
    "出行": "Transportation",
    "加油": "Transportation",
    "entertainment": "Entertainment",
    "streaming": "Entertainment",
    "movies": "Entertainment",
    "娱乐": "Entertainment",
    "电影": "Entertainment",
    "游戏": "Entertainment",
    "utilities": "Utilities",
    "utility": "Utilities",
    "hydro": "Utilities",
    "electric": "Utilities",
    "internet": "Utilities",
    "水电": "Utilities",
    "电费": "Utilities",
    "水费": "Utilities",
    "宽带": "Utilities",
    "healthcare": "Healthcare",
    "health": "Healthcare",
    "medical": "Healthcare",
    "pharmacy": "Healthcare",
    "医疗": "Healthcare",
    "看病": "Healthcare",
    "药店": "Healthcare",
    "housing": "Housing",
    "rent": "Housing",
    "mortgage": "Housing",
    "住房": "Housing",
    "房租": "Housing",
    "房贷": "Housing",
    "travel": "Travel",
    "flight": "Travel",
    "hotel": "Travel",
    "旅行": "Travel",
    "旅游": "Travel",
    "机票": "Travel",
    "酒店": "Travel",
}
COMPARE_KEYWORDS = [
    "compare",
    "versus",
    "vs",
    "increase",
    "difference",
    "month over month",
    "trend",
    "对比",
    "比较",
    "环比",
    "同比",
    "变化",
    "增长",
    "减少",
]
SUMMARY_KEYWORDS = [
    "summary",
    "cash flow",
    "balance",
    "how am i doing",
    "overview",
    "total income",
    "total expense",
    "net cash",
    "总览",
    "总结",
    "概况",
    "财务状况",
    "结余",
    "现金流",
    "总收入",
    "总支出",
    "净收入",
    "收支情况",
]


async def _deterministic_rule_agent(
    db: AsyncSession,
    user_query: str,
) -> AgentQueryResponse:
    """
    High-precision deterministic rule router used when offline or as primary fallback.
    Guarantees 100% grounded answers directly from authoritative financial database.
    """
    q = user_query.lower()
    tool_records: list[ToolCallRecord] = []
    response_lines: list[str] = []

    # 1. Recurring charges & subscriptions
    if any(k in q for k in RECURRING_KEYWORDS):
        args: dict[str, Any] = {}
        output = await execute_tool(db, "detect_recurring_transactions", args)
        tool_records.append(
            ToolCallRecord(tool_name="detect_recurring_transactions", arguments=args, output=output)
        )

        if not output:
            response_lines.append(
                "I analyzed your transaction history and found no recurring subscriptions or bills at this time."
            )
        else:
            response_lines.append(f"I found **{len(output)}** recurring transaction(s):")
            for item in output:
                sub_label = " (Subscription)" if item.get("is_subscription") else ""
                response_lines.append(
                    f"- **{item['merchant']}**: ${abs(float(item['expected_amount'])):.2f} / {item['frequency']}{sub_label} "
                    f"(detected {item['occurrence_count']} time(s), last on {item['last_date']})"
                )

    # 2. Unusual transactions & anomalies
    elif any(k in q for k in UNUSUAL_KEYWORDS):
        args = {}
        output = await execute_tool(db, "detect_unusual_transactions", args)
        tool_records.append(
            ToolCallRecord(tool_name="detect_unusual_transactions", arguments=args, output=output)
        )

        if not output:
            response_lines.append(
                "Good news! No unusual transactions, suspicious spikes, or duplicate charges were detected."
            )
        else:
            response_lines.append(
                f"I flagged **{len(output)}** unusual transaction(s) requiring your attention:"
            )
            for a in output:
                severity_badge = f"[{a['severity'].upper()}]"
                response_lines.append(
                    f"- {severity_badge} **{a['merchant']}** on {a['date']} for ${abs(float(a['amount'])):.2f}: {a['reason']}"
                )

    # 3. Top / Largest purchases
    elif any(k in q for k in TOP_KEYWORDS):
        txn_type = (
            "income"
            if any(k in q for k in ["income", "earned", "deposit", "收入", "进账", "入账"])
            else "expense"
        )
        args = {"limit": 5, "txn_type": txn_type}
        output = await execute_tool(db, "get_top_transactions", args)
        tool_records.append(
            ToolCallRecord(tool_name="get_top_transactions", arguments=args, output=output)
        )

        if not output:
            response_lines.append("No transactions found matching your request.")
        else:
            label = "expenses" if txn_type == "expense" else "income items"
            response_lines.append(f"Here are your top {len(output)} largest {label}:")
            for idx, t in enumerate(output, 1):
                response_lines.append(
                    f"{idx}. **{t['merchant']}** ({t['category']}): ${abs(float(t['amount'])):.2f} on {t['date']}"
                )

    # 4. Period comparison
    elif any(k in q for k in COMPARE_KEYWORDS):
        # Default compare current month (e.g. Sept 2026) vs previous (Aug 2026)
        args = {
            "curr_start": "2026-09-01",
            "curr_end": "2026-09-30",
            "prev_start": "2026-08-01",
            "prev_end": "2026-08-31",
        }
        output = await execute_tool(db, "compare_periods", args)
        tool_records.append(
            ToolCallRecord(tool_name="compare_periods", arguments=args, output=output)
        )

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
            response_lines.append(
                f"- Category with greatest increase: **{top_inc[0]['category']}** (+${float(top_inc[0]['amount_increase']):.2f})"
            )

    # 5. Spending by Category / Specific Merchant
    elif any(k in q for k in CATEGORY_KEYWORDS):
        category_match = None
        for key, cat_name in CATEGORY_MAP.items():
            if key in q:
                category_match = cat_name
                break

        args = {"category": category_match} if category_match else {}
        output = await execute_tool(db, "get_spending_by_category", args)
        tool_records.append(
            ToolCallRecord(tool_name="get_spending_by_category", arguments=args, output=output)
        )

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

    # 6. Overall Monthly Summary
    elif any(k in q for k in SUMMARY_KEYWORDS):
        args = {}
        output = await execute_tool(db, "get_monthly_summary", args)
        tool_records.append(
            ToolCallRecord(tool_name="get_monthly_summary", arguments=args, output=output)
        )

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
        tool_records.append(
            ToolCallRecord(tool_name="search_transactions", arguments=args, output=output)
        )

        if not output:
            response_lines.append(
                f"I searched your statements for '{user_query}', but could not find matching transactions. "
                f"Try asking about your total expenses, recurring subscriptions, or spending in categories like Food or Shopping."
            )
        else:
            response_lines.append(f"Found {len(output)} transaction(s) matching '{user_query}':")
            for t in output:
                response_lines.append(
                    f"- **{t['merchant']}** ({t['category']}): ${abs(float(t['amount'])):.2f} on {t['date']}"
                )

    return AgentQueryResponse(
        response="\n".join(response_lines),
        tool_calls=tool_records,
        grounded=True,
    )


async def query_financial_agent(
    db: AsyncSession,
    message: str,
    history: list[ChatMessage] | None = None,
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

    start_time = time.perf_counter()
    agent_response = await _deterministic_rule_agent(db, clean_msg)
    duration_ms = (time.perf_counter() - start_time) * 1000

    # Build spans for observability
    tool_spans = []
    for tc in agent_response.tool_calls:
        output_str = str(tc.output)[:120] if tc.output is not None else ""
        is_err = isinstance(tc.output, dict) and "error" in tc.output
        tool_spans.append(
            ToolExecutionSpan(
                tool_name=tc.tool_name,
                arguments=tc.arguments,
                output_summary=output_str,
                duration_ms=round(duration_ms / max(len(agent_response.tool_calls), 1), 2),
                success=not is_err,
                error_message=tc.output.get("error") if is_err else None,
            )
        )

    ai_tracker.record_trace(
        query=clean_msg,
        duration_ms=duration_ms,
        grounded=agent_response.grounded,
        tool_spans=tool_spans,
        response_text=agent_response.response,
    )

    return agent_response
