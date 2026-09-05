import json
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone

import os

# Use PostgreSQL as primary for production/concurrency
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/governor_test")

# If it's still sqlite (e.g. for simple local test), keep check_same_thread
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
    
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class AgentStatus(str):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"

class MandateStatus(str):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"

class Agent(Base):
    __tablename__ = "agents"

    agent_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default=AgentStatus.ACTIVE, nullable=False)
    
    mandates = relationship("Mandate", back_populates="agent")


class Mandate(Base):
    __tablename__ = "mandates"

    mandate_id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    effective_from = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    daily_cap = Column(Integer, nullable=False)  # in paise
    weekly_cap = Column(Integer, nullable=False) # in paise
    txn_cap = Column(Integer, nullable=False)    # in paise
    
    # Store lists as JSON (e.g. ["software", "cloud"])
    allowed_categories = Column(JSON, nullable=False)
    allowed_payees = Column(JSON, nullable=True) # if null, any payee allowed (or can be strict)

    status = Column(String, default=MandateStatus.ACTIVE, nullable=False)
    
    agent = relationship("Agent", back_populates="mandates")


class Transaction(Base):
    """ Used to track daily/weekly spends, and for ML feature extraction """
    __tablename__ = "transactions"
    
    txn_id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, index=True, nullable=False)
    payee_id = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Integer, nullable=False) # in paise
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    
    # States: AUTHORIZED -> EXECUTING -> SUCCEEDED | FAILED | UNKNOWN -> RELEASED
    status = Column(String, default="AUTHORIZED", nullable=False)
    
    # Razorpay execution correlation
    razorpay_payout_id = Column(String, index=True, nullable=True)

class MandateUsage(Base):
    __tablename__ = "mandate_usage"
    
    mandate_id = Column(String, ForeignKey("mandates.mandate_id"), primary_key=True)
    daily_usage = Column(Integer, default=0, nullable=False) # in paise
    weekly_usage = Column(Integer, default=0, nullable=False) # in paise
    last_reset_date = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    
    idempotency_key = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=False)
    request_hash = Column(String, nullable=False)
    status = Column(String, default="PENDING", nullable=False) # PENDING, COMPLETED, FAILED, UNKNOWN
    response_payload = Column(String, nullable=True) # JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

# To initialize DB schemas
def init_db():
    Base.metadata.create_all(bind=engine)

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    
    event_id = Column(String, primary_key=True, index=True) # e.g. ev_...
    event_type = Column(String, nullable=False)
    payload = Column(String, nullable=False)
    processed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

class ProvenanceRecord(Base):
    __tablename__ = "provenance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    txn_id = Column(String, ForeignKey("transactions.txn_id"), index=True, nullable=False)
    source_type = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    source_trust = Column(String, nullable=False)
    payment_intent_origin = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

class AuditEvent(Base):
    __tablename__ = "audit_events"

    sequence_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, index=True, nullable=False, unique=True) # UUID
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    event_type = Column(String, nullable=False)
    entity_id = Column(String, index=True, nullable=False)
    payload = Column(String, nullable=False)
    previous_event_hash = Column(String, nullable=False)
    event_hash = Column(String, nullable=False)
