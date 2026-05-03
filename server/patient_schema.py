"""
Foldables — Patient Profile Schema & Validation.

Defines the complete patient biological profile used by all scoring pipelines.
Includes real clinical thresholds (AASLD/KDIGO) for organ status classification.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import re


# ── Clinical Thresholds ────────────────────────────────────────────────

def classify_liver(alt: float | None, ast: float | None) -> str:
    """AASLD-based liver status from ALT/AST."""
    val = alt or ast or 0
    if val <= 0:
        return "unknown"
    if val <= 40:
        return "normal"
    if val <= 120:
        return "mild_impairment"
    if val <= 300:
        return "moderate_impairment"
    return "severe_impairment"


def classify_kidney(egfr: float | None) -> str:
    """KDIGO-based kidney status from eGFR."""
    if egfr is None or egfr <= 0:
        return "unknown"
    if egfr >= 90:
        return "normal"
    if egfr >= 60:
        return "mild_impairment"
    if egfr >= 30:
        return "moderate_impairment"
    return "severe_impairment"


def compute_bmi(
        weight_kg: float | None,
        height_cm: float | None) -> float | None:
    """Compute BMI from weight and height."""
    if not weight_kg or not height_cm or height_cm <= 0:
        return None
    h_m = height_cm / 100.0
    return round(weight_kg / (h_m * h_m), 1)


# ── Schema Dataclasses ─────────────────────────────────────────────────

@dataclass
class BasicInfo:
    age: int | None = None
    gender: str | None = None  # male/female/other
    weight_kg: float | None = None
    height_cm: float | None = None
    bmi: float | None = None
    ethnicity: str | None = None
    pregnancy_status: str | None = None  # not_pregnant/pregnant/unknown


@dataclass
class Condition:
    primary_diagnosis: str | None = None
    subtype: str | None = None
    severity: str | None = None  # mild/moderate/severe
    duration_months: int | None = None
    comorbidities: list[str] = field(default_factory=list)
    family_history: list[str] = field(default_factory=list)


@dataclass
class Symptoms:
    seizure_frequency_per_month: float | None = None
    anxiety_score: int | None = None  # 0-10
    depression_score: int | None = None
    sleep_disturbance_score: int | None = None
    fatigue_score: int | None = None
    cognitive_impairment_score: int | None = None


@dataclass
class Vitals:
    heart_rate: int | None = None
    blood_pressure: str | None = None  # "120/80"
    temperature: float | None = None


@dataclass
class MedEntry:
    drug_id: str = ""
    drug_name: str = ""
    dose_mg: float = 0
    frequency: str = ""  # "BID"/"TID"/"QD"
    duration_months: int = 0
    reason_stopped: str | None = None  # only for past meds


@dataclass
class Genetics:
    CYP2D6: str | None = None  # Poor/Intermediate/Normal/Ultrarapid
    CYP3A4: str | None = None
    CYP2C19: str | None = None
    CYP2C9: str | None = None
    UGT1A4: str | None = None
    HLA_variants: list[str] = field(default_factory=list)


@dataclass
class Organs:
    liver_status: str = "unknown"
    kidney_status: str = "unknown"
    heart_status: str = "unknown"


@dataclass
class Labs:
    ALT: float | None = None
    AST: float | None = None
    creatinine: float | None = None
    eGFR: float | None = None
    glucose: float | None = None


@dataclass
class Biomarkers:
    serotonin_level: str | None = None  # low/normal/high
    dopamine_level: str | None = None
    androgen_level: str | None = None


@dataclass
class TargetExpression:
    GABA_activity: str | None = None  # low/normal/high
    NMDA_activity: str | None = None


@dataclass
class DrugResponseProfile:
    antiepileptic_response: str | None = None
    ssri_response: str | None = None


@dataclass
class SideEffectEntry:
    drug_id: str = ""
    reaction: str = ""
    severity: str = ""  # mild/moderate/severe


@dataclass
class AllergyEntry:
    substance: str = ""
    reaction_type: str = ""


@dataclass
class Lifestyle:
    sleep_hours: float | None = None
    sleep_quality: str | None = None  # poor/fair/good
    stress_level: str | None = None  # low/moderate/high
    alcohol_use: str | None = None  # none/low/moderate/heavy
    smoking: bool | None = None
    exercise_frequency: int | None = None  # days per week


@dataclass
class RiskProfile:
    side_effect_tolerance: str | None = None  # low/medium/high
    urgency_level: str | None = None


@dataclass
class TreatmentGoal:
    primary_goal: str | None = None
    secondary_goal: str | None = None
    quality_of_life_priority: bool = True


# ── Full Patient Profile ──────────────────────────────────────────────

@dataclass
class PatientProfile:
    """Complete patient biological profile for Foldables scoring engine."""
    basic_info: BasicInfo = field(default_factory=BasicInfo)
    condition: Condition = field(default_factory=Condition)
    symptoms: Symptoms = field(default_factory=Symptoms)
    vitals: Vitals = field(default_factory=Vitals)
    current_meds: list[MedEntry] = field(default_factory=list)
    past_meds: list[MedEntry] = field(default_factory=list)
    genetics: Genetics = field(default_factory=Genetics)
    organs: Organs = field(default_factory=Organs)
    labs: Labs = field(default_factory=Labs)
    biomarkers: Biomarkers = field(default_factory=Biomarkers)
    target_expression: TargetExpression = field(
        default_factory=TargetExpression)
    drug_response_profile: DrugResponseProfile = field(
        default_factory=DrugResponseProfile)
    side_effect_history: list[SideEffectEntry] = field(default_factory=list)
    allergies: list[AllergyEntry] = field(default_factory=list)
    lifestyle: Lifestyle = field(default_factory=Lifestyle)
    risk_profile: RiskProfile = field(default_factory=RiskProfile)
    treatment_goal: TreatmentGoal = field(default_factory=TreatmentGoal)

    def auto_classify_organs(self) -> None:
        """Auto-classify organ status from lab values."""
        self.organs.liver_status = classify_liver(self.labs.ALT, self.labs.AST)
        self.organs.kidney_status = classify_kidney(self.labs.eGFR)
        if self.basic_info.weight_kg and self.basic_info.height_cm:
            self.basic_info.bmi = compute_bmi(
                self.basic_info.weight_kg, self.basic_info.height_cm
            )

    def completeness(self) -> dict[str, Any]:
        """Compute data completeness and confidence level."""
        total = 0
        filled = 0
        sections: dict[str, tuple[int, int]] = {}

        for section_name in [
            "basic_info", "condition", "symptoms", "genetics",
            "labs", "biomarkers", "lifestyle", "risk_profile",
        ]:
            obj = getattr(self, section_name)
            s_total = 0
            s_filled = 0
            for k, v in obj.__dict__.items():
                s_total += 1
                if v is not None and v != "" and v != [] and v != "unknown":
                    s_filled += 1
            sections[section_name] = (s_filled, s_total)
            total += s_total
            filled += s_filled

        # Current meds count
        if self.current_meds:
            filled += 1
        total += 1

        pct = round(filled / max(1, total) * 100, 1)
        if pct >= 80:
            level = "HIGH"
        elif pct >= 60:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "percentage": pct,
            "confidence_level": level,
            "filled": filled,
            "total": total,
            "sections": {k: {"filled": v[0], "total": v[1]} for k, v in sections.items()},
        }

    def clinical_alerts(self) -> list[dict[str, str]]:
        """Generate real-time clinical context alerts based on inputs."""
        alerts: list[dict[str, str]] = []

        # PCOS pre-warning
        bi = self.basic_info
        if (bi.gender == "female" and bi.age and bi.age < 35
                and any(m.drug_id == "vpa" for m in self.current_meds)):
            if (self.biomarkers.androgen_level == "high"
                    or any(m.drug_id == "vpa" for m in self.current_meds)):
                alerts.append({
                    "type": "CRITICAL",
                    "title": "PCOS Risk Pre-Warning",
                    "message": (
                        "Female patient under 35 on Valproic Acid. "
                        "VPA has documented androgen receptor binding (ChEMBL Ki=28µM). "
                        "2.8× elevated PCOS risk (Isojärvi et al. 1993)."
                    ),
                    "source": "ChEMBL + FAERS",
                })

        # Liver alert
        if self.labs.ALT and self.labs.ALT > 40:
            severity = "WARNING" if self.labs.ALT <= 120 else "CRITICAL"
            alerts.append({
                "type": severity,
                "title": f"Elevated ALT: {self.labs.ALT} U/L",
                "message": (
                    f"ALT {self.labs.ALT} U/L (normal ≤40). "
                    "Hepatic drug metabolism may be impaired. "
                    "CYP2C9/CYP2C19 substrate drugs will receive higher exposure estimates."
                ),
                "source": "AASLD Guidelines",
            })

        # CYP2D6 poor metabolizer
        if self.genetics.CYP2D6 and self.genetics.CYP2D6.lower() in ("poor", "pm"):
            alerts.append({
                "type": "WARNING",
                "title": "CYP2D6 Poor Metabolizer",
                "message": (
                    "Drug accumulation risk 3-5× for CYP2D6 substrates. "
                    "CPIC recommends dose reduction or alternative drug selection."
                ),
                "source": "CPIC Guidelines",
            })

        # Kidney impairment
        if self.labs.eGFR and self.labs.eGFR < 60:
            alerts.append({
                "type": "WARNING",
                "title": f"Reduced Renal Function: eGFR {self.labs.eGFR}",
                "message": (
                    "Renally-cleared drugs (e.g., Levetiracetam) require dose adjustment. "
                    "KDIGO Stage 3+ kidney disease."
                ),
                "source": "KDIGO Guidelines",
            })

        # Pregnancy
        if bi.pregnancy_status == "pregnant":
            alerts.append({
                "type": "CRITICAL",
                "title": "Pregnancy Detected",
                "message": (
                    "Valproic Acid is FDA Category X (teratogenic). "
                    "Topiramate is Category D. "
                    "Lamotrigine and Levetiracetam have better safety profiles."
                ),
                "source": "FDA Pregnancy Categories",
            })

        # Missing genomics
        missing_cyp = []
        for cyp in ["CYP2D6", "CYP3A4", "CYP2C19", "CYP2C9"]:
            if getattr(self.genetics, cyp) is None:
                missing_cyp.append(cyp)
        if missing_cyp:
            alerts.append({
                "type": "INFO",
                "title": "Incomplete Genomic Profile",
                "message": (
                    f"Missing: {', '.join(missing_cyp)}. "
                    "Genomic risk estimates are approximated — "
                    "add CYP status for precision scoring."
                ),
                "source": "System",
            })

        return alerts

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        d = asdict(self)
        d["_completeness"] = self.completeness()
        d["_alerts"] = self.clinical_alerts()
        return d


# ── Factory: Build from raw JSON ──────────────────────────────────────

def _extract_phenotype_status(genetics_string: str) -> str:
    """Extract metabolizer phenotype from genetics string like '*1/*4 (Intermediate Metabolizer)'"""
    if not genetics_string or not isinstance(genetics_string, str):
        return "normal"
    
    genetics_lower = genetics_string.lower()
    
    if "poor" in genetics_lower:
        return "poor"
    elif "intermediate" in genetics_lower:
        return "intermediate"
    elif "rapid" in genetics_lower and "ultra" not in genetics_lower:
        return "rapid"
    elif "ultrarapid" in genetics_lower or "ultra" in genetics_lower:
        return "ultrarapid"
    elif "normal" in genetics_lower or "wild" in genetics_lower:
        return "normal"
    
    return "normal"


def _normalize_flat_patient_schema(data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert flat patient JSON schema to nested schema expected by build_patient_from_dict()
    Handles uploaded JSON files with structure: {age, sex, conditions[], currentMedications[], etc.}
    """
    # If already nested, return as-is
    if data.get("basic_info") is not None:
        return data
    
    normalized = {}
    
    # Basic info normalization
    age = data.get("age", 0)
    sex = data.get("sex", data.get("gender", "other"))
    # Normalize gender: M->male, F->female
    if sex.upper() == "M":
        sex = "male"
    elif sex.upper() == "F":
        sex = "female"
    else:
        sex = sex.lower()
    
    weight = data.get("weight", data.get("weight_kg", 70.0))
    height = data.get("height", data.get("height_cm", 170.0))
    bmi = data.get("bmi")
    if bmi is None and weight and height:
        bmi = round(weight / ((height / 100) ** 2), 1)
    
    normalized["basic_info"] = {
        "age": age,
        "gender": sex,
        "weight_kg": weight,
        "height_cm": height,
        "bmi": bmi or 22.0,
        "ethnicity": data.get("ethnicity", "unknown"),
        "pregnancy_status": data.get("pregnancy_status", "not_pregnant"),
    }
    
    # Condition normalization
    conditions_list = data.get("conditions", [])
    if not conditions_list and data.get("condition"):
        conditions_list = [data["condition"]]
    
    if conditions_list:
        primary_condition = conditions_list[0]
        primary_diagnosis = primary_condition.get("name",
                                                  primary_condition.get("primary_diagnosis",
                                                                       data.get("primary_diagnosis", "Unknown")))
        
        # Extract severity/stage
        severity = primary_condition.get("severity", primary_condition.get("stage", "moderate"))
        
        # Normalize stage strings to severity levels
        if "stage" in severity.lower():
            stage_match = re.search(r'stage\s*([iv]+|[1-4])', severity.lower())
            if stage_match:
                stage = stage_match.group(1)
                if stage in ['i', '1']:
                    severity = "mild"
                elif stage in ['ii', '2']:
                    severity = "moderate"
                elif stage in ['iii', '3']:
                    severity = "severe"
                elif stage in ['iv', '4']:
                    severity = "severe"
        
        # Ensure severity is valid
        if severity.lower() not in ["mild", "moderate", "severe"]:
            severity = "moderate"
        
        # Extract comorbidities from remaining conditions
        comorbidities = [c.get("name", "") for c in conditions_list[1:] if c.get("name")]
        
        normalized["condition"] = {
            "primary_diagnosis": primary_diagnosis,
            "subtype": primary_condition.get("subtype", primary_condition.get("stage")),
            "severity": severity.lower(),
            "duration_months": int(primary_condition.get("duration_years", 0.5) * 12),
            "comorbidities": comorbidities,
            "family_history": [],
        }
    else:
        normalized["condition"] = {
            "primary_diagnosis": "Unknown",
            "subtype": None,
            "severity": "moderate",
            "duration_months": 0,
            "comorbidities": [],
            "family_history": [],
        }
    
    # Genetics normalization
    genetics_raw = data.get("genetics", {})
    normalized["genetics"] = {
        "CYP2D6": _extract_phenotype_status(genetics_raw.get("CYP2D6", genetics_raw.get("cyp2d6", "normal"))),
        "CYP2C9": _extract_phenotype_status(genetics_raw.get("CYP2C9", genetics_raw.get("cyp2c9", "normal"))),
        "CYP2C19": _extract_phenotype_status(genetics_raw.get("CYP2C19", genetics_raw.get("cyp2c19", "normal"))),
        "CYP3A4": _extract_phenotype_status(genetics_raw.get("CYP3A4", genetics_raw.get("cyp3a4", "normal"))),
        "CYP1A2": _extract_phenotype_status(genetics_raw.get("CYP1A2", genetics_raw.get("cyp1a2", "normal"))),
    }
    
    # Labs normalization
    lab_results = data.get("labResults", {})
    liver_function = lab_results.get("liverFunction", {})
    metabolic_panel = lab_results.get("metabolicPanel", {})
    
    normalized["labs"] = {
        "ALT": liver_function.get("ALT", liver_function.get("alt", 25.0)),
        "AST": liver_function.get("AST", liver_function.get("ast", 25.0)),
        "bilirubin": liver_function.get("totalBilirubin", liver_function.get("bilirubin", 0.8)),
        "albumin": liver_function.get("albumin", 4.0),
        "eGFR": metabolic_panel.get("eGFR", metabolic_panel.get("egfr", 90.0)),
        "creatinine": metabolic_panel.get("creatinine", 0.9),
    }
    
    # Medications normalization
    current_meds = data.get("currentMedications", [])
    normalized_current = []
    for med in current_meds:
        # Extract dose as number (remove 'mg' suffix if present)
        dose_str = str(med.get("dose", med.get("dose_mg", "100mg")))
        dose_match = re.search(r'(\d+(?:\.\d+)?)', dose_str)
        dose_mg = float(dose_match.group(1)) if dose_match else 100.0
        
        normalized_current.append({
            "drug_name": med.get("name", ""),
            "dose_mg": dose_mg,
            "frequency": med.get("frequency", "daily"),
            "duration_months": 0,
        })
    
    normalized["current_meds"] = normalized_current
    normalized["past_meds"] = []
    
    # Lifestyle normalization
    social_history = data.get("socialHistory", data.get("lifestyle", {}))
    normalized["lifestyle"] = {
        "alcohol_use": social_history.get("alcohol", "none"),
        "smoking": social_history.get("smoking") == "smoker" if isinstance(social_history.get("smoking"), str) else False,
        "exercise_frequency": 3,  # default
    }
    
    # Default empty sections
    normalized["symptoms"] = {}
    normalized["vitals"] = {}
    normalized["biomarkers"] = {}
    normalized["target_expression"] = {}
    normalized["drug_response_profile"] = {}
    normalized["side_effect_history"] = []
    normalized["allergies"] = []
    normalized["risk_profile"] = {}
    normalized["treatment_goal"] = {}
    
    return normalized


def build_patient_from_dict(data: dict[str, Any]) -> PatientProfile:
    """Build a PatientProfile from a raw JSON dict (from frontend or uploaded file)."""
    
    # STEP 1: Detect and normalize flat schema if needed
    data = _normalize_flat_patient_schema(data)
    
    p = PatientProfile()

    # Basic info
    bi = data.get("basic_info", {})
    p.basic_info = BasicInfo(
        age=bi.get("age"),
        gender=bi.get("gender"),
        weight_kg=bi.get("weight_kg"),
        height_cm=bi.get("height_cm"),
        ethnicity=bi.get("ethnicity"),
        pregnancy_status=bi.get("pregnancy_status"),
    )

    # Condition
    c = data.get("condition", {})
    p.condition = Condition(
        primary_diagnosis=c.get("primary_diagnosis"),
        subtype=c.get("subtype"),
        severity=c.get("severity"),
        duration_months=c.get("duration_months"),
        comorbidities=c.get("comorbidities", []),
        family_history=c.get("family_history", []),
    )

    # Symptoms
    s = data.get("symptoms", {})
    p.symptoms = Symptoms(
        seizure_frequency_per_month=s.get("seizure_frequency_per_month"),
        anxiety_score=s.get("anxiety_score"),
        depression_score=s.get("depression_score"),
        sleep_disturbance_score=s.get("sleep_disturbance_score"),
        fatigue_score=s.get("fatigue_score"),
        cognitive_impairment_score=s.get("cognitive_impairment_score"),
    )

    # Genetics - normalize CYP keys to uppercase
    g = data.get("genetics", {})
    g_normalized = {}
    for key, value in g.items():
        if key.lower().startswith("cyp"):
            g_normalized[key.upper()] = value
        else:
            g_normalized[key] = value
    
    p.genetics = Genetics(
        CYP2D6=g_normalized.get("CYP2D6"),
        CYP3A4=g_normalized.get("CYP3A4"),
        CYP2C19=g_normalized.get("CYP2C19"),
        CYP2C9=g_normalized.get("CYP2C9"),
        UGT1A4=g_normalized.get("UGT1A4"),
        HLA_variants=g_normalized.get("HLA_variants", []),
    )

    # Labs
    lb = data.get("labs", {})
    p.labs = Labs(
        ALT=lb.get("ALT"), AST=lb.get("AST"),
        creatinine=lb.get("creatinine"), eGFR=lb.get("eGFR"),
        glucose=lb.get("glucose"),
    )

    # Biomarkers
    bm = data.get("biomarkers", {})
    p.biomarkers = Biomarkers(
        serotonin_level=bm.get("serotonin_level"),
        dopamine_level=bm.get("dopamine_level"),
        androgen_level=bm.get("androgen_level"),
    )

    # Current meds
    for med in data.get("current_meds", []):
        p.current_meds.append(MedEntry(
            drug_id=med.get("drug_id", ""),
            drug_name=med.get("drug_name", ""),
            dose_mg=med.get("dose_mg", 0),
            frequency=med.get("frequency", ""),
            duration_months=med.get("duration_months", 0),
        ))

    # Past meds
    for med in data.get("past_meds", []):
        p.past_meds.append(MedEntry(
            drug_id=med.get("drug_id", ""),
            drug_name=med.get("drug_name", ""),
            dose_mg=med.get("dose_mg", 0),
            frequency=med.get("frequency", ""),
            duration_months=med.get("duration_months", 0),
            reason_stopped=med.get("reason_stopped"),
        ))

    # Lifestyle
    ls = data.get("lifestyle", {})
    p.lifestyle = Lifestyle(
        sleep_hours=ls.get("sleep_hours"),
        sleep_quality=ls.get("sleep_quality"),
        stress_level=ls.get("stress_level"),
        alcohol_use=ls.get("alcohol_use"),
        smoking=ls.get("smoking"),
        exercise_frequency=ls.get("exercise_frequency"),
    )

    # Risk profile
    rp = data.get("risk_profile", {})
    p.risk_profile = RiskProfile(
        side_effect_tolerance=rp.get("side_effect_tolerance"),
        urgency_level=rp.get("urgency_level"),
    )

    # Treatment goal
    tg = data.get("treatment_goal", {})
    p.treatment_goal = TreatmentGoal(
        primary_goal=tg.get("primary_goal"),
        secondary_goal=tg.get("secondary_goal"),
        quality_of_life_priority=tg.get("quality_of_life_priority", True),
    )

    # Auto-classify organs from labs
    p.auto_classify_organs()

    return p


# ── Gabi preset (demo) ────────────────────────────────────────────────

GABI_PRESET: dict[str, Any] = {
    "basic_info": {
        "age": 24, "gender": "female", "weight_kg": 58,
        "height_cm": 165, "ethnicity": "Caucasian",
        "pregnancy_status": "not_pregnant",
    },
    "condition": {
        "primary_diagnosis": "epilepsy",
        "subtype": "Juvenile Myoclonic Epilepsy",
        "severity": "moderate", "duration_months": 36,
        "comorbidities": ["PCOS"],
        "family_history": ["epilepsy"],
    },
    "symptoms": {
        "seizure_frequency_per_month": 1.5,
        "anxiety_score": 4, "depression_score": 3,
        "sleep_disturbance_score": 5, "fatigue_score": 6,
        "cognitive_impairment_score": 3,
    },
    "genetics": {
        "CYP2D6": "Poor", "CYP3A4": "Normal",
        "CYP2C19": "Normal", "CYP2C9": "Intermediate",
    },
    "labs": {
        "ALT": 42, "AST": 38, "creatinine": 0.8,
        "eGFR": 95, "glucose": 92,
    },
    "biomarkers": {"androgen_level": "high"},
    "current_meds": [{
        "drug_id": "vpa", "drug_name": "Valproic Acid",
        "dose_mg": 1000, "frequency": "BID", "duration_months": 9,
    }],
    "lifestyle": {
        "sleep_hours": 7, "sleep_quality": "fair",
        "stress_level": "moderate", "alcohol_use": "none",
        "smoking": False, "exercise_frequency": 3,
    },
    "risk_profile": {
        "side_effect_tolerance": "low", "urgency_level": "moderate",
    },
    "treatment_goal": {
        "primary_goal": "seizure_freedom",
        "secondary_goal": "minimize_side_effects",
        "quality_of_life_priority": True,
    },
}
