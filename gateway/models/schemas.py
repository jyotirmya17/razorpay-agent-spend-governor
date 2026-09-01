from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum

class DecisionEnum(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    FLAG_FOR_REVIEW = "FLAG_FOR_REVIEW"

class PayoutRequest(BaseModel):
    agent_id: str = Field(..., description="Unique identifier of the agent requesting the payout")
    idempotency_key: str = Field(..., description="Unique key to prevent duplicate processing")
    payee_id: str = Field(..., description="Target vendor or payee identifier")
    category: str = Field(..., description="Category of the spend (e.g., software_subscription)")
    amount: int = Field(..., gt=0, description="Amount in the lowest denomination (e.g., paise for INR)")
    currency: str = Field(default="INR", description="Currency code")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None), description="Timestamp of the request")

class GovernorResponse(BaseModel):
    request_id: str
    decision: DecisionEnum
    reason_code: Optional[str] = None
    anomaly_score: Optional[float] = None
    risk_signals: List[str] = []
    razorpay_payout_id: Optional[str] = None
    audit_hash: str
