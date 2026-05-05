from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./claimsight.db")

# Handle SQLite vs PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ClaimRecord(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String, unique=True, index=True)
    patient_name = Column(String)
    patient_dob = Column(String)
    payer_id = Column(String)
    payer_name = Column(String)
    provider_npi = Column(String)
    diagnosis_codes = Column(JSON)
    cpt_codes = Column(JSON)
    total_charge = Column(Float)
    service_date = Column(String)
    raw_edi = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String, index=True)
    risk_score = Column(Integer)
    risk_level = Column(String)
    confidence = Column(Integer)
    top_denial_reasons = Column(JSON)
    counterfactuals = Column(JSON)
    rule_flags = Column(JSON)
    plain_english = Column(Text)
    recommended_action = Column(Text)
    actual_outcome = Column(String, nullable=True)
    outcome_recorded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    claim_id = Column(String, nullable=True)
    details = Column(JSON)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()