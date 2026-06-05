"""
External API Adapters for Live Background Research.

This module provides functions to fetch live data from public external APIs
such as OpenFDA (for Adverse Events) and PubChem (for Molecular Properties).
"""

import json
import urllib.request
import urllib.parse
from typing import Any, Dict


def fetch_live_fda_adverse_events(drug_name: str, limit: int = 10) -> Dict[str, Any]:
    """
    Fetch live Adverse Event data (FAERS) from the OpenFDA API.
    
    Args:
        drug_name (str): The common name of the drug (e.g., "valproic acid").
        limit (int): The number of top adverse events to return.
        
    Returns:
        Dict: Parsed JSON response containing the top reactions.
    """
    # OpenFDA exact match count query
    encoded_name = urllib.parse.quote(f'"{drug_name}"')
    url = (
        f"https://api.fda.gov/drug/event.json"
        f"?search=patient.drug.medicinalproduct:{encoded_name}"
        f"&count=patient.reaction.reactionmeddrapt.exact"
        f"&limit={limit}"
    )
    
    req = urllib.request.Request(url, headers={"User-Agent": "QuantaMed-Research-Bot/1.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            results = data.get("results", [])
            
            # Reformat to match the expected schema
            top_events = [
                {
                    "event": item.get("term"),
                    "count": item.get("count"),
                }
                for item in results
            ]
            
            return {
                "source": "OpenFDA Live API",
                "drug_name": drug_name,
                "top_events": top_events
            }
    except Exception as e:
        raise RuntimeError(f"Failed to fetch FDA data for {drug_name}: {e}")


def fetch_live_pubchem_properties(drug_name: str) -> Dict[str, Any]:
    """
    Fetch molecular properties from the PubChem REST API.
    
    Args:
        drug_name (str): The common name of the drug.
        
    Returns:
        Dict: A dictionary of key molecular properties.
    """
    encoded_name = urllib.parse.quote(drug_name)
    properties_list = "MolecularWeight,XLogP,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,TopologicalPolarSurfaceArea"
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/property/{properties_list}/JSON"
    
    req = urllib.request.Request(url, headers={"User-Agent": "QuantaMed-Research-Bot/1.0", "Accept": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            props = data.get("PropertyTable", {}).get("Properties", [])
            if not props:
                raise ValueError("No properties found in response")
            
            first_hit = props[0]
            
            return {
                "source": "PubChem Live API",
                "cid": first_hit.get("CID"),
                "mw": first_hit.get("MolecularWeight"),
                "logp": first_hit.get("XLogP"),
                "psa": first_hit.get("TopologicalPolarSurfaceArea"),
                "hbd": first_hit.get("HBondDonorCount"),
                "hba": first_hit.get("HBondAcceptorCount"),
                "rotatable_bonds": first_hit.get("RotatableBondCount")
            }
    except Exception as e:
        raise RuntimeError(f"Failed to fetch PubChem data for {drug_name}: {e}")
