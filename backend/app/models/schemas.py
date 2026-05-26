"""
Pydantic request/response schemas for the Fraud Detection API.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────────────────────
# REQUEST SCHEMAS
# ──────────────────────────────────────────────────────────────

class TransactionSubmitRequest(BaseModel):
    account_id: str = Field(..., example="ACC10294", description="Unique account identifier")
    amount: float = Field(..., gt=0, example=5000.00, description="Transaction amount in INR")
    lat: float = Field(..., ge=-90, le=90, example=19.0760, description="Transaction latitude")
    lon: float = Field(..., ge=-180, le=180, example=72.8777, description="Transaction longitude")

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return round(v, 2)


class OTPVerifyRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6, example="123456")


# ──────────────────────────────────────────────────────────────
# RESPONSE SCHEMAS
# ──────────────────────────────────────────────────────────────

class TransactionResponse(BaseModel):
    transaction_id: str
    status: str
    risk_score: Optional[float] = None
    message: Optional[str] = None


class TransactionDetail(BaseModel):
    id: UUID
    account_id: str
    amount: float
    status: str
    is_fraudulent: bool
    risk_score: Optional[float]
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


class LedgerSummaryResponse(BaseModel):
    total_volume: float
    fraud_count: int
    throughput: float
    transactions: list[dict]
    status_breakdown: dict


class HealthResponse(BaseModel):
    status: str
    service: str
    