from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
sys.path.append(os.path.dirname(__file__))
from edi_parser import parse_edi_837, generate_sample_edi
import json

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

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ClaimSight API",
        "version": "0.1.0"
    }

@app.get("/")
async def root():
    return {
        "message": "ClaimSight - Datadog for Healthcare AI Agents",
        "docs": "/docs"
    }

@app.post("/claims/parse")
async def parse_claim(file: UploadFile = File(...)):
    """Parse an EDI 837 claim file"""
    try:
        content = await file.read()
        edi_text = content.decode('utf-8')
        claim = parse_edi_837(edi_text)
        return {
            "success": True,
            "claim": {
                "claim_id": claim.claim_id,
                "patient_name": claim.patient_name,
                "patient_dob": claim.patient_dob,
                "payer_id": claim.payer_id,
                "payer_name": claim.payer_name,
                "provider_npi": claim.provider_npi,
                "diagnosis_codes": claim.diagnosis_codes,
                "cpt_codes": claim.cpt_codes,
                "total_charge": claim.total_charge,
                "service_date": claim.service_date
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/claims/sample")
async def get_sample_claim():
    """Get a sample EDI 837 claim for testing"""
    edi = generate_sample_edi()
    parsed = parse_edi_837(edi)
    return {
        "raw_edi": edi,
        "parsed": {
            "claim_id": parsed.claim_id,
            "patient_name": parsed.patient_name,
            "patient_dob": parsed.patient_dob,
            "payer_id": parsed.payer_id,
            "payer_name": parsed.payer_name,
            "provider_npi": parsed.provider_npi,
            "diagnosis_codes": parsed.diagnosis_codes,
            "cpt_codes": parsed.cpt_codes,
            "total_charge": parsed.total_charge,
            "service_date": parsed.service_date
        }
    }

from denial_agent import analyze_claim

@app.get("/claims/analyze-sample")
async def analyze_sample_claim():
    """Analyze the sample claim for denial risk"""
    from edi_parser import generate_sample_edi
    edi = generate_sample_edi()
    claim = parse_edi_837(edi)
    
    try:
        analysis = analyze_claim(claim)
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
        return {"success": False, "error": str(e)}