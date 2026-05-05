import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class ParsedClaim:
    claim_id: str
    patient_name: str
    patient_dob: str
    payer_id: str
    payer_name: str
    provider_npi: str
    diagnosis_codes: list[str]
    cpt_codes: list[dict]
    total_charge: float
    service_date: str

def parse_edi_837(edi_content: str) -> ParsedClaim:
    """
    Parse X12 EDI 837 Professional claim format
    into structured data
    """
    segments = edi_content.strip().split('~')
    segments = [s.strip() for s in segments if s.strip()]
    
    claim_id = ""
    patient_name = ""
    patient_dob = ""
    payer_id = ""
    payer_name = ""
    provider_npi = ""
    diagnosis_codes = []
    cpt_codes = []
    total_charge = 0.0
    service_date = ""
    
    for segment in segments:
        elements = segment.split('*')
        seg_id = elements[0]
        
        # Patient name (NM1 segment with qualifier QC)
        if seg_id == 'NM1' and len(elements) > 1 and elements[1] == 'QC':
            last = elements[3] if len(elements) > 3 else ""
            first = elements[4] if len(elements) > 4 else ""
            patient_name = f"{first} {last}".strip()
        
        # Patient DOB (DMG segment)
        if seg_id == 'DMG' and len(elements) > 2:
            raw_dob = elements[2]
            if len(raw_dob) == 8:
                patient_dob = f"{raw_dob[4:6]}/{raw_dob[6:8]}/{raw_dob[0:4]}"
        
        # Payer info (NM1 with qualifier PR)
        if seg_id == 'NM1' and len(elements) > 1 and elements[1] == '40':
            payer_name = elements[3] if len(elements) > 3 else ""
            payer_id = elements[9] if len(elements) > 9 else ""
        
        # Provider NPI (NM1 with qualifier 85)
        if seg_id == 'NM1' and len(elements) > 1 and elements[1] == '85':
            provider_npi = elements[9] if len(elements) > 9 else ""
        
        # Diagnosis codes (HI segment)
        if seg_id == 'HI':
            for el in elements[1:]:
                if ':' in el:
                    parts = el.split(':')
                    if len(parts) > 1 and parts[1]:
                        diagnosis_codes.append(parts[1])
        
        # Claim ID and total charge (CLM segment)
        if seg_id == 'CLM':
            claim_id = elements[1] if len(elements) > 1 else ""
            try:
                total_charge = float(elements[2]) if len(elements) > 2 else 0.0
            except ValueError:
                total_charge = 0.0
        
        # Service lines - CPT codes (SV1 segment)
        if seg_id == 'SV1' and len(elements) > 1:
            cpt_info = elements[1].split(':')
            cpt_code = cpt_info[1] if len(cpt_info) > 1 else ""
            modifier = cpt_info[2] if len(cpt_info) > 2 else ""
            try:
                charge = float(elements[2]) if len(elements) > 2 else 0.0
            except ValueError:
                charge = 0.0
            if cpt_code:
                cpt_codes.append({
                    "code": cpt_code,
                    "modifier": modifier,
                    "charge": charge
                })
        
        # Service date (DTP segment with qualifier 472)
        if seg_id == 'DTP' and len(elements) > 1 and elements[1] == '472':
            raw_date = elements[3] if len(elements) > 3 else ""
            if len(raw_date) == 8:
                service_date = f"{raw_date[4:6]}/{raw_date[6:8]}/{raw_date[0:4]}"
    
    return ParsedClaim(
        claim_id=claim_id,
        patient_name=patient_name,
        patient_dob=patient_dob,
        payer_id=payer_id,
        payer_name=payer_name,
        provider_npi=provider_npi,
        diagnosis_codes=diagnosis_codes,
        cpt_codes=cpt_codes,
        total_charge=total_charge,
        service_date=service_date
    )


def generate_sample_edi() -> str:
    """
    Generate a realistic sample EDI 837 claim
    for testing purposes
    """
    return """ISA*00*          *00*          *ZZ*SUBMITTERS ID   *ZZ*RECEIVERS ID    *200101*1253*^*00501*000000905*0*T*:~
GS*HC*SENDER*RECEIVER*20200101*1253*1*X*005010X222A1~
ST*837*0001*005010X222A1~
BPR*22*1500.00*C*ACH~
NM1*41*2*BILLING PROVIDER*****46*123456789~
NM1*40*2*BCBS ILLINOIS*****46*00430~
HL*1**20*1~
NM1*85*2*THERAPY CLINIC*****XX*1234567890~
HL*2*1*22*0~
NM1*QC*1*SMITH*JOHN****MI*12345678901~
DMG*D8*19850315*M~
CLM*CLAIM-2024-001*1500.00***11:B:1*Y*A*Y*I~
DTP*472*D8*20240115~
HI*ABK:F32.1*ABF:Z00.00~
SV1*HC:90837:GT*200.00*UN*1***1~
SV1*HC:90791**150.00*UN*1***1~
SV1*HC:96130**250.00*UN*1***1~
SE*20*0001~
GE*1*1~
IEA*1*000000905~"""