"""
Patient Aggregate Root - Core Domain Entity
Represents a patient with complete medical profile and business logic
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import uuid
import re


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Severity(Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class MetabolizerStatus(Enum):
    POOR = "poor"
    INTERMEDIATE = "intermediate"
    NORMAL = "normal"
    RAPID = "rapid"
    ULTRARAPID = "ultrarapid"


@dataclass(frozen=True)
class BasicInfo:
    """Value Object - Immutable patient demographics"""
    age: int
    gender: Gender
    weight_kg: float
    height_cm: float
    bmi: float
    ethnicity: str
    
    def __post_init__(self):
        if self.age < 0 or self.age > 120:
            raise ValueError(f"Invalid age: {self.age}")
        if self.weight_kg <= 0 or self.weight_kg > 500:
            raise ValueError(f"Invalid weight: {self.weight_kg}")
        if self.height_cm <= 0 or self.height_cm > 300:
            raise ValueError(f"Invalid height: {self.height_cm}")


@dataclass(frozen=True)
class Condition:
    """Value Object - Medical condition details"""
    primary_diagnosis: str
    subtype: Optional[str]
    severity: Severity
    duration_years: float
    comorbidities: List[str]
    icd10_codes: List[str]


@dataclass(frozen=True)
class GeneticProfile:
    """Value Object - Pharmacogenetic markers"""
    cyp2d6: MetabolizerStatus
    cyp2c9: MetabolizerStatus
    cyp2c19: MetabolizerStatus
    cyp3a4: MetabolizerStatus
    cyp1a2: MetabolizerStatus
    slco1b1: Optional[str] = None
    vkorc1: Optional[str] = None
    hla_b5701: Optional[bool] = None
    
    def is_poor_metabolizer(self, enzyme: str) -> bool:
        """Check if patient is poor metabolizer for specific enzyme"""
        status = getattr(self, enzyme.lower(), None)
        return status == MetabolizerStatus.POOR if status else False


@dataclass(frozen=True)
class LabResults:
    """Value Object - Laboratory test results"""
    alt_u_l: float
    ast_u_l: float
    bilirubin_mg_dl: float
    albumin_g_dl: float
    egfr_ml_min: float
    creatinine_mg_dl: float
    glucose_mg_dl: float
    hba1c_percent: Optional[float] = None
    ldl_mg_dl: Optional[float] = None
    hdl_mg_dl: Optional[float] = None
    triglycerides_mg_dl: Optional[float] = None
    test_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def has_hepatic_impairment(self) -> bool:
        """Check for liver dysfunction"""
        return self.alt_u_l > 120 or self.ast_u_l > 120 or self.bilirubin_mg_dl > 2.0
    
    def has_renal_impairment(self) -> bool:
        """Check for kidney dysfunction"""
        return self.egfr_ml_min < 60 or self.creatinine_mg_dl > 1.5


@dataclass(frozen=True)
class Medication:
    """Value Object - Single medication entry"""
    name: str
    dose_mg: float
    frequency: str
    route: str
    start_date: str
    indication: str
    active: bool = True


@dataclass
class MedicationHistory:
    """Value Object - Complete medication profile"""
    current_medications: List[Medication]
    past_medications: List[Medication]
    allergies: List[str]
    adverse_reactions: List[Dict[str, str]]
    
    def has_drug_interaction_risk(self, new_drug: str) -> bool:
        """Check for potential drug interactions"""
        # Simplified - would use drug interaction database in production
        high_risk_combinations = {
            "warfarin": ["aspirin", "nsaids", "ssri"],
            "metformin": ["contrast_dye"],
            "statins": ["fibrates", "azole_antifungals"]
        }
        
        current_drug_names = [med.name.lower() for med in self.current_medications]
        new_drug_lower = new_drug.lower()
        
        for drug, interactions in high_risk_combinations.items():
            if drug in new_drug_lower:
                return any(interaction in " ".join(current_drug_names) for interaction in interactions)
        
        return False
    
    def is_allergic_to(self, drug: str) -> bool:
        """Check if patient has allergy to drug"""
        return any(drug.lower() in allergy.lower() for allergy in self.allergies)


def _extract_phenotype(genetics_string: str) -> str:
    """
    Extract metabolizer phenotype from genetics string like '*1/*4 (Intermediate Metabolizer)'
    Returns: 'poor', 'intermediate', 'normal', 'rapid', or 'ultrarapid'
    """
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
    
    # Default to normal if can't parse
    return "normal"


def _normalize_flat_schema(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert flat patient JSON schema to nested schema expected by Patient.create_new()
    Handles uploaded JSON files with structure: {age, sex, conditions[], currentMedications[], etc.}
    """
    normalized = {}
    
    # Extract patient name
    normalized["name"] = patient_data.get("name", patient_data.get("patientId", "Unknown Patient"))
    
    # Basic info normalization
    age = patient_data.get("age", 0)
    sex = patient_data.get("sex", patient_data.get("gender", "other"))
    # Normalize gender: M->male, F->female
    if sex.upper() == "M":
        sex = "male"
    elif sex.upper() == "F":
        sex = "female"
    else:
        sex = sex.lower()
    
    weight = patient_data.get("weight", patient_data.get("weight_kg", 70.0))
    height = patient_data.get("height", patient_data.get("height_cm", 170.0))
    bmi = patient_data.get("bmi")
    if bmi is None and weight and height:
        bmi = round(weight / ((height / 100) ** 2), 1)
    
    normalized["basic_info"] = {
        "age": age,
        "gender": sex,
        "weight_kg": weight,
        "height_cm": height,
        "bmi": bmi or 22.0,
        "ethnicity": patient_data.get("ethnicity", "unknown"),
    }
    
    # Condition normalization
    conditions_list = patient_data.get("conditions", [])
    if not conditions_list and patient_data.get("condition"):
        conditions_list = [patient_data["condition"]]
    
    if conditions_list:
        primary_condition = conditions_list[0]
        primary_diagnosis = primary_condition.get("name",
                                                  primary_condition.get("primary_diagnosis",
                                                                       patient_data.get("primary_diagnosis", "Unknown")))
        
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
                    severity = "critical"
        
        # Ensure severity is valid
        if severity.lower() not in ["mild", "moderate", "severe", "critical"]:
            severity = "moderate"
        
        # Extract comorbidities from remaining conditions
        comorbidities = [c.get("name", "") for c in conditions_list[1:] if c.get("name")]
        
        # Extract ICD-10 codes
        icd10_codes = [c.get("icd10", "") for c in conditions_list if c.get("icd10")]
        
        normalized["condition"] = {
            "primary_diagnosis": primary_diagnosis,
            "subtype": primary_condition.get("subtype", primary_condition.get("stage")),
            "severity": severity.lower(),
            "duration_years": primary_condition.get("duration_years", 0.5),
            "comorbidities": comorbidities,
            "icd10_codes": icd10_codes,
        }
    else:
        # Default condition if none provided
        normalized["condition"] = {
            "primary_diagnosis": "Unknown",
            "subtype": None,
            "severity": "moderate",
            "duration_years": 0.0,
            "comorbidities": [],
            "icd10_codes": [],
        }
    
    # Genetics normalization
    genetics_raw = patient_data.get("genetics", {})
    normalized["genetics"] = {
        "cyp2d6": _extract_phenotype(genetics_raw.get("CYP2D6", genetics_raw.get("cyp2d6", "normal"))),
        "cyp2c9": _extract_phenotype(genetics_raw.get("CYP2C9", genetics_raw.get("cyp2c9", "normal"))),
        "cyp2c19": _extract_phenotype(genetics_raw.get("CYP2C19", genetics_raw.get("cyp2c19", "normal"))),
        "cyp3a4": _extract_phenotype(genetics_raw.get("CYP3A4", genetics_raw.get("cyp3a4", "normal"))),
        "cyp1a2": _extract_phenotype(genetics_raw.get("CYP1A2", genetics_raw.get("cyp1a2", "normal"))),
    }
    
    # Labs normalization
    lab_results = patient_data.get("labResults", {})
    liver_function = lab_results.get("liverFunction", {})
    metabolic_panel = lab_results.get("metabolicPanel", {})
    
    normalized["labs"] = {
        "alt_u_l": liver_function.get("ALT", liver_function.get("alt", 25.0)),
        "ast_u_l": liver_function.get("AST", liver_function.get("ast", 25.0)),
        "bilirubin_mg_dl": liver_function.get("totalBilirubin", liver_function.get("bilirubin", 0.8)),
        "albumin_g_dl": liver_function.get("albumin", 4.0),
        "egfr_ml_min": metabolic_panel.get("eGFR", metabolic_panel.get("egfr", 90.0)),
        "creatinine_mg_dl": metabolic_panel.get("creatinine", 0.9),
        "glucose_mg_dl": metabolic_panel.get("glucose", 95.0),
    }
    
    # Medications normalization
    current_meds = patient_data.get("currentMedications", [])
    normalized_current = []
    for med in current_meds:
        # Extract dose as number (remove 'mg' suffix if present)
        dose_str = str(med.get("dose", med.get("dose_mg", "100mg")))
        dose_match = re.search(r'(\d+(?:\.\d+)?)', dose_str)
        dose_mg = float(dose_match.group(1)) if dose_match else 100.0
        
        normalized_current.append({
            "name": med.get("name", ""),
            "dose_mg": dose_mg,
            "frequency": med.get("frequency", "daily"),
            "route": med.get("route", "oral"),
            "start_date": med.get("start_date", "2024-01-01"),
            "indication": med.get("indication", ""),
            "active": True
        })
    
    # Handle allergies - can be list of strings or list of dicts
    allergies_raw = patient_data.get("allergies", [])
    allergies = []
    for allergy in allergies_raw:
        if isinstance(allergy, dict):
            allergies.append(allergy.get("allergen", str(allergy)))
        else:
            allergies.append(str(allergy))
    
    normalized["medications"] = {
        "current": normalized_current,
        "past": [],
        "allergies": allergies,
        "adverse_reactions": [],
    }
    
    # Lifestyle normalization
    normalized["lifestyle"] = patient_data.get("socialHistory", patient_data.get("lifestyle", {}))
    
    return normalized


@dataclass
class Patient:
    """
    Patient Aggregate Root
    Encapsulates all patient data and business rules
    """
    session_id: str
    basic_info: BasicInfo
    condition: Condition
    genetics: GeneticProfile
    labs: LabResults
    medications: MedicationHistory
    lifestyle: Dict[str, Any]
    name: str = ""  # Patient name extracted from uploaded data
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @staticmethod
    def create_new(patient_data: Dict[str, Any]) -> 'Patient':
        """
        Factory method to create new patient from raw data
        Supports both nested schema (from wizard) and flat schema (from uploaded JSON)
        """
        session_id = str(uuid.uuid4())
        
        # STEP 1: Detect schema format and normalize if needed
        if patient_data.get("basic_info") is None:
            # Flat schema detected - normalize it to nested format
            patient_data = _normalize_flat_schema(patient_data)
        
        # Extract patient name (works for both schemas now)
        patient_name = patient_data.get("name", "Unknown Patient")
        
        # STEP 2: Parse basic info (now guaranteed to be nested)
        basic_data = patient_data.get("basic_info", {})
        
        # Normalize gender field (handle M/F abbreviations)
        gender_str = basic_data.get("gender", "other")
        if gender_str.upper() == "M":
            gender_str = "male"
        elif gender_str.upper() == "F":
            gender_str = "female"
        else:
            gender_str = gender_str.lower()
        
        basic_info = BasicInfo(
            age=basic_data.get("age", 0),
            gender=Gender(gender_str),
            weight_kg=basic_data.get("weight_kg", 70.0),
            height_cm=basic_data.get("height_cm", 170.0),
            bmi=basic_data.get("bmi", 22.0),
            ethnicity=basic_data.get("ethnicity", "unknown")
        )
        
        # STEP 3: Parse condition
        condition_data = patient_data.get("condition", {})
        
        # Convert duration_months to duration_years if needed
        if "duration_months" in condition_data and "duration_years" not in condition_data:
            duration_years = condition_data["duration_months"] / 12.0
        else:
            duration_years = condition_data.get("duration_years", 0.0)
        
        # Normalize severity (already handled in _normalize_flat_schema, but double-check)
        severity_str = condition_data.get("severity", "moderate").lower()
        if severity_str not in ["mild", "moderate", "severe", "critical"]:
            severity_str = "moderate"
        
        condition = Condition(
            primary_diagnosis=condition_data.get("primary_diagnosis", "Unknown"),
            subtype=condition_data.get("subtype"),
            severity=Severity(severity_str),
            duration_years=duration_years,
            comorbidities=condition_data.get("comorbidities", []),
            icd10_codes=condition_data.get("icd10_codes", [])
        )
        
        # STEP 4: Parse genetics - normalize keys to lowercase
        genetics_data_raw = patient_data.get("genetics", {})
        genetics_data = {}
        for key, value in genetics_data_raw.items():
            genetics_data[key.lower()] = value
        
        def _to_metabolizer_status(value: str) -> MetabolizerStatus:
            """Safely convert a string to MetabolizerStatus, normalizing case."""
            normalized = (value or "normal").strip().lower()
            alias_map = {
                "pm": "poor", "poor_metabolizer": "poor",
                "im": "intermediate", "intermediate_metabolizer": "intermediate",
                "nm": "normal", "em": "normal", "extensive": "normal", "normal_metabolizer": "normal",
                "um": "ultrarapid", "ultrarapid_metabolizer": "ultrarapid",
                "rm": "rapid", "rapid_metabolizer": "rapid",
            }
            normalized = alias_map.get(normalized, normalized)
            try:
                return MetabolizerStatus(normalized)
            except ValueError:
                return MetabolizerStatus.NORMAL

        genetics = GeneticProfile(
            cyp2d6=_to_metabolizer_status(genetics_data.get("cyp2d6", "normal")),
            cyp2c9=_to_metabolizer_status(genetics_data.get("cyp2c9", "normal")),
            cyp2c19=_to_metabolizer_status(genetics_data.get("cyp2c19", "normal")),
            cyp3a4=_to_metabolizer_status(genetics_data.get("cyp3a4", "normal")),
            cyp1a2=_to_metabolizer_status(genetics_data.get("cyp1a2", "normal")),
            slco1b1=genetics_data.get("slco1b1"),
            vkorc1=genetics_data.get("vkorc1"),
            hla_b5701=genetics_data.get("hla_b5701")
        )
        
        # STEP 5: Parse labs
        labs_data = patient_data.get("labs", {})
        labs = LabResults(
            alt_u_l=labs_data.get("alt_u_l", 25.0),
            ast_u_l=labs_data.get("ast_u_l", 25.0),
            bilirubin_mg_dl=labs_data.get("bilirubin_mg_dl", 0.8),
            albumin_g_dl=labs_data.get("albumin_g_dl", 4.0),
            egfr_ml_min=labs_data.get("egfr_ml_min", 90.0),
            creatinine_mg_dl=labs_data.get("creatinine_mg_dl", 0.9),
            glucose_mg_dl=labs_data.get("glucose_mg_dl", 95.0),
            hba1c_percent=labs_data.get("hba1c_percent"),
            ldl_mg_dl=labs_data.get("ldl_mg_dl"),
            hdl_mg_dl=labs_data.get("hdl_mg_dl"),
            triglycerides_mg_dl=labs_data.get("triglycerides_mg_dl"),
            test_date=labs_data.get("test_date", datetime.now().isoformat())
        )
        
        # STEP 6: Parse medications
        meds_data = patient_data.get("medications", {})
        current_meds = [
            Medication(
                name=med.get("name", ""),
                dose_mg=med.get("dose_mg", 100.0),
                frequency=med.get("frequency", "daily"),
                route=med.get("route", "oral"),
                start_date=med.get("start_date", "2024-01-01"),
                indication=med.get("indication", ""),
                active=med.get("active", True)
            )
            for med in meds_data.get("current", [])
        ]
        
        past_meds = [
            Medication(
                name=med.get("name", ""),
                dose_mg=med.get("dose_mg", 100.0),
                frequency=med.get("frequency", "daily"),
                route=med.get("route", "oral"),
                start_date=med.get("start_date", "2024-01-01"),
                indication=med.get("indication", ""),
                active=False
            )
            for med in meds_data.get("past", [])
        ]
        
        medications = MedicationHistory(
            current_medications=current_meds,
            past_medications=past_meds,
            allergies=meds_data.get("allergies", []),
            adverse_reactions=meds_data.get("adverse_reactions", [])
        )
        
        # STEP 7: Parse lifestyle
        lifestyle = patient_data.get("lifestyle", {})
        
        # STEP 8: Create and return Patient with name field populated
        return Patient(
            session_id=session_id,
            basic_info=basic_info,
            condition=condition,
            genetics=genetics,
            labs=labs,
            medications=medications,
            lifestyle=lifestyle,
            name=patient_name
        )
    
    def can_take_drug(self, drug_name: str) -> tuple[bool, List[str]]:
        """
        Business Rule: Determine if patient can safely take a drug
        Returns: (can_take, reasons)
        """
        reasons = []
        
        # Check allergies
        if self.medications.is_allergic_to(drug_name):
            reasons.append(f"Patient is allergic to {drug_name}")
            return False, reasons
        
        # Check drug interactions
        if self.medications.has_drug_interaction_risk(drug_name):
            reasons.append(f"Potential drug interaction with current medications")
        
        # Check hepatic function
        if self.labs.has_hepatic_impairment():
            reasons.append("Hepatic impairment detected - dose adjustment may be needed")
        
        # Check renal function
        if self.labs.has_renal_impairment():
            reasons.append("Renal impairment detected - dose adjustment may be needed")
        
        # Check genetic factors
        if "cyp2d6" in drug_name.lower() and self.genetics.is_poor_metabolizer("cyp2d6"):
            reasons.append("CYP2D6 poor metabolizer - increased risk of adverse effects")
        
        # If only warnings (not contraindications), still allow
        can_take = len(reasons) == 0 or all("may be needed" in r or "increased risk" in r for r in reasons)
        
        return can_take, reasons
    
    def get_risk_score(self) -> float:
        """
        Business Rule: Calculate overall patient risk score (0-100)
        Higher score = higher risk
        """
        risk = 0.0
        
        # Age risk
        if self.basic_info.age > 65:
            risk += 15
        elif self.basic_info.age < 18:
            risk += 10
        
        # BMI risk
        if self.basic_info.bmi > 30 or self.basic_info.bmi < 18.5:
            risk += 10
        
        # Severity risk
        severity_scores = {
            Severity.MILD: 5,
            Severity.MODERATE: 15,
            Severity.SEVERE: 25,
            Severity.CRITICAL: 40
        }
        risk += severity_scores.get(self.condition.severity, 0)
        
        # Comorbidity risk
        risk += len(self.condition.comorbidities) * 5
        
        # Organ function risk
        if self.labs.has_hepatic_impairment():
            risk += 15
        if self.labs.has_renal_impairment():
            risk += 15
        
        # Polypharmacy risk
        if len(self.medications.current_medications) > 5:
            risk += 10
        
        # Genetic risk
        poor_metabolizers = sum(1 for attr in ['cyp2d6', 'cyp2c9', 'cyp2c19', 'cyp3a4']
                               if self.genetics.is_poor_metabolizer(attr))
        risk += poor_metabolizers * 5
        
        return min(risk, 100.0)  # Cap at 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert patient to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "basic_info": {
                "age": self.basic_info.age,
                "gender": self.basic_info.gender.value,
                "weight_kg": self.basic_info.weight_kg,
                "height_cm": self.basic_info.height_cm,
                "bmi": self.basic_info.bmi,
                "ethnicity": self.basic_info.ethnicity
            },
            "condition": {
                "primary_diagnosis": self.condition.primary_diagnosis,
                "subtype": self.condition.subtype,
                "severity": self.condition.severity.value,
                "duration_years": self.condition.duration_years,
                "comorbidities": self.condition.comorbidities,
                "icd10_codes": self.condition.icd10_codes
            },
            "genetics": {
                "cyp2d6": self.genetics.cyp2d6.value,
                "cyp2c9": self.genetics.cyp2c9.value,
                "cyp2c19": self.genetics.cyp2c19.value,
                "cyp3a4": self.genetics.cyp3a4.value,
                "cyp1a2": self.genetics.cyp1a2.value,
                "slco1b1": self.genetics.slco1b1,
                "vkorc1": self.genetics.vkorc1,
                "hla_b5701": self.genetics.hla_b5701
            },
            "labs": {
                "alt_u_l": self.labs.alt_u_l,
                "ast_u_l": self.labs.ast_u_l,
                "bilirubin_mg_dl": self.labs.bilirubin_mg_dl,
                "albumin_g_dl": self.labs.albumin_g_dl,
                "egfr_ml_min": self.labs.egfr_ml_min,
                "creatinine_mg_dl": self.labs.creatinine_mg_dl,
                "glucose_mg_dl": self.labs.glucose_mg_dl,
                "hba1c_percent": self.labs.hba1c_percent,
                "ldl_mg_dl": self.labs.ldl_mg_dl,
                "hdl_mg_dl": self.labs.hdl_mg_dl,
                "triglycerides_mg_dl": self.labs.triglycerides_mg_dl,
                "test_date": self.labs.test_date
            },
            "medications": {
                "current": [
                    {
                        "name": med.name,
                        "dose_mg": med.dose_mg,
                        "frequency": med.frequency,
                        "route": med.route,
                        "start_date": med.start_date,
                        "indication": med.indication,
                        "active": med.active
                    }
                    for med in self.medications.current_medications
                ],
                "past": [
                    {
                        "name": med.name,
                        "dose_mg": med.dose_mg,
                        "frequency": med.frequency,
                        "route": med.route,
                        "start_date": med.start_date,
                        "indication": med.indication,
                        "active": med.active
                    }
                    for med in self.medications.past_medications
                ],
                "allergies": self.medications.allergies,
                "adverse_reactions": self.medications.adverse_reactions
            },
            "lifestyle": self.lifestyle,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

# Made with Bob
