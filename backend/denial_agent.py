from groq import Groq
from edi_parser import ParsedClaim
import os
import json

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Real denial reason codes used by payers
DENIAL_CODES = {
    "CO-50": "Not medically necessary",
    "CO-97": "Payment included in another service",
    "CO-4": "Procedure code inconsistent with modifier",
    "PR-1": "Deductible amount",
    "CO-167": "Diagnosis not covered",
    "CO-96": "Non-covered charge",
    "CO-B7": "Not authorized by provider",
    "CO-22": "Coordination of benefits",
}

# Known high-risk CPT/payer combinations
HIGH_RISK_COMBINATIONS = {
    "90837": {
        "requires_modifier_telehealth": ["GT", "95"],
        "requires_prior_auth_payers": ["BCBS", "Aetna", "United"],
        "max_units_per_day": 1,
        "requires_diagnosis": ["F32", "F33", "F41", "F42", "F43"]
    },
    "90791": {
        "requires_prior_auth_payers": ["BCBS", "Aetna"],
        "max_units_per_year": 1,
    },
    "96130": {
        "requires_prior_auth_payers": ["BCBS", "United", "Cigna"],
        "requires_modifier": True,
    }
}

def analyze_claim(claim: ParsedClaim) -> dict:
    """
    Analyze a parsed claim and predict denial risk
    using Groq LLM + rule-based checks
    """
    
    # Rule-based pre-checks
    rule_flags = []
    
    for cpt in claim.cpt_codes:
        code = cpt["code"]
        modifier = cpt.get("modifier", "")
        
        if code in HIGH_RISK_COMBINATIONS:
            rules = HIGH_RISK_COMBINATIONS[code]
            
            # Check if payer requires prior auth
            payer_upper = claim.payer_name.upper()
            for payer in rules.get("requires_prior_auth_payers", []):
                if payer.upper() in payer_upper:
                    rule_flags.append(
                        f"CPT {code} typically requires prior authorization "
                        f"from {claim.payer_name}"
                    )
            
            # Check diagnosis compatibility
            required_dx = rules.get("requires_diagnosis", [])
            if required_dx:
                has_valid_dx = any(
                    any(dx.startswith(req) for req in required_dx)
                    for dx in claim.diagnosis_codes
                )
                if not has_valid_dx:
                    rule_flags.append(
                        f"CPT {code} may not be covered for "
                        f"diagnosis codes: {', '.join(claim.diagnosis_codes)}"
                    )
    
    # Build prompt for Groq
    claim_summary = f"""
    Claim ID: {claim.claim_id}
    Payer: {claim.payer_name} (ID: {claim.payer_id})
    Patient DOB: {claim.patient_dob}
    Service Date: {claim.service_date}
    Provider NPI: {claim.provider_npi}
    
    Diagnosis Codes: {', '.join(claim.diagnosis_codes)}
    
    CPT Codes:
    {chr(10).join([f"  - {c['code']} (modifier: {c['modifier'] or 'none'}, charge: ${c['charge']})" for c in claim.cpt_codes])}
    
    Total Charge: ${claim.total_charge}
    
    Pre-analysis flags:
    {chr(10).join(rule_flags) if rule_flags else 'None'}
    """
    
    prompt = f"""You are an expert healthcare claims analyst with 20 years of experience 
in medical billing and insurance denials.

Analyze this healthcare claim and provide a denial risk assessment:

{claim_summary}

Respond with ONLY a JSON object in this exact format:
{{
    "risk_score": <integer 0-100>,
    "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
    "top_denial_reasons": [
        {{
            "code": "<denial code like CO-50>",
            "description": "<description>",
            "explanation": "<specific explanation for this claim>"
        }}
    ],
    "counterfactuals": [
        {{
            "change": "<what to change>",
            "impact": "<how it reduces risk>",
            "new_risk_score": <integer 0-100>
        }}
    ],
    "plain_english": "<explain in simple terms why this claim might be denied>",
    "confidence": <integer 0-100>,
    "recommended_action": "<specific action to take before submission>"
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1500
    )
    
    raw = response.choices[0].message.content.strip()
    
    # Clean JSON if wrapped in markdown
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    
    result = json.loads(raw)
    
    # Add rule-based flags to result
    result["rule_flags"] = rule_flags
    result["claim_id"] = claim.claim_id
    
    return result