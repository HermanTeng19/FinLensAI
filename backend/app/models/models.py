import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List, Any
from sqlalchemy import (
    String,
    DateTime,
    Date,
    Numeric,
    Float,
    Integer,
    Boolean,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    statements: Mapped[List["Statement"]] = relationship(
        "Statement", back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )


class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), nullable=False)  # "pdf" | "csv"
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )  # pending, processing, completed, failed
    period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_transactions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="statements")
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="statement", cascade="all, delete-orphan"
    )
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob", back_populates="statement", cascade="all, delete-orphan"
    )
    insights: Mapped[List["Insight"]] = relationship(
        "Insight", back_populates="statement", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    statement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("statements.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    merchant: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    original_description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="CAD", nullable=False)
    transaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # expense, income, transfer
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    statement: Mapped[Optional["Statement"]] = relationship(
        "Statement", back_populates="transactions"
    )
    user: Mapped[Optional["User"]] = relationship("User", back_populates="transactions")


class Category(Base):
    __tablename__ = "categories"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon_name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_system_default: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    statement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("statements.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    statement: Mapped["Statement"] = relationship(
        "Statement", back_populates="processing_jobs"
    )


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    statement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("statements.id", ondelete="CASCADE"), nullable=True, index=True
    )
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    statement: Mapped[Optional["Statement"]] = relationship(
        "Statement", back_populates="insights"
    )
