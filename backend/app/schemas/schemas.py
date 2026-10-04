import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List, Any
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
