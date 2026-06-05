"""Legal Compliance Product for Background Research.

This module provides the core functionality to conduct background research
on a given drug and evaluate it against global standards to produce
legally compliant advice.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any, Dict

from server.kaggle_data import (
    get_drug_properties,
    get_tox21_profile,
    get_faers_signals,
)
from server.domain.external_apis import (
    fetch_live_fda_adverse_events,
    fetch_live_pubchem_properties,
)


def fetch_drug_background(drug_id: str) -> Dict[str, Any]:
    """Retrieve all relevant background data for a drug, attempting live external APIs first."""
    # Attempt to get the full name for the external APIs from the local properties
    full_name = drug_id
    try:
        local_props = get_drug_properties(drug_id)
        full_name = local_props.get("name", drug_id)
    except Exception:
        local_props = {"error": "Properties not found locally"}

    # 1. Properties
    try:
        properties = fetch_live_pubchem_properties(full_name)
    except Exception as e:
        properties = local_props  # fallback
        properties["note"] = f"Live PubChem API failed ({str(e)}), using local data"
        
    # 2. Tox21 (Still local, as Tox21 API requires complex compound mapping)
    try:
        tox21 = get_tox21_profile(drug_id)
    except ValueError:
        tox21 = {"error": "Tox21 data not found"}
        
    # 3. FAERS signals
    try:
        faers = fetch_live_fda_adverse_events(full_name)
    except Exception as e:
        try:
            faers = get_faers_signals(drug_id)
            faers["note"] = f"Live FDA API failed ({str(e)}), using local data"
        except ValueError:
            faers = {"error": "FAERS data not found"}

    return {
        "drug_id": drug_id,
        "full_name": full_name,
        "properties": properties,
        "tox21": tox21,
        "faers": faers,
    }


def generate_legal_compliance_report(drug_id: str) -> Dict[str, Any]:
    """Generate a comprehensive legal compliance report for a drug composition."""
    
    # Step 1: Perform Background Research
    background_data = fetch_drug_background(drug_id)
    
    # Step 2: Use Ollama to generate compliant advice (Fallback to rules if offline)
    background_str = json.dumps(background_data, indent=2)
    
    prompt = (
        "You are an expert pharmaceutical legal and regulatory compliance advisor. "
        "Review the following drug background data (including properties, Tox21 assays, and FAERS signals):\\n"
        f"{background_str}\\n\\n"
        "Generate a legally compliant advisory report based on global standards (e.g., FDA, EMA, ICH guidelines). "
        "Your output MUST be a JSON object with the following keys:\\n"
        "- 'summary': A high-level summary of the compliance profile.\\n"
        "- 'risk_assessment': A detailed analysis of risks found in Tox21 or FAERS data.\\n"
        "- 'regulatory_recommendations': Actionable advice for regulatory submission or clinical trial monitoring.\\n"
        "- 'global_standards_alignment': How well this aligns with international best practices.\\n"
        "Return ONLY the raw JSON object. Do not include any markdown formatting."
    )
    
    data = json.dumps({
        "model": "llama3:latest",
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }).encode("utf-8")
    
    req_obj = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    advice_payload = None
    try:
        with urllib.request.urlopen(req_obj, timeout=30) as response:
            result = json.loads(response.read().decode())
            response_text = result.get("response", "{}")
            advice_payload = json.loads(response_text)
    except Exception as e:
        # Fallback rules engine if LLM fails or is not available
        advice_payload = _generate_fallback_advice(background_data)
        advice_payload["note"] = f"LLM generation failed ({str(e)}). Using fallback rules engine."

    return {
        "drug_id": drug_id,
        "background_research": background_data,
        "legal_advice": advice_payload
    }


def _generate_fallback_advice(background_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback rule-based generation of legal advice."""
    drug_id = background_data.get("drug_id", "unknown")
    properties = background_data.get("properties", {})
    
    # Basic rule-based analysis
    high_risk = False
    tox21 = background_data.get("tox21", {})
    if isinstance(tox21, dict) and not "error" in tox21:
        for assay, result in tox21.items():
            if "Active" in str(result):
                high_risk = True
                
    faers = background_data.get("faers", {})
    faers_risk = False
    if isinstance(faers, dict) and "signals" in faers:
        faers_risk = len(faers["signals"]) > 0

    return {
        "summary": f"Fallback compliance review for {drug_id}.",
        "risk_assessment": "High risk detected in Tox21 assays." if high_risk else ("FAERS signals detected." if faers_risk else "Standard risk profile."),
        "regulatory_recommendations": "Strict monitoring required during trials." if (high_risk or faers_risk) else "Proceed with standard Phase 1 protocols.",
        "global_standards_alignment": "Requires further detailed analysis to ensure full alignment with ICH and FDA guidelines."
    }
