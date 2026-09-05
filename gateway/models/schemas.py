from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum

class DecisionEnum(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    FLAG_FOR_REVIEW = "FLAG_FOR_REVIEW"

class ProvenanceData(BaseModel):
    source_type: str = Field(..., description="e.g., TRUSTED_TASK, EXTERNAL_CONTENT")
    source_id: str = Field(..., description="Identifier for the source")
    source_trust: str = Field(..., description="TRUSTED, UNTRUSTED, UNKNOWN")
    payment_intent_origin: str = Field(..., description="Origin context of the payment intent")

class PayoutRequest(BaseModel):
    agent_id: str = Field(..., description="ID of the agent initiating the payout")
    request_id: str = Field(..., description="Unique identifier for the HTTP request (used for tracing and logging)")
    idempotency_key: str = Field(..., description="Unique key guaranteeing exactly-once financial execution")
    payee_id: str = Field(..., description="ID of the payee/vendor")
    category: str = Field(..., description="Category of the spend (e.g., software_subscription)")
    amount: int = Field(..., gt=0, description="Amount in the lowest denomination (e.g., paise for INR)")
    currency: str = Field(default="INR", description="Currency code")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None), description="Timestamp of the request")
    provenance: Optional[ProvenanceData] = Field(default=None, description="Decision provenance metadata")

class GovernorResponse(BaseModel):
    request_id: str
    decision: DecisionEnum
    reason_code: Optional[str] = None
    anomaly_score: Optional[float] = None
    risk_signals: List[str] = []
    razorpay_payout_id: Optional[str] = None
    audit_hash: str
