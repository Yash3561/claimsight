import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from database import create_tables, SessionLocal, ClaimRecord, AnalysisRecord, AuditLog
from datetime import datetime, timedelta
import random

# Real CPT codes with descriptions and typical charges
CPT_CODES = {
    "90837": {"desc": "Psychotherapy 60 min", "charge": 200.0, "high_risk_payers": ["BCBS", "Aetna", "United"]},
    "90834": {"desc": "Psychotherapy 45 min", "charge": 150.0, "high_risk_payers": ["Aetna", "Cigna"]},
    "90832": {"desc": "Psychotherapy 30 min", "charge": 100.0, "high_risk_payers": []},
    "90791": {"desc": "Psychiatric Diagnostic Eval", "charge": 350.0, "high_risk_payers": ["BCBS", "Aetna", "United", "Cigna"]},
    "90792": {"desc": "Psychiatric Eval with Medical", "charge": 400.0, "high_risk_payers": ["BCBS", "United"]},
    "96130": {"desc": "Psychological Testing", "charge": 250.0, "high_risk_payers": ["BCBS", "United", "Cigna"]},
    "99213": {"desc": "Office Visit Est Low", "charge": 120.0, "high_risk_payers": []},
    "99214": {"desc": "Office Visit Est Mod", "charge": 185.0, "high_risk_payers": ["Medicaid"]},
    "99215": {"desc": "Office Visit Est High", "charge": 250.0, "high_risk_payers": ["Medicaid", "Cigna"]},
    "99203": {"desc": "Office Visit New Low", "charge": 150.0, "high_risk_payers": []},
    "99204": {"desc": "Office Visit New Mod", "charge": 220.0, "high_risk_payers": ["Medicaid"]},
    "90847": {"desc": "Family Psychotherapy", "charge": 180.0, "high_risk_payers": ["Cigna", "Aetna"]},
    "90853": {"desc": "Group Psychotherapy", "charge": 75.0, "high_risk_payers": []},
    "96127": {"desc": "Brief Emotional Assessment", "charge": 30.0, "high_risk_payers": []},
    "90839": {"desc": "Psychotherapy Crisis 60 min", "charge": 280.0, "high_risk_payers": ["BCBS", "United", "Aetna"]},
}

# Real ICD-10 codes
DIAGNOSIS_CODES = [
    ["F32.1", "Z00.00"],   # Major Depression, Moderate + Wellness exam
    ["F41.1", "F32.0"],   # GAD + Depression, Mild
    ["F33.1"],             # Major Depression Recurrent
    ["F43.10", "F41.1"],  # PTSD + GAD
    ["F32.9"],             # Depression unspecified
    ["F41.9", "Z13.89"],  # Anxiety unspecified + Mental health screening
    ["F33.0", "F41.1"],   # MDD Recurrent Mild + GAD
    ["F43.23"],            # Adjustment disorder with anxiety
    ["F32.2", "F41.1"],   # MDD Severe + GAD
    ["F40.10"],            # Social anxiety
    ["M54.5", "M79.3"],   # Low back pain + Myalgia
    ["J06.9", "Z00.00"],  # URI + Wellness
    ["E11.9", "I10"],     # Type 2 Diabetes + Hypertension
    ["I10", "E78.5"],     # Hypertension + Hyperlipidemia
    ["K21.0", "K58.9"],   # GERD + IBS
]

# Real payers with realistic denial patterns
PAYERS = [
    {
        "name": "BCBS ILLINOIS",
        "id": "00430",
        "denial_rate": 0.65,
        "common_denials": ["CO-50", "CO-97", "CO-B7"],
    },
    {
        "name": "AETNA",
        "id": "60054",
        "denial_rate": 0.55,
        "common_denials": ["CO-50", "CO-4", "CO-167"],
    },
    {
        "name": "UNITED HEALTHCARE",
        "id": "87726",
        "denial_rate": 0.60,
        "common_denials": ["CO-50", "CO-97", "PR-1"],
    },
    {
        "name": "CIGNA",
        "id": "62308",
        "denial_rate": 0.45,
        "common_denials": ["CO-4", "CO-50", "CO-22"],
    },
    {
        "name": "HUMANA",
        "id": "61101",
        "denial_rate": 0.40,
        "common_denials": ["CO-97", "PR-1", "CO-50"],
    },
    {
        "name": "MEDICARE",
        "id": "00120",
        "denial_rate": 0.30,
        "common_denials": ["CO-96", "CO-50", "CO-4"],
    },
    {
        "name": "MEDICAID ILLINOIS",
        "id": "77777",
        "denial_rate": 0.70,
        "common_denials": ["CO-50", "CO-167", "CO-B7"],
    },
]

DENIAL_DESCRIPTIONS = {
    "CO-50": "Not medically necessary",
    "CO-97": "Payment included in allowance for another service",
    "CO-4": "Procedure code inconsistent with modifier",
    "CO-167": "Diagnosis not covered",
    "CO-96": "Non-covered charge",
    "CO-B7": "Not authorized by provider",
    "CO-22": "Coordination of benefits",
    "PR-1": "Deductible amount",
}

PATIENT_NAMES = [
    ("SMITH", "JOHN"), ("JOHNSON", "MARY"), ("WILLIAMS", "JAMES"),
    ("BROWN", "PATRICIA"), ("JONES", "ROBERT"), ("GARCIA", "LINDA"),
    ("MILLER", "MICHAEL"), ("DAVIS", "BARBARA"), ("RODRIGUEZ", "WILLIAM"),
    ("MARTINEZ", "ELIZABETH"), ("HERNANDEZ", "DAVID"), ("LOPEZ", "JENNIFER"),
    ("GONZALEZ", "RICHARD"), ("WILSON", "MARIA"), ("ANDERSON", "CHARLES"),
    ("THOMAS", "SUSAN"), ("TAYLOR", "JOSEPH"), ("MOORE", "JESSICA"),
    ("JACKSON", "THOMAS"), ("MARTIN", "SARAH"), ("LEE", "CHRISTOPHER"),
    ("PEREZ", "KAREN"), ("THOMPSON", "MATTHEW"), ("WHITE", "NANCY"),
    ("HARRIS", "ANTHONY"), ("SANCHEZ", "LISA"), ("CLARK", "MARK"),
]

PROVIDER_NPIS = [
    "1234567890", "1987654321", "1122334455",
    "1556677889", "1998877665", "1443322110",
    "1776655443", "1334455667", "1889900112",
]

def generate_risk_score(payer: dict, cpt_codes: list) -> dict:
    """Generate realistic risk score based on payer and CPT patterns"""
    base_risk = int(payer["denial_rate"] * 100)
    
    high_risk_cpts = [c for c in cpt_codes 
                     if payer["name"].split()[0] in CPT_CODES.get(c["code"], {}).get("high_risk_payers", [])]
    
    if high_risk_cpts:
        base_risk += random.randint(10, 25)
    
    base_risk += random.randint(-15, 15)
    base_risk = max(10, min(98, base_risk))
    
    if base_risk >= 80:
        risk_level = "CRITICAL"
    elif base_risk >= 60:
        risk_level = "HIGH"
    elif base_risk >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    denial_code = random.choice(payer["common_denials"])
    
    return {
        "risk_score": base_risk,
        "risk_level": risk_level,
        "confidence": random.randint(78, 97),
        "top_denial_reasons": [
            {
                "code": denial_code,
                "description": DENIAL_DESCRIPTIONS[denial_code],
                "explanation": f"{payer['name']} commonly denies this service combination"
            }
        ],
        "counterfactuals": [
            {
                "change": "Obtain prior authorization before service",
                "impact": "Reduces denial risk significantly",
                "new_risk_score": max(10, base_risk - random.randint(30, 50))
            }
        ],
        "plain_english": f"This claim has a {base_risk}% chance of denial from {payer['name']} based on historical patterns for these service codes.",
        "recommended_action": f"Verify prior authorization requirements with {payer['name']} before submitting.",
        "rule_flags": [f"CPT {c['code']} has elevated denial rate with {payer['name']}" for c in high_risk_cpts]
    }

def generate_edi_837(claim_id, patient, payer, provider_npi, diagnosis_codes, cpt_codes, service_date, total_charge):
    """Generate realistic EDI 837 Professional claim"""
    sv1_lines = []
    for cpt in cpt_codes:
        sv1_lines.append(f"SV1*HC:{cpt['code']}*{cpt['charge']:.2f}*UN*1***1~")
    
    hi_codes = "*".join([f"ABK:{dx}" if i == 0 else f"ABF:{dx}" 
                         for i, dx in enumerate(diagnosis_codes)])
    
    date_formatted = service_date.strftime("%Y%m%d")
    dob = f"19{random.randint(60,99)}{random.randint(1,12):02d}{random.randint(1,28):02d}"
    
    edi = f"""ISA*00*          *00*          *ZZ*SUBMITTERS ID   *ZZ*RECEIVERS ID    *{date_formatted[:6]}*1253*^*00501*000000905*0*T*:~
GS*HC*SENDER*RECEIVER*{date_formatted}*1253*1*X*005010X222A1~
ST*837*0001*005010X222A1~
BPR*22*{total_charge:.2f}*C*ACH~
NM1*41*2*BILLING PROVIDER*****46*123456789~
NM1*40*2*{payer['name']}*****46*{payer['id']}~
HL*1**20*1~
NM1*85*2*THERAPY CLINIC*****XX*{provider_npi}~
HL*2*1*22*0~
NM1*QC*1*{patient[0]}*{patient[1]}****MI*{random.randint(10000000000, 99999999999)}~
DMG*D8*{dob}*M~
CLM*{claim_id}*{total_charge:.2f}***11:B:1*Y*A*Y*I~
DTP*472*D8*{date_formatted}~
HI*{hi_codes}~
{''.join(sv1_lines)}
SE*20*0001~
GE*1*1~
IEA*1*000000905~"""
    
    return edi

def seed_database():
    create_tables()
    db = SessionLocal()
    
    try:
        existing = db.query(ClaimRecord).count()
        if existing > 5:
            print(f"Database already has {existing} claims. Skipping seed.")
            return
        
        print("🌱 Seeding ClaimSight with realistic claims...")
        
        # Generate 28 claims across different scenarios
        claims_config = [
            # High risk mental health claims
            {"cpts": ["90837", "90791", "96130"], "dx_idx": 0, "payer_idx": 0, "days_ago": 45},
            {"cpts": ["90837", "90791"], "dx_idx": 1, "payer_idx": 1, "days_ago": 42},
            {"cpts": ["90792", "90837"], "dx_idx": 2, "payer_idx": 2, "days_ago": 40},
            {"cpts": ["90839", "90837"], "dx_idx": 8, "payer_idx": 0, "days_ago": 38},
            {"cpts": ["90791", "96130"], "dx_idx": 3, "payer_idx": 3, "days_ago": 35},
            # Medium risk
            {"cpts": ["90834", "96127"], "dx_idx": 1, "payer_idx": 1, "days_ago": 33},
            {"cpts": ["90847", "90837"], "dx_idx": 6, "payer_idx": 4, "days_ago": 30},
            {"cpts": ["99214", "90837"], "dx_idx": 4, "payer_idx": 2, "days_ago": 28},
            {"cpts": ["90832", "96127"], "dx_idx": 9, "payer_idx": 3, "days_ago": 26},
            {"cpts": ["99215", "90791"], "dx_idx": 7, "payer_idx": 6, "days_ago": 25},
            # Low risk office visits
            {"cpts": ["99213"], "dx_idx": 10, "payer_idx": 5, "days_ago": 23},
            {"cpts": ["99203", "96127"], "dx_idx": 11, "payer_idx": 4, "days_ago": 21},
            {"cpts": ["99214"], "dx_idx": 12, "payer_idx": 5, "days_ago": 20},
            {"cpts": ["99213", "96127"], "dx_idx": 13, "payer_idx": 4, "days_ago": 18},
            {"cpts": ["99204"], "dx_idx": 14, "payer_idx": 5, "days_ago": 16},
            # More high risk
            {"cpts": ["90837", "90847"], "dx_idx": 5, "payer_idx": 0, "days_ago": 15},
            {"cpts": ["90791", "90837", "96130"], "dx_idx": 2, "payer_idx": 1, "days_ago": 14},
            {"cpts": ["90839", "90791"], "dx_idx": 8, "payer_idx": 2, "days_ago": 12},
            {"cpts": ["90792", "96130"], "dx_idx": 3, "payer_idx": 6, "days_ago": 11},
            {"cpts": ["90837", "90853"], "dx_idx": 0, "payer_idx": 3, "days_ago": 10},
            # Mixed
            {"cpts": ["99215", "96127"], "dx_idx": 7, "payer_idx": 1, "days_ago": 9},
            {"cpts": ["90834", "90847"], "dx_idx": 6, "payer_idx": 0, "days_ago": 8},
            {"cpts": ["99214", "96127"], "dx_idx": 4, "payer_idx": 4, "days_ago": 7},
            {"cpts": ["90832"], "dx_idx": 9, "payer_idx": 5, "days_ago": 6},
            {"cpts": ["90837"], "dx_idx": 1, "payer_idx": 2, "days_ago": 5},
            {"cpts": ["99213"], "dx_idx": 11, "payer_idx": 5, "days_ago": 4},
            {"cpts": ["90791", "90837"], "dx_idx": 0, "payer_idx": 0, "days_ago": 3},
            {"cpts": ["99204", "96127"], "dx_idx": 13, "payer_idx": 4, "days_ago": 2},
        ]
        
        for i, config in enumerate(claims_config):
            claim_id = f"CLM-2026-{str(i+1).zfill(4)}"
            patient = random.choice(PATIENT_NAMES)
            payer = PAYERS[config["payer_idx"]]
            provider_npi = random.choice(PROVIDER_NPIS)
            diagnosis_codes = DIAGNOSIS_CODES[config["dx_idx"]]
            service_date = datetime.now() - timedelta(days=config["days_ago"])
            
            cpt_list = []
            total_charge = 0
            for cpt_code in config["cpts"]:
                cpt_info = CPT_CODES[cpt_code]
                charge = cpt_info["charge"] + random.uniform(-20, 20)
                cpt_list.append({
                    "code": cpt_code,
                    "modifier": "GT" if "90837" in cpt_code and random.random() > 0.5 else "",
                    "charge": round(charge, 2)
                })
                total_charge += charge
            
            total_charge = round(total_charge, 2)
            
            raw_edi = generate_edi_837(
                claim_id, patient, payer, provider_npi,
                diagnosis_codes, cpt_list, service_date, total_charge
            )
            
            claim_record = ClaimRecord(
                claim_id=claim_id,
                patient_name=f"{patient[1]} {patient[0]}",
                patient_dob=f"{random.randint(1,12):02d}/{random.randint(1,28):02d}/{random.randint(1960,1995)}",
                payer_id=payer["id"],
                payer_name=payer["name"],
                provider_npi=provider_npi,
                diagnosis_codes=diagnosis_codes,
                cpt_codes=cpt_list,
                total_charge=total_charge,
                service_date=service_date.strftime("%m/%d/%Y"),
                raw_edi=raw_edi,
                created_at=service_date
            )
            db.add(claim_record)
            db.commit()
            
            risk_data = generate_risk_score(payer, cpt_list)
            
            # Some claims have recorded outcomes
            actual_outcome = None
            outcome_recorded_at = None
            if config["days_ago"] > 20:
                if random.random() < payer["denial_rate"]:
                    actual_outcome = "DENIED"
                else:
                    actual_outcome = "APPROVED"
                outcome_recorded_at = datetime.now() - timedelta(days=config["days_ago"] - 14)
            
            analysis_record = AnalysisRecord(
                claim_id=claim_id,
                risk_score=risk_data["risk_score"],
                risk_level=risk_data["risk_level"],
                confidence=risk_data["confidence"],
                top_denial_reasons=risk_data["top_denial_reasons"],
                counterfactuals=risk_data["counterfactuals"],
                rule_flags=risk_data["rule_flags"],
                plain_english=risk_data["plain_english"],
                recommended_action=risk_data["recommended_action"],
                actual_outcome=actual_outcome,
                outcome_recorded_at=outcome_recorded_at,
                created_at=service_date + timedelta(hours=random.randint(1,4))
            )
            db.add(analysis_record)
            
            log = AuditLog(
                action="CLAIM_ANALYZED",
                claim_id=claim_id,
                details={"risk_score": risk_data["risk_score"], "payer": payer["name"]},
                created_at=service_date + timedelta(hours=random.randint(1,4))
            )
            db.add(log)
            db.commit()
            
            print(f"✅ {claim_id} | {patient[1]} {patient[0]} | {payer['name']} | Risk: {risk_data['risk_score']} ({risk_data['risk_level']})")
        
        # Print summary
        total = db.query(ClaimRecord).count()
        high_risk = db.query(AnalysisRecord).filter(AnalysisRecord.risk_score >= 70).count()
        with_outcomes = db.query(AnalysisRecord).filter(AnalysisRecord.actual_outcome != None).count()
        
        print(f"\n🎉 Seeding complete!")
        print(f"📊 Total claims: {total}")
        print(f"🔴 High risk: {high_risk}")
        print(f"✅ With outcomes: {with_outcomes}")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()