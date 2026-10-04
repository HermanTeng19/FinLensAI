from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schemas import AgentQueryRequest, AgentQueryResponse
from app.services.agent.agent import query_financial_agent
from app.services.agent.tools import TOOL_DEFINITIONS

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/query", response_model=AgentQueryResponse, status_code=status.HTTP_200_OK)
async def query_agent(
    request: AgentQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Query the Agentic Financial Assistant with natural language.
    The agent dynamically selects authoritative tools and provides grounded answers.
    """
    return await query_financial_agent(
        db=db,
        message=request.message,
        history=request.history,
    )


@router.get("/tools", response_model=list[dict[str, Any]])
async def list_available_tools():
    """
    List all registered deterministic financial tools and their JSON schemas.
    """
    return TOOL_DEFINITIONS
