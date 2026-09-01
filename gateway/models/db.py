import json
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone

# Optional fallback to SQLite for local zero-setup dev
# For prod/eval, this would be a postgres:// URL
DATABASE_URL = "sqlite:///./governor.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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
    status = Column(String, default="COMPLETED", nullable=False) # e.g. COMPLETED, FAILED

# To initialize DB schemas
def init_db():
    Base.metadata.create_all(bind=engine)
