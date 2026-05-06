import sys
import os
sys.path.append(os.path.dirname(__file__))

from groq import Groq
from database import AnalysisRecord, ClaimRecord
import json
from datetime import datetime

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def generate_appeal(claim: ClaimRecord, analysis: AnalysisRecord) -> dict:
    """
    Generate a professional appeal letter for a denied claim
    with specific policy citations and medical necessity arguments
    """
    
    cpt_descriptions = {
        "90837": "Psychotherapy, 60 minutes",
        "90791": "Psychiatric diagnostic evaluation",
        "90834": "Psychotherapy, 45 minutes",
        "90832": "Psychotherapy, 30 minutes",
        "96130": "Psychological testing evaluation",
        "96131": "Psychological testing, additional hour",
        "99213": "Office visit, established patient, low complexity",
        "99214": "Office visit, established patient, moderate complexity",
        "99215": "Office visit, established patient, high complexity",
    }
    
    cpt_details = []
    for cpt in claim.cpt_codes:
        desc = cpt_descriptions.get(cpt["code"], f"CPT {cpt['code']}")
        cpt_details.append(f"{cpt['code']} - {desc} (${cpt['charge']})")
    
    denial_reasons = []
    for reason in analysis.top_denial_reasons:
        denial_reasons.append(
            f"{reason['code']}: {reason['description']} - {reason['explanation']}"
        )
    
    prompt = f"""You are an expert medical billing specialist with 20 years of experience 
writing successful insurance appeal letters. Write a professional, compelling appeal letter 
for the following denied claim.

CLAIM DETAILS:
- Claim ID: {claim.claim_id}
- Patient DOB: {claim.patient_dob}
- Service Date: {claim.service_date}
- Payer: {claim.payer_name}
- Provider NPI: {claim.provider_npi}
- Diagnosis Codes: {', '.join(claim.diagnosis_codes)}
- Services Provided:
  {chr(10).join(cpt_details)}
- Total Charge: ${claim.total_charge}

DENIAL REASONS:
{chr(10).join(denial_reasons)}

AI RISK ANALYSIS:
{analysis.plain_english}

Write a formal appeal letter that:
1. Opens with formal greeting to the Appeals Department
2. Clearly states the claim being appealed with all identifiers
3. Argues medical necessity with clinical justification
4. References specific payer policy language and CMS guidelines
5. Cites relevant clinical literature or treatment guidelines
6. Requests specific action (overturn denial, expedited review)
7. Closes professionally with contact information placeholder

The letter should be authoritative, specific, and compelling.
Use professional medical billing language.

Respond with ONLY a JSON object:
{{
    "letter": "<full appeal letter text with \\n for line breaks>",
    "key_arguments": ["<argument 1>", "<argument 2>", "<argument 3>"],
    "supporting_codes": ["<relevant policy/regulation codes>"],
    "estimated_success_rate": <integer 0-100>,
    "urgency_level": "<STANDARD|EXPEDITED|URGENT>"
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2000
    )
    
    raw = response.choices[0].message.content.strip()
    
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    
    result = json.loads(raw)
    result["generated_at"] = datetime.utcnow().isoformat()
    result["claim_id"] = claim.claim_id
    
    return result