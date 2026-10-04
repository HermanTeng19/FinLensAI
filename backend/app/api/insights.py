import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schemas import (
    GenerateInsightsRequest,
    InsightListResponse,
)
from app.services.insights.engine import generate_insights, get_insights

router = APIRouter(prefix="/insights", tags=["AI Insights"])


@router.get("", response_model=InsightListResponse)
async def list_insights(
    statement_id: uuid.UUID | None = Query(None, description="Filter insights by statement ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve grounded financial insights for the user or a specific statement.
    Automatically generates deterministic insights if none are currently stored.
    """
    insights = await get_insights(db, statement_id=statement_id)

    warnings = sum(1 for i in insights if i.insight_type == "warning")
    positives = sum(1 for i in insights if i.insight_type == "positive")
    infos = sum(1 for i in insights if i.insight_type == "info")

    return InsightListResponse(
        insights=insights,
        total_count=len(insights),
        warning_count=warnings,
        positive_count=positives,
        info_count=infos,
    )


@router.post("/generate", response_model=InsightListResponse, status_code=status.HTTP_200_OK)
async def trigger_insights_generation(
    req: GenerateInsightsRequest | None = None,
    statement_id: uuid.UUID | None = Query(None, description="Query fallback statement ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Explicitly trigger or re-run the deterministic AI insights generation engine.
    """
    target_stmt_id = None
    if req and req.statement_id:
        target_stmt_id = req.statement_id
    elif statement_id:
        target_stmt_id = statement_id

    insights = await generate_insights(db, statement_id=target_stmt_id)

    warnings = sum(1 for i in insights if i.insight_type == "warning")
    positives = sum(1 for i in insights if i.insight_type == "positive")
    infos = sum(1 for i in insights if i.insight_type == "info")

    return InsightListResponse(
        insights=insights,
        total_count=len(insights),
        warning_count=warnings,
        positive_count=positives,
        info_count=infos,
    )
