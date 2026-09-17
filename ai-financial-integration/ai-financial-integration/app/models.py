"""
ORM models (the financial core) and Pydantic schemas (the API contract).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


# --------------------------------------------------------------------------
# ORM MODELS
# --------------------------------------------------------------------------

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String, nullable=False)
    account_type = Column(String, default="checking")  # checking, savings, credit
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship(
        "Transaction", back_populates="account", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)  # negative = debit, positive = credit
    timestamp = Column(DateTime, default=datetime.utcnow)

    category = Column(String, default="Uncategorized")
    category_source = Column(String, default="none")  # "model" | "rule" | "manual"

    is_flagged_fraud = Column(Boolean, default=False)
    fraud_score = Column(Float, nullable=True)

    account = relationship("Account", back_populates="transactions")


# --------------------------------------------------------------------------
# PYDANTIC SCHEMAS
# --------------------------------------------------------------------------

class AccountCreate(BaseModel):
    owner_name: str
    account_type: str = "checking"
    balance: float = 0.0


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_name: str
    account_type: str
    balance: float
    created_at: datetime


class TransactionCreate(BaseModel):
    account_id: int
    description: str
    amount: float
    timestamp: Optional[datetime] = None
    category: Optional[str] = None  # if provided, treated as a manual label


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    description: str
    amount: float
    timestamp: datetime
    category: str
    category_source: str
    is_flagged_fraud: bool
    fraud_score: Optional[float] = None


class FraudScanResult(BaseModel):
    account_id: int
    scanned_transactions: int
    flagged_transactions: list[int]
    threshold: float


class CategorySummary(BaseModel):
    category: str
    total_spent: float
    transaction_count: int
