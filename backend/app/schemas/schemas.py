import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


# Health Check
class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str
    project: str
    database: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Category Schema
class CategoryBase(BaseModel):
    code: str
    name: str
    icon_name: str
    is_system_default: bool = True

    model_config = ConfigDict(from_attributes=True)


# Transaction Schema
class TransactionBase(BaseModel):
    date: date
    merchant: str
    original_description: str
    amount: Decimal = Field(..., description="Deterministic Decimal amount. Negative for expense, positive for income.")
    currency: str = "CAD"
    transaction_type: str = Field(..., description="'expense', 'income', or 'transfer'")
    category: str
    subcategory: Optional[str] = None
    confidence: float = 1.0
    source_page: Optional[int] = None


class TransactionCreate(TransactionBase):
    statement_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None


class TransactionResponse(TransactionBase):
    id: uuid.UUID
    statement_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Statement Schema
class StatementBase(BaseModel):
    filename: str
    file_format: str
    status: str = "pending"
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    total_transactions: int = 0


class StatementResponse(StatementBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Analytics Schemas
class FinancialSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal
    currency: str = "CAD"
    transaction_count: int


class CategorySpending(BaseModel):
    category: str
    amount: Decimal
    percentage: float
    transaction_count: int


class MonthlyTrend(BaseModel):
    month: str  # "YYYY-MM"
    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal


class RecurringItem(BaseModel):
    merchant: str
    category: str
    frequency: str  # weekly, bi-weekly, monthly, annual
    expected_amount: Decimal
    last_date: date
    next_expected_date: Optional[date] = None
    occurrence_count: int
    confidence: float
    is_subscription: bool = False
    transaction_ids: List[uuid.UUID] = []


class UnusualTransaction(BaseModel):
    transaction_id: uuid.UUID
    date: date
    merchant: str
    amount: Decimal
    category: str
    anomaly_type: str  # duplicate_charge, category_outlier, large_expense
    reason: str
    severity: str = "medium"  # low, medium, high


class PeriodComparison(BaseModel):
    current_expenses: Decimal
    previous_expenses: Decimal
    delta_expenses: Decimal
    delta_percentage: float
    current_income: Decimal
    previous_income: Decimal
    delta_income: Decimal
    top_increased_categories: List[CategorySpending] = []


# Agent & Chat Schemas
class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Any


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str


class AgentQueryRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class AgentQueryResponse(BaseModel):
    response: str
    tool_calls: List[ToolCallRecord] = []
    grounded: bool = True


# Phase 9: AI Insights Schemas
class SupportingTransactionSchema(BaseModel):
    id: uuid.UUID
    date: date
    merchant: str
    amount: Decimal
    category: str


class InsightCardSchema(BaseModel):
    id: uuid.UUID
    statement_id: Optional[uuid.UUID] = None
    insight_type: str = Field(..., description="'warning', 'positive', or 'info'")
    category: str = Field(..., description="Category like 'spending_spike', 'unusual_transaction', 'subscription', etc.")
    title: str
    content: str
    severity: str = Field(default="medium", description="'high', 'medium', or 'low'")
    metric: Optional[str] = None
    supporting_transactions: List[SupportingTransactionSchema] = []
    metadata: Dict[str, Any] = {}
    generated_at: datetime


class InsightListResponse(BaseModel):
    insights: List[InsightCardSchema]
    total_count: int
    warning_count: int
    positive_count: int
    info_count: int


class GenerateInsightsRequest(BaseModel):
    statement_id: Optional[uuid.UUID] = None


