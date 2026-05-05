import sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

from edi_parser import parse_edi_837, generate_sample_edi
from denial_agent import analyze_claim
from database import get_db, create_tables, ClaimRecord, AnalysisRecord, AuditLog

app = FastAPI(
    title="ClaimSight",
    description="Datadog for Healthcare AI Agents",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    create_tables()
    print("✅ ClaimSight database initialized")

def log_action(db: Session, action: str, claim_id: str = None, details: dict = {}):
    log = AuditLog(
        action=action,
        claim_id=claim_id,
        details=details
    )
    db.add(log)
    db.commit()

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    claim_count = db.query(ClaimRecord).count()
    analysis_count = db.query(AnalysisRecord).count()
    return {
        "status": "healthy",
        "service": "ClaimSight API",
        "version": "0.1.0",
        "stats": {
            "total_claims": claim_count,
            "total_analyses": analysis_count
        }
    }

@app.get("/")
async def root():
    return {
        "message": "ClaimSight - Datadog for Healthcare AI Agents",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "parse_claim": "POST /claims/parse",
            "analyze_claim": "POST /claims/analyze",
            "sample": "GET /claims/sample",
            "history": "GET /claims/history",
            "audit_log": "GET /audit/logs"
        }
    }

@app.post("/claims/parse")
async def parse_claim(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Parse an EDI 837 claim file"""
    try:
        content = await file.read()
        edi_text = content.decode('utf-8')
        claim = parse_edi_837(edi_text)

        # Check if claim already exists
        existing = db.query(ClaimRecord).filter(
            ClaimRecord.claim_id == claim.claim_id
        ).first()

        if not existing:
            record = ClaimRecord(
                claim_id=claim.claim_id,
                patient_name=claim.patient_name,
                patient_dob=claim.patient_dob,
                payer_id=claim.payer_id,
                payer_name=claim.payer_name,
                provider_npi=claim.provider_npi,
                diagnosis_codes=claim.diagnosis_codes,
                cpt_codes=claim.cpt_codes,
                total_charge=claim.total_charge,
                service_date=claim.service_date,
                raw_edi=edi_text
            )
            db.add(record)
            db.commit()

        log_action(db, "CLAIM_PARSED", claim.claim_id, {
            "payer": claim.payer_name,
            "total_charge": claim.total_charge
        })

        return {"success": True, "claim": claim.__dict__}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/claims/analyze")
async def analyze_claim_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Parse and analyze an EDI 837 claim for denial risk"""
    try:
        content = await file.read()
        edi_text = content.decode('utf-8')
        claim = parse_edi_837(edi_text)

        # Save claim
        existing = db.query(ClaimRecord).filter(
            ClaimRecord.claim_id == claim.claim_id
        ).first()

        if not existing:
            record = ClaimRecord(
                claim_id=claim.claim_id,
                patient_name=claim.patient_name,
                patient_dob=claim.patient_dob,
                payer_id=claim.payer_id,
                payer_name=claim.payer_name,
                provider_npi=claim.provider_npi,
                diagnosis_codes=claim.diagnosis_codes,
                cpt_codes=claim.cpt_codes,
                total_charge=claim.total_charge,
                service_date=claim.service_date,
                raw_edi=edi_text
            )
            db.add(record)
            db.commit()

        # Run AI analysis
        analysis = analyze_claim(claim)

        # Save analysis
        analysis_record = AnalysisRecord(
            claim_id=claim.claim_id,
            risk_score=analysis["risk_score"],
            risk_level=analysis["risk_level"],
            confidence=analysis["confidence"],
            top_denial_reasons=analysis["top_denial_reasons"],
            counterfactuals=analysis["counterfactuals"],
            rule_flags=analysis["rule_flags"],
            plain_english=analysis["plain_english"],
            recommended_action=analysis["recommended_action"]
        )
        db.add(analysis_record)
        db.commit()

        log_action(db, "CLAIM_ANALYZED", claim.claim_id, {
            "risk_score": analysis["risk_score"],
            "risk_level": analysis["risk_level"]
        })

        return {
            "success": True,
            "claim": {
                "claim_id": claim.claim_id,
                "patient_name": claim.patient_name,
                "payer_name": claim.payer_name,
                "total_charge": claim.total_charge,
                "cpt_codes": claim.cpt_codes,
                "diagnosis_codes": claim.diagnosis_codes
            },
            "analysis": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/claims/analyze-sample")
async def analyze_sample(db: Session = Depends(get_db)):
    """Analyze sample claim - for testing"""
    edi = generate_sample_edi()
    claim = parse_edi_837(edi)

    # Save claim
    existing = db.query(ClaimRecord).filter(
        ClaimRecord.claim_id == claim.claim_id
    ).first()

    if not existing:
        record = ClaimRecord(
            claim_id=claim.claim_id,
            patient_name=claim.patient_name,
            patient_dob=claim.patient_dob,
            payer_id=claim.payer_id,
            payer_name=claim.payer_name,
            provider_npi=claim.provider_npi,
            diagnosis_codes=claim.diagnosis_codes,
            cpt_codes=claim.cpt_codes,
            total_charge=claim.total_charge,
            service_date=claim.service_date,
            raw_edi=edi
        )
        db.add(record)
        db.commit()

    analysis = analyze_claim(claim)

    analysis_record = AnalysisRecord(
        claim_id=claim.claim_id,
        risk_score=analysis["risk_score"],
        risk_level=analysis["risk_level"],
        confidence=analysis["confidence"],
        top_denial_reasons=analysis["top_denial_reasons"],
        counterfactuals=analysis["counterfactuals"],
        rule_flags=analysis["rule_flags"],
        plain_english=analysis["plain_english"],
        recommended_action=analysis["recommended_action"]
    )
    db.add(analysis_record)
    db.commit()

    log_action(db, "SAMPLE_ANALYZED", claim.claim_id, {
        "risk_score": analysis["risk_score"]
    })

    return {
        "success": True,
        "claim": {
            "claim_id": claim.claim_id,
            "patient_name": claim.patient_name,
            "payer_name": claim.payer_name,
            "total_charge": claim.total_charge
        },
        "analysis": analysis
    }


@app.get("/claims/history")
async def get_claim_history(db: Session = Depends(get_db)):
    """Get all analyzed claims with their risk scores"""
    analyses = db.query(AnalysisRecord).order_by(
        AnalysisRecord.created_at.desc()
    ).limit(50).all()

    return {
        "success": True,
        "total": len(analyses),
        "claims": [
            {
                "claim_id": a.claim_id,
                "risk_score": a.risk_score,
                "risk_level": a.risk_level,
                "confidence": a.confidence,
                "recommended_action": a.recommended_action,
                "analyzed_at": a.created_at,
                "actual_outcome": a.actual_outcome
            }
            for a in analyses
        ]
    }


@app.post("/claims/{claim_id}/outcome")
async def record_outcome(
    claim_id: str,
    outcome: str,
    db: Session = Depends(get_db)
):
    """
    Record actual outcome for a claim (APPROVED/DENIED)
    This is the ground truth loop - how we know if AI was right
    """
    analysis = db.query(AnalysisRecord).filter(
        AnalysisRecord.claim_id == claim_id
    ).order_by(AnalysisRecord.created_at.desc()).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Claim not found")

    analysis.actual_outcome = outcome
    analysis.outcome_recorded_at = datetime.utcnow()
    db.commit()

    was_correct = (
        (outcome == "DENIED" and analysis.risk_score >= 50) or
        (outcome == "APPROVED" and analysis.risk_score < 50)
    )

    log_action(db, "OUTCOME_RECORDED", claim_id, {
        "outcome": outcome,
        "predicted_risk": analysis.risk_score,
        "prediction_correct": was_correct
    })

    return {
        "success": True,
        "claim_id": claim_id,
        "outcome": outcome,
        "predicted_risk_score": analysis.risk_score,
        "prediction_correct": was_correct
    }


@app.get("/audit/logs")
async def get_audit_logs(db: Session = Depends(get_db)):
    """Get full HIPAA audit trail"""
    logs = db.query(AuditLog).order_by(
        AuditLog.created_at.desc()
    ).limit(100).all()

    return {
        "success": True,
        "total": len(logs),
        "logs": [
            {
                "action": l.action,
                "claim_id": l.claim_id,
                "details": l.details,
                "timestamp": l.created_at
            }
            for l in logs
        ]
    }


@app.get("/analytics/summary")
async def get_analytics(db: Session = Depends(get_db)):
    """Get system performance analytics"""
    total_claims = db.query(AnalysisRecord).count()
    high_risk = db.query(AnalysisRecord).filter(
        AnalysisRecord.risk_score >= 70
    ).count()
    with_outcomes = db.query(AnalysisRecord).filter(
        AnalysisRecord.actual_outcome != None
    ).count()

    correct = 0
    if with_outcomes > 0:
        all_with_outcomes = db.query(AnalysisRecord).filter(
            AnalysisRecord.actual_outcome != None
        ).all()
        correct = sum(1 for a in all_with_outcomes if (
            (a.actual_outcome == "DENIED" and a.risk_score >= 50) or
            (a.actual_outcome == "APPROVED" and a.risk_score < 50)
        ))

    return {
        "success": True,
        "analytics": {
            "total_claims_analyzed": total_claims,
            "high_risk_claims": high_risk,
            "high_risk_percentage": round(high_risk / total_claims * 100, 1) if total_claims > 0 else 0,
            "claims_with_outcomes": with_outcomes,
            "prediction_accuracy": round(correct / with_outcomes * 100, 1) if with_outcomes > 0 else 0,
            "estimated_revenue_protected": high_risk * 1500
        }
    }