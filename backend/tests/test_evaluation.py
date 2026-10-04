import pytest

from app.evaluation.runner import (
    run_agent_tool_benchmark,
    run_categorization_benchmark,
    run_merchant_benchmark,
)


@pytest.mark.asyncio
async def test_merchant_normalization_benchmark_gates():
    res = await run_merchant_benchmark()
    assert res["total_samples"] >= 30
    assert res["accuracy"] >= 0.90, (
        f"Merchant normalization accuracy {res['accuracy']} below 90% threshold"
    )
    assert res["macro_f1"] >= 0.90


@pytest.mark.asyncio
async def test_transaction_categorization_benchmark_gates():
    res = await run_categorization_benchmark()
    assert res["total_samples"] >= 30
    assert res["accuracy"] >= 0.90, f"Categorization accuracy {res['accuracy']} below 90% threshold"
    assert res["macro_f1"] >= 0.90, f"Categorization macro F1 {res['macro_f1']} below 90% threshold"


@pytest.mark.asyncio
async def test_agent_tool_selection_benchmark_gates():
    res = await run_agent_tool_benchmark()
    assert res["total_samples"] >= 30
    assert res["accuracy"] >= 0.95, (
        f"Agent tool selection accuracy {res['accuracy']} below 95% threshold"
    )
    assert res["macro_f1"] >= 0.95
