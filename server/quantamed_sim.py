"""QuantaMed Simulation Backend.

This module provides simulation functions.
"""
# pylint: disable=invalid-name,too-many-arguments,too-many-locals,line-too-long
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np  # noqa: F401

# ---------------------------------------------------------------------------
# Qiskit imports — wrapped in try/except so the server can start without
# a working Qiskit installation.  When Qiskit is unavailable the protein-
# folding endpoint returns cached results with a "backend: cached_fallback"
# flag so the dashboard can display a "Cached" badge.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
_QISKIT_AVAILABLE = False
try:
    from qiskit import BasicAer  # type: ignore[import-untyped]
    from qiskit.algorithms import VQE  # type: ignore[import-untyped]
    from qiskit.algorithms.optimizers import COBYLA  # type: ignore[import-untyped]
    from qiskit.circuit.library import TwoLocal  # type: ignore[import-untyped]
    from qiskit.quantum_info import Statevector, Operator, SparsePauliOp  # type: ignore[import-untyped]
    from qiskit.opflow import PauliSumOp  # type: ignore[import-untyped]
    from qiskit.utils import QuantumInstance  # type: ignore[import-untyped]
    _QISKIT_AVAILABLE = True
except ImportError:
    pass


@dataclass(frozen=True)
class _DrugPkParams:
    drug_id: str
    label: str
    bioavailability: float
    vd_l: float
    half_life_h: float
    default_doses_per_day: int
    therapeutic_range_ug_ml: tuple[float, float] | None


_PK_PARAMS: dict[str, _DrugPkParams] = {
    # Note: These are hackathon-grade illustrative parameters (not for clinical use).
    # They are chosen to produce stable, intuitive PK curves and sensible unit scales.
    "vpa": _DrugPkParams(
        drug_id="vpa",
        label="Valproic Acid",
        bioavailability=1.0,
        vd_l=15.0,
        half_life_h=15.0,
        default_doses_per_day=2,
        therapeutic_range_ug_ml=(50.0, 100.0),
    ),
    "ltg": _DrugPkParams(
        drug_id="ltg",
        label="Lamotrigine",
        bioavailability=0.98,
        vd_l=25.0,
        half_life_h=25.0,
        default_doses_per_day=2,
        therapeutic_range_ug_ml=None,
    ),
    "lev": _DrugPkParams(
        drug_id="lev",
        label="Levetiracetam",
        bioavailability=0.95,
        vd_l=42.0,
        half_life_h=7.0,
        default_doses_per_day=2,
        therapeutic_range_ug_ml=None,
    ),
    "tpm": _DrugPkParams(
        drug_id="tpm",
        label="Topiramate",
        bioavailability=0.80,
        vd_l=55.0,
        half_life_h=21.0,
        default_doses_per_day=2,
        therapeutic_range_ug_ml=None,
    ),
    "zns": _DrugPkParams(
        drug_id="zns",
        label="Zonisamide",
        bioavailability=0.65,
        vd_l=45.0,
        half_life_h=63.0,
        default_doses_per_day=1,
        therapeutic_range_ug_ml=(10.0, 40.0),
    ),
}


def _cyp2c9_clearance_multiplier(phenotype: str) -> float:
    """Return a multiplier applied to ke (i.e., clearance proportional).

    Example: 0.7 means 30% lower elimination rate (higher exposure).
    """
    p = (phenotype or "").strip().lower()
    if p in {"pm", "poor", "poor_metabolizer"}:
        return 0.55
    if p in {"im", "inter", "intermediate", "intermediate_metabolizer"}:
        return 0.70
    # normal / unknown
    return 1.0


def _ltg_co_med_ke_multiplier(co_med: str) -> float:
    """Return a multiplier applied to LTG ke to represent DDIs (demo-level).

    - VPA co-therapy reduces LTG clearance (↑ exposure) -> lower ke
    - Estrogen-containing OCP increases LTG clearance (↓ exposure) -> higher ke
    """
    cm = (co_med or "").strip().lower()
    if cm in {"vpa", "valproate", "valproic_acid"}:
        return 0.55
    if cm in {"ocp", "estrogen", "ethinylestradiol"}:
        return 1.50
    return 1.0


def compute_pk_curve(
    *,
    drug_id: str,
    daily_dose_mg: float,
    doses_per_day: int | None = None,
    cyp2c9: str = "normal",
    co_med: str = "none",
    hours: float = 24.0,
    step_h: float = 0.25,
) -> dict[str, Any]:
    """One-compartment, repeated bolus dosing at steady state.

    Returns concentrations in ug/mL (numerically equal to mg/L).
    """
    key = (drug_id or "").strip().lower()
    if key not in _PK_PARAMS:
        raise ValueError(f"Unsupported drug_id '{drug_id}'. Valid: {sorted(_PK_PARAMS.keys())}")

    params = _PK_PARAMS[key]
    if doses_per_day is None:
        doses_per_day = params.default_doses_per_day
    if doses_per_day <= 0:
        raise ValueError("doses_per_day must be >= 1")
    if daily_dose_mg <= 0:
        raise ValueError("daily_dose_mg must be > 0")

    tau_h = 24.0 / float(doses_per_day)
    dose_interval_mg = float(daily_dose_mg) / float(doses_per_day)

    ke_h_inv = math.log(2.0) / float(params.half_life_h)
    # Only apply CYP2C9 modifier where it makes sense (here: VPA demo).
    if params.drug_id == "vpa":
        ke_h_inv *= _cyp2c9_clearance_multiplier(cyp2c9)
    if params.drug_id == "ltg":
        ke_h_inv *= _ltg_co_med_ke_multiplier(co_med)

    if ke_h_inv <= 0:
        raise ValueError("Invalid ke computed")

    # Steady-state for IV bolus approximation:
    # Cmax_ss = (F*dose/Vd) / (1 - exp(-ke*tau))
    denom = 1.0 - math.exp(-ke_h_inv * tau_h)
    cmax = (params.bioavailability * dose_interval_mg / params.vd_l) / denom
    cmin = cmax * math.exp(-ke_h_inv * tau_h)
    cavg = (params.bioavailability * dose_interval_mg) / (ke_h_inv * params.vd_l * tau_h)

    # Build a 0..hours curve (repeat within each dosing interval).
    n = max(2, int(hours / step_h) + 1)
    times = [round(i * step_h, 5) for i in range(n)]
    conc = []
    for t in times:
        t_since = t % tau_h
        conc.append(cmax * math.exp(-ke_h_inv * t_since))

    tr = params.therapeutic_range_ug_ml
    status = "ok"
    if tr is not None and cavg > tr[1]:
        status = "high"
    elif tr is not None and cavg < tr[0]:
        status = "low"

    return {
        "model": "one_compartment_bolus_steady_state",
        "drug": {
            "drug_id": params.drug_id,
            "label": params.label,
            "bioavailability": params.bioavailability,
            "vd_l": params.vd_l,
            "half_life_h_base": params.half_life_h,
            "therapeutic_range_ug_ml": tr,
        },
        "inputs": {
            "daily_dose_mg": float(daily_dose_mg),
            "doses_per_day": int(doses_per_day),
            "cyp2c9": (cyp2c9 or "").strip().lower(),
            "co_med": (co_med or "").strip().lower(),
            "hours": float(hours),
            "step_h": float(step_h),
        },
        "derived": {
            "tau_h": tau_h,
            "dose_interval_mg": dose_interval_mg,
            "ke_h_inv": ke_h_inv,
            "cmax_ug_ml": cmax,
            "cmin_ug_ml": cmin,
            "cavg_ug_ml": cavg,
            "status": status,
        },
        "series": {"t_h": times, "c_ug_ml": [round(x, 4) for x in conc]},
    }


# ---------------------------------------------------------------------------
# QuantaMed candidate scoring and personalized compatibility simulation

_CANDIDATE_DRUGS: dict[str, dict[str, Any]] = {
    "ltg": {
        "drug_id": "ltg",
        "label": "Lamotrigine",
        "target": "Glutamate NMDA receptor / sodium channel modulation",
        "summary": "Mood stabilization by dampening glutamate release and sodium currents.",
        "quantum_energy_ev": -2.84,
        "quantum_binding_score": 88,
        "bbb_penetration_pct": 91,
        "lipinski": {"mw": 256.09, "logp": 2.1, "hbd": 1, "hba": 3},
        "manufacturability": 91,
        "base_safety": 88,
        "off_target_profile": {
            "hERG": 0.12,
            "CYP2C19": 0.14,
            "Androgen receptor": 0.08,
            "Sigma-1": 0.10,
        },
        "pillars": {
            "efficacy": 88,
            "safety": 84,
            "manufacturability": 91,
            "bbb": 91,
        },
    },
    "vpa": {
        "drug_id": "vpa",
        "label": "Valproic Acid",
        "target": "GABAergic enhancement / histone deacetylase modulation",
        "summary": "Broad-spectrum anticonvulsant with mood stabilizing efficacy; strong exposure sensitivity to CYP2C9 genotype.",
        "quantum_energy_ev": -2.71,
        "quantum_binding_score": 76,
        "bbb_penetration_pct": 87,
        "lipinski": {"mw": 144.21, "logp": 2.0, "hbd": 1, "hba": 2},
        "manufacturability": 84,
        "base_safety": 68,
        "off_target_profile": {
            "hERG": 0.18,
            "CYP2C9": 0.30,
            "Androgen receptor": 0.22,
            "Estrogen receptor": 0.16,
        },
        "pillars": {
            "efficacy": 82,
            "safety": 68,
            "manufacturability": 84,
            "bbb": 87,
        },
    },
    "lev": {
        "drug_id": "lev",
        "label": "Levetiracetam",
        "target": "SV2A synaptic vesicle protein",
        "summary": "Fast-acting synaptic release modulator with low off-target liability and high manufacturability.",
        "quantum_energy_ev": -2.21,
        "quantum_binding_score": 82,
        "bbb_penetration_pct": 62,
        "lipinski": {"mw": 170.21, "logp": -0.4, "hbd": 1, "hba": 4},
        "manufacturability": 93,
        "base_safety": 92,
        "off_target_profile": {
            "hERG": 0.06,
            "CYP2C19": 0.05,
            "Dopamine receptor": 0.11,
            "Histamine H1": 0.08,
        },
        "pillars": {
            "efficacy": 74,
            "safety": 92,
            "manufacturability": 93,
            "bbb": 62,
        },
    },
    "tpm": {
        "drug_id": "tpm",
        "label": "Topiramate",
        "target": "AMPA/kainate receptors + carbonic anhydrase",
        "summary": "Multi-target neuromodulator with moderate binding and strong manufacturability, but attention to cognitive side effects is needed.",
        "quantum_energy_ev": -2.44,
        "quantum_binding_score": 79,
        "bbb_penetration_pct": 78,
        "lipinski": {"mw": 339.39, "logp": -0.2, "hbd": 2, "hba": 5},
        "manufacturability": 87,
        "base_safety": 74,
        "off_target_profile": {
            "hERG": 0.10,
            "Carbonic anhydrase": 0.22,
            "GABA-B": 0.14,
            "Serotonin receptor": 0.12,
        },
        "pillars": {
            "efficacy": 80,
            "safety": 74,
            "manufacturability": 87,
            "bbb": 78,
        },
    },
    "zns": {
        "drug_id": "zns",
        "label": "Zonisamide",
        "target": "Sodium/calcium channel blockade + carbonic anhydrase inhibition",
        "summary": "Dual-mechanism anticonvulsant with moderate binding and good BBB penetration; long half-life supports once-daily dosing.",
        "quantum_energy_ev": -2.05,
        "quantum_binding_score": 58,
        "bbb_penetration_pct": 84,
        "lipinski": {"mw": 212.23, "logp": -0.2, "hbd": 1, "hba": 4},
        "manufacturability": 82,
        "base_safety": 76,
        "off_target_profile": {
            "hERG": 0.09,
            "Carbonic anhydrase": 0.34,
            "CYP3A4": 0.18,
            "Dopamine receptor": 0.14,
        },
        "pillars": {
            "efficacy": 64,
            "safety": 76,
            "manufacturability": 82,
            "bbb": 84,
        },
    },
}

_PATIENT_PROFILES: dict[str, dict[str, Any]] = {
    "juvenile_myoclonic_epilepsy": {
        "patient_id": "juvenile_myoclonic_epilepsy",
        "name": "Gabi",
        "condition": "Juvenile Myoclonic Epilepsy",
        "sex": "female",
        "age": 24,
        "weight_kg": 58,
        "cyp_genotype": "intermediate",
        "cyp_variant": "CYP2C9 intermediate metabolizer",
        "cyp2d6": "poor",
        "cyp2d6_variant": "CYP2D6 poor metabolizer",
        "co_med": "none",
        "current_drug": "vpa",
        "current_dose_mg": 1000,
        "months_on_therapy": 9,
        "liver_function": "mildly_elevated",
        "alt_u_l": 42,
        "target_protein": "Nav1.2",
        "seizure_control": "partial",
        "breakthrough_per_month": 1.5,
        "weight_change_kg": 7.2,
        "notes": "PCOS detected at month 6 on Valproic Acid. Weight gain +7.2kg over 9 months. Partial seizure control with 1–2 breakthrough seizures per month. CYP2D6 Poor Metabolizer increases drug accumulation risk 3–5×.",
    },
    "treatment_resistant_depression": {
        "patient_id": "treatment_resistant_depression",
        "name": "Arjun",
        "condition": "Treatment-resistant depression",
        "sex": "male",
        "cyp_genotype": "poor",
        "cyp_variant": "CYP2C9 poor metabolizer",
        "co_med": "vpa",
        "age": 34,
        "weight_kg": 72,
        "liver_function": "mildly impaired",
        "notes": "History of partial response to SSRIs and poor tolerability to benzodiazepines.",
    },
    "anxiety_plus_depression": {
        "patient_id": "anxiety_plus_depression",
        "name": "Maya",
        "condition": "Anxiety with secondary depression",
        "sex": "female",
        "cyp_genotype": "normal",
        "cyp_variant": "CYP2C9 normal metabolizer",
        "co_med": "none",
        "age": 28,
        "weight_kg": 61,
        "liver_function": "normal",
        "notes": "Elevated social anxiety, insomnia, and low mood after failed first-line SSRI treatment.",
    },
}


def get_quantamed_candidates() -> list[dict[str, Any]]:
    """Return all candidate drug metadata for the QuantaMed demo."""
    return list(_CANDIDATE_DRUGS.values())


def get_quantamed_patient_profiles() -> list[dict[str, Any]]:
    """Return patient profiles used by the QuantaMed demo."""
    return list(_PATIENT_PROFILES.values())


def _lipinski_violation_count(drug_data: dict[str, Any]) -> int:
    lip = drug_data.get("lipinski", {})
    violations = 0
    if lip.get("mw", 0) > 500:
        violations += 1
    if lip.get("logp", 0) > 5:
        violations += 1
    if lip.get("hbd", 0) > 5:
        violations += 1
    if lip.get("hba", 0) > 10:
        violations += 1
    return violations


def compute_manufacturability_score(drug_id: str) -> dict[str, Any]:
    """Compute a simulated manufacturability score."""
    drug = _CANDIDATE_DRUGS.get(drug_id)
    if drug is None:
        raise ValueError(f"Unsupported drug_id '{drug_id}'")
    lip = drug["lipinski"]
    violations = _lipinski_violation_count(drug)
    score = max(0, min(100, drug["manufacturability"] - violations * 8))
    return {
        "drug_id": drug_id,
        "label": drug["label"],
        "lipinski": lip,
        "violations": violations,
        "manufacturability_score": score,
    }


def _off_target_penalty(drug_id: str, patient_profile: dict[str, Any]) -> tuple[float, list[dict[str, Any]]]:
    """Compute off-target binding penalty with sex-specific risk modifiers.

    Key modifiers:
    - Androgen receptor binding for female patients under 30 → 2.8× PCOS risk multiplier
    - Treatment-resistant conditions → 1.2× modifier on androgen receptor sensitivity
    - Histamine H1 binding for any patient → weight gain signal
    """
    drug = _CANDIDATE_DRUGS.get(drug_id)
    if drug is None:
        raise ValueError(f"Unsupported drug_id '{drug_id}'")
    off_target = drug["off_target_profile"]
    entries = []
    penalty = 0.0

    patient_sex = patient_profile.get("sex", "unknown").lower()
    patient_age = patient_profile.get("age", 50)
    patient_condition = patient_profile.get("condition", "").lower()

    for protein, value in off_target.items():
        factor = 1.0
        risk_notes = []

        # Sex-specific PCOS risk: female patients under 30 on VPA with AR binding
        if protein == "Androgen receptor":
            if patient_sex == "female" and patient_age < 30:
                factor = 2.8  # 2.8× elevated PCOS risk (Mikkonen et al., 2004)
                risk_notes.append("PCOS risk 2.8× elevated for female patients under 30")
            if patient_condition.startswith("treatment-resistant"):
                factor *= 1.2
                risk_notes.append("Treatment-resistant condition amplifies AR sensitivity")

        # Histamine H1 → weight gain signal, amplified if patient already has weight gain
        if protein == "Histamine H1":
            weight_change = patient_profile.get("weight_change_kg", 0)
            if weight_change > 5:
                factor = 1.5
                risk_notes.append(f"Existing weight gain (+{weight_change}kg) amplifies H1 risk")

        score = round(100 - value * 80, 1)
        entries.append({
            "protein": protein,
            "risk_score": score,
            "raw_binding": value,
            "sex_factor": factor,
            "risk_notes": risk_notes,
        })
        penalty += value * 15 * factor

    penalty = min(100.0, penalty)
    return penalty, entries


def simulate_tribe_response(drug_id: str, patient_id: str) -> dict[str, Any]:
    """Simulate a brain slice or holistic patient response based on the patient/drug match."""
    drug = _CANDIDATE_DRUGS.get(drug_id)
    patient = _PATIENT_PROFILES.get(patient_id)
    if drug is None or patient is None:
        raise ValueError("Unsupported drug_id or patient_id")
    if drug_id == "ltg":
        return {
            "patient": patient["name"],
            "drug": drug["label"],
            "predicted_state": "Reward pathway stabilized, anxiety downshifted",
            "visual_sim": "calm sensory coherence",
            "tribe_input": "Nature sounds 8Hz · Harmonic rhythm · Low-intensity coherent waves",
            "brain_state": "Fully Integrated — Metabolically & Hormonally Stable",
            "confidence": "high",
        }
    if drug_id == "vpa":
        return {
            "patient": patient["name"],
            "drug": drug["label"],
            "predicted_state": "Mood rhythm stabilized with mild metabolic vigilance",
            "visual_sim": "moderate stabilizing stimulus",
            "tribe_input": "Discordant 40Hz stimuli · Chaotic rhythm · High-intensity visual noise",
            "brain_state": "Reward Pathway Dysregulated — Hormonal Stress Active",
            "confidence": "medium",
        }
    return {
        "patient": patient["name"],
        "drug": drug["label"],
        "predicted_state": "Stable cognitive integration with low off-target stress",
        "visual_sim": "balanced sensory profile",
        "tribe_input": "Mixed frequency stimuli · Moderate rhythm",
        "brain_state": "Moderate Integration — Some Off-Target Activity",
        "confidence": "medium",
    }


def _get_cyp_genotype(patient: dict[str, Any]) -> str:
    """Extract the CYP2C9 phenotype string from a patient profile.

    Handles both old format (cyp_variant: "CYP2C9 poor metabolizer")
    and new format (cyp_genotype: "intermediate").
    """
    # Try cyp_genotype first (direct phenotype label)
    genotype = (patient.get("cyp_genotype") or "").strip().lower()
    if genotype in {"poor", "pm", "poor_metabolizer"}:
        return "poor"
    if genotype in {"im", "inter", "intermediate", "intermediate_metabolizer"}:
        return "intermediate"
    if genotype in {"normal", "nm", "em", "extensive", "normal_metabolizer"}:
        return "normal"

    # Fallback: parse cyp_variant string
    variant = (patient.get("cyp_variant") or "").strip().lower()
    if "poor" in variant:
        return "poor"
    if "intermediate" in variant or "inter" in variant:
        return "intermediate"

    return "normal"


def score_quantamed_candidate(drug_id: str, patient_id: str) -> dict[str, Any]:
    """Score a candidate drug for a specific patient ID, considering all relevant parameters."""
    drug = _CANDIDATE_DRUGS.get(drug_id)
    patient = _PATIENT_PROFILES.get(patient_id)
    if drug is None or patient is None:
        raise ValueError("Unsupported drug_id or patient_id")

    penalty, off_target_details = _off_target_penalty(drug_id, patient)
    manufacturability = compute_manufacturability_score(drug_id)["manufacturability_score"]

    # Determine CYP phenotype using the unified helper
    cyp_phenotype = _get_cyp_genotype(patient)

    # Exposure modifier: CYP2C9 status affects VPA specifically
    exposure_modifier = 1.0
    if cyp_phenotype == "poor" and drug_id == "vpa":
        exposure_modifier = 1.35  # Poor metabolizer → 35% higher exposure
    elif cyp_phenotype == "intermediate" and drug_id == "vpa":
        exposure_modifier = 1.25  # Intermediate metabolizer → 25% higher exposure (Gabi)

    efficacy = max(0, min(100, drug["quantum_binding_score"] + (10 if drug["bbb_penetration_pct"] > 80 else 0)))

    # Safety: apply off-target penalty AND exposure modifier
    adjusted_safety = max(0, min(100, drug["base_safety"] - penalty * 0.6 - (exposure_modifier - 1.0) * 30))

    composite = round(
        (efficacy * 0.25 + adjusted_safety * 0.25 + manufacturability * 0.2 + drug["bbb_penetration_pct"] * 0.15 + (100 - penalty) * 0.15) / 100,
        4,
    )

    return {
        "drug_id": drug_id,
        "patient_id": patient_id,
        "scores": {
            "efficacy": round(efficacy, 1),
            "safety": round(adjusted_safety, 1),
            "manufacturability": manufacturability,
            "bbb": drug["bbb_penetration_pct"],
            "off_target_penalty": round(penalty, 1),
            "exposure_modifier": exposure_modifier,
            "composite": composite,
        },
        "details": {
            "quantum_energy_ev": drug["quantum_energy_ev"],
            "binding_score": drug["quantum_binding_score"],
            "cyp_phenotype_used": cyp_phenotype,
            "tribe_prediction": simulate_tribe_response(drug_id, patient_id),
            "off_target_details": off_target_details,
        },
    }


def recommend_quantamed_candidates(patient_id: str) -> dict[str, Any]:
    """Iterate over candidates and rank them by composite score for a given patient."""
    patient = _PATIENT_PROFILES.get(patient_id)
    if patient is None:
        raise ValueError(f"Unsupported patient_id '{patient_id}'")
    ranked = []
    for drug_id, drug_data in _CANDIDATE_DRUGS.items():
        score = score_quantamed_candidate(drug_id, patient_id)
        ranked.append({
            "drug_id": drug_id,
            "label": drug_data["label"],
            "composite_score": score["scores"]["composite"],
            "summary": drug_data["summary"],
            "scores": score["scores"],
        })
    ranked.sort(key=lambda x: x["composite_score"], reverse=True)
    return {
        "patient_id": patient_id,
        "patient_name": patient["name"],
        "condition": patient["condition"],
        "recommendations": ranked,
    }


def get_quantamed_drug_summary(drug_id: str, patient_id: str) -> dict[str, Any]:
    """Get the scored evaluation representation of a single drug candidate."""
    return score_quantamed_candidate(drug_id, patient_id)


def get_quantamed_patient_summary(patient_id: str) -> dict[str, Any]:
    """Retrieve detailed metadata about a given patient's profile."""
    patient = _PATIENT_PROFILES.get(patient_id)
    if patient is None:
        raise ValueError(f"Unsupported patient_id '{patient_id}'")
    return patient


# ---------------------------------------------------------------------------
# Protein folding — toy quantum simulation with Qiskit VQE (or cached fallback)
# ---------------------------------------------------------------------------

def _get_protein_folding_config() -> dict[str, Any]:
    return {
        "00": {
            "label": "Unfolded chain",
            "energy": 6.0,
            "points": [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],
            "description": "Extended unfolded peptide",
        },
        "01": {
            "label": "Partial fold",
            "energy": 3.9,
            "points": [(0, 0), (1, 0), (2, -1), (3, -1), (4, -1)],
            "description": "Beginning to collapse into a helix-like motif",
        },
        "10": {
            "label": "Misfolded state",
            "energy": 4.8,
            "points": [(0, 0), (1, 0), (2, -1), (2, -2), (3, -2)],
            "description": "Non-native packing with higher strain",
        },
        "11": {
            "label": "Stable folded state",
            "energy": 1.0,
            "points": [(0, 0), (1, 0), (1, -1), (2, -1), (2, -2)],
            "description": "Compact low-energy protein folding topology",
        },
    }


def _interpolate_frames(start_points: list[tuple[float | int, float | int]], end_points: list[tuple[float | int, float | int]], steps: int = 20) -> list[list[tuple[float, float]]]:
    frames: list[list[tuple[float, float]]] = []
    for step in range(steps + 1):
        t = step / steps
        frames.append([
            (sx + (ex - sx) * t, sy + (ey - sy) * t)
            for (sx, sy), (ex, ey) in zip(start_points, end_points)
        ])
    return frames


def _cached_protein_folding_result() -> dict[str, Any]:
    """Pre-computed fallback result when Qiskit is unavailable."""
    configs = _get_protein_folding_config()
    best_key = "11"  # Stable folded state has minimum energy
    final_config = configs[best_key]
    initial = configs["00"]["points"]
    target = final_config["points"]
    frames = _interpolate_frames(initial, target, steps=24)

    return {
        "model": "toy_quantum_protein_folding",
        "case": "default",
        "energy_ev": 1.0,
        "bitstring": best_key,
        "probabilities": {"00": 0.0312, "01": 0.0871, "10": 0.0405, "11": 0.8412},
        "final_state": {
            "label": final_config["label"],
            "description": final_config["description"],
            "energy": final_config["energy"],
        },
        "frames": [
            [{"x": round(x, 3), "y": round(y, 3)} for x, y in frame]
            for frame in frames
        ],
        "backend": "cached_fallback",
        "note": "Qiskit unavailable — using pre-computed VQE result.",
    }


def quantum_protein_folding_payload(case: str = "default") -> dict[str, Any]:
    """Run quantum folding simulation utilizing a toy Qiskit pipeline."""
    # pylint: disable=too-many-locals
    configs = _get_protein_folding_config()
    if case != "default":
        raise ValueError("Unsupported protein folding case")

    if not _QISKIT_AVAILABLE:
        return _cached_protein_folding_result()

    try:
        hamiltonian_matrix = np.diag([configs[key]["energy"] for key in ["00", "01", "10", "11"]])
        sparse_pauli = SparsePauliOp.from_operator(Operator(hamiltonian_matrix))
        hamiltonian = PauliSumOp(sparse_pauli)

        ansatz = TwoLocal(num_qubits=2, rotation_blocks=["ry", "rz"], entanglement_blocks="cz", reps=3)
        optimizer = COBYLA(maxiter=150)
        backend = BasicAer.get_backend("statevector_simulator")
        qinstance = QuantumInstance(backend)
        vqe = VQE(ansatz=ansatz, optimizer=optimizer, quantum_instance=qinstance)
        result = vqe.compute_minimum_eigenvalue(operator=hamiltonian)

        state = Statevector.from_instruction(ansatz.bind_parameters(result.optimal_parameters))
        probabilities = state.probabilities_dict()
        best_key = max(probabilities, key=probabilities.get)
        final_config = configs.get(best_key, configs["11"])

        initial = configs["00"]["points"]
        target = final_config["points"]
        frames = _interpolate_frames(initial, target, steps=24)

        return {
            "model": "toy_quantum_protein_folding",
            "case": case,
            "energy_ev": float(result.eigenvalue.real),
            "bitstring": best_key,
            "probabilities": {k: round(float(v), 4) for k, v in probabilities.items()},
            "final_state": {
                "label": final_config["label"],
                "description": final_config["description"],
                "energy": final_config["energy"],
            },
            "frames": [
                [{"x": round(x, 3), "y": round(y, 3)} for x, y in frame]
                for frame in frames
            ],
            "backend": "qiskit_aer_statevector",
        }
    except Exception:  # pylint: disable=broad-exception-caught
        # Any Qiskit runtime error → graceful fallback to cached result
        return _cached_protein_folding_result()


def vqe_demo_payload() -> dict[str, Any]:
    """Deterministic VQE-like convergence curves for demo charts.

    This keeps the UI stable/reproducible and can be swapped later with
    real Qiskit Aer output (same shape: iters + datasets).
    """
    iters = list(range(1, 148))

    def vqe_curve(seed: float, final_e: float) -> list[float]:
        out = []
        for i in iters:
            decay = math.exp(-i / 35.0)
            noise = (math.sin(i * seed + 1.0) * 0.4 + math.cos(i * 0.7) * 0.2) * decay
            out.append(final_e + (3.5 - final_e) * math.exp(-i / 40.0) + noise)
        return [round(x, 5) for x in out]

    return {
        "iters": iters,
        "datasets": [
            {
                "key": "ltg",
                "label": "Lamotrigine (LTG)",
                "color": "#00e676",
                "borderWidth": 2,
                "data": vqe_curve(1.3, -2.84),
            },
            {
                "key": "vpa",
                "label": "Valproic Acid (VPA)",
                "color": "#ffab40",
                "borderWidth": 2,
                "data": vqe_curve(2.1, -2.71),
            },
            {
                "key": "tpm",
                "label": "Topiramate (TPM)",
                "color": "#b388ff",
                "borderWidth": 1.5,
                "data": vqe_curve(0.9, -2.44),
            },
            {
                "key": "lev",
                "label": "Levetiracetam (LEV)",
                "color": "#00d4ff",
                "borderWidth": 1.5,
                "data": vqe_curve(1.7, -2.21),
            },
            {
                "key": "zns",
                "label": "Zonisamide (ZNS)",
                "color": "#ff5252",
                "borderWidth": 1.5,
                "data": vqe_curve(0.6, -2.05),
            },
        ],
        "meta": {
            "backend": "demo_fixture",
            "note": "Swap server.quantamed_sim.vqe_demo_payload with real Qiskit Aer output when ready.",
        },
    }
