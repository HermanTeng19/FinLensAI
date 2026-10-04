"""
FinLens AI — Comprehensive AI Evaluation & Benchmark Suite.
Executes automated benchmarks for:
- Merchant Normalization Precision & Accuracy
- Transaction Categorization Precision, Recall & F1-score
- AI Agent Tool Selection & Intent Grounding Accuracy
"""

import asyncio
import sys
from decimal import Decimal
from typing import Any

from app.core.database import AsyncSessionLocal
from app.evaluation.datasets import (
    AGENT_BENCHMARK_DATA,
    CATEGORIZATION_BENCHMARK_DATA,
    MERCHANT_BENCHMARK_DATA,
)
from app.evaluation.metrics import calculate_classification_metrics
from app.services.agent.agent import _deterministic_rule_agent
from app.services.document_ai.categorizer import Categorizer
from app.services.document_ai.merchant_normalizer import MerchantNormalizer


async def run_merchant_benchmark() -> dict[str, Any]:
    y_true = []
    y_pred = []
    failures = []

    for raw_desc, expected_merchant in MERCHANT_BENCHMARK_DATA:
        pred_merchant, _ = MerchantNormalizer.normalize(raw_desc)
        y_true.append(expected_merchant)
        y_pred.append(pred_merchant)
        if pred_merchant != expected_merchant:
            failures.append(
                {
                    "input": raw_desc,
                    "expected": expected_merchant,
                    "predicted": pred_merchant,
                }
            )

    metrics = calculate_classification_metrics(y_true, y_pred)
    metrics["failures"] = failures
    return metrics


async def run_categorization_benchmark() -> dict[str, Any]:
    y_true = []
    y_pred = []
    failures = []

    for merchant, raw_desc, amount_str, expected_cat, _ in CATEGORIZATION_BENCHMARK_DATA:
        pred_cat, _, _, _ = Categorizer.classify(merchant, raw_desc, Decimal(amount_str))
        y_true.append(expected_cat)
        y_pred.append(pred_cat)
        if pred_cat != expected_cat:
            failures.append(
                {
                    "merchant": merchant,
                    "input": raw_desc,
                    "amount": amount_str,
                    "expected": expected_cat,
                    "predicted": pred_cat,
                }
            )

    metrics = calculate_classification_metrics(y_true, y_pred)
    metrics["failures"] = failures
    return metrics


async def run_agent_tool_benchmark() -> dict[str, Any]:
    y_true = []
    y_pred = []
    failures = []

    async with AsyncSessionLocal() as db:
        for query, expected_tool in AGENT_BENCHMARK_DATA:
            res = await _deterministic_rule_agent(db, query)
            pred_tool = res.tool_calls[0].tool_name if res.tool_calls else "none"
            y_true.append(expected_tool)
            y_pred.append(pred_tool)
            if pred_tool != expected_tool:
                failures.append(
                    {
                        "query": query,
                        "expected": expected_tool,
                        "predicted": pred_tool,
                    }
                )

    metrics = calculate_classification_metrics(y_true, y_pred)
    metrics["failures"] = failures
    return metrics


async def run_all_benchmarks(verbose: bool = True) -> dict[str, Any]:
    if verbose:
        print("=" * 70)
        print("           FinLens AI — AI Engine Evaluation & Benchmarks")
        print("=" * 70)

    # 1. Merchant Normalization
    merchant_res = await run_merchant_benchmark()
    if verbose:
        print("\n[1] Merchant Normalization Benchmark:")
        print(f"    - Total Samples:   {merchant_res['total_samples']}")
        print(f"    - Accuracy:        {merchant_res['accuracy'] * 100:.2f}% (Target: > 90.0%)")
        print(f"    - Macro F1:        {merchant_res['macro_f1'] * 100:.2f}%")
        if merchant_res["failures"]:
            print(f"    - Failures ({len(merchant_res['failures'])}):")
            for f in merchant_res["failures"]:
                print(
                    f"        '{f['input']}' -> Got '{f['predicted']}', Expected '{f['expected']}'"
                )

    # 2. Categorization
    cat_res = await run_categorization_benchmark()
    if verbose:
        print("\n[2] Transaction Categorization Benchmark:")
        print(f"    - Total Samples:   {cat_res['total_samples']}")
        print(f"    - Accuracy:        {cat_res['accuracy'] * 100:.2f}% (Target: > 90.0%)")
        print(f"    - Macro F1:        {cat_res['macro_f1'] * 100:.2f}% (Target: > 90.0%)")
        print("    - Per-Class Metrics:")
        for c, m in cat_res["per_class"].items():
            print(
                f"        * {c:<15}: Precision={m['precision'] * 100:5.1f}%, Recall={m['recall'] * 100:5.1f}%, F1={m['f1'] * 100:5.1f}% (N={m['support']})"
            )
        if cat_res["failures"]:
            print(f"    - Failures ({len(cat_res['failures'])}):")
            for f in cat_res["failures"]:
                print(
                    f"        '{f['input']}' -> Got '{f['predicted']}', Expected '{f['expected']}'"
                )

    # 3. Agent Tool Selection
    agent_res = await run_agent_tool_benchmark()
    if verbose:
        print("\n[3] AI Agent Tool Selection & Intent Routing Benchmark:")
        print(f"    - Total Queries:   {agent_res['total_samples']}")
        print(f"    - Accuracy:        {agent_res['accuracy'] * 100:.2f}% (Target: > 95.0%)")
        print(f"    - Macro F1:        {agent_res['macro_f1'] * 100:.2f}%")
        print("    - Per-Tool Metrics:")
        for t, m in agent_res["per_class"].items():
            print(
                f"        * {t:<28}: Precision={m['precision'] * 100:5.1f}%, Recall={m['recall'] * 100:5.1f}%, F1={m['f1'] * 100:5.1f}% (N={m['support']})"
            )
        if agent_res["failures"]:
            print(f"    - Failures ({len(agent_res['failures'])}):")
            for f in agent_res["failures"]:
                print(
                    f"        Query: '{f['query']}' -> Selected '{f['predicted']}', Expected '{f['expected']}'"
                )

    # Check Acceptance Criteria
    merchant_pass = merchant_res["accuracy"] >= 0.90
    cat_pass = cat_res["accuracy"] >= 0.90 and cat_res["macro_f1"] >= 0.90
    agent_pass = agent_res["accuracy"] >= 0.95

    all_passed = merchant_pass and cat_pass and agent_pass

    if verbose:
        print("\n" + "=" * 70)
        status_str = "PASSED ALL QUALITY GATES" if all_passed else "FAILED QUALITY GATES"
        print(f"  BENCHMARK SUMMARY: {status_str}")
        print(
            f"  - Merchant Normalization: {'PASS' if merchant_pass else 'FAIL'} ({merchant_res['accuracy'] * 100:.1f}%)"
        )
        print(
            f"  - Categorization F1:     {'PASS' if cat_pass else 'FAIL'} ({cat_res['macro_f1'] * 100:.1f}%)"
        )
        print(
            f"  - Agent Tool Accuracy:   {'PASS' if agent_pass else 'FAIL'} ({agent_res['accuracy'] * 100:.1f}%)"
        )
        print("=" * 70)

    return {
        "all_passed": all_passed,
        "merchant": merchant_res,
        "categorization": cat_res,
        "agent": agent_res,
    }


if __name__ == "__main__":
    result = asyncio.run(run_all_benchmarks(verbose=True))
    sys.exit(0 if result["all_passed"] else 1)
