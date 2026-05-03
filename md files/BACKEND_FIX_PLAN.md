# QuantaMed Backend Complete Overhaul Plan

**Objective**: Fix every bug, wire every disconnected function, and make every upload and button produce real computed output with zero errors.

**Status**: 🔴 CRITICAL - Multiple import errors, missing methods, and disconnected pipelines preventing system from functioning

---

## 📋 EXECUTION CHECKLIST

### Phase 1: Critical Import & Startup Errors (BLOCKING)
- [ ] **PART 1**: Fix `service_adapters.py` module-level imports
  - Replace `from server import scoring_engine` with direct function imports
  - Replace `from server import protein_dynamics` with direct function imports  
  - Replace `from server import pdf_report` with direct function imports
  - Update all method calls to use imported functions directly

- [ ] **PART 2**: Add missing methods to `DrugAnalysisAdapter`
  - Implement `_calculate_pharmacokinetics(patient, drug_name, dose_mg)`
  - Implement `_generate_drug_recommendations(patient, warnings)`
  - Fix `_has_interaction(drug1, drug2)` with known interaction pairs

### Phase 2: Patient Upload Pipeline (CORE FLOW)
- [ ] **PART 3**: Wire upload endpoints to run full analysis
  - Modify `upload_patient_json` to call `run_full_analysis` after session creation
  - Modify `create_patient_session` to call `run_full_analysis` after session creation
  - Return analysis results in response under "analysis" key

- [ ] **PART 4**: Fix `patient_schema.py` conversion bugs
  - Normalize all CYP keys to uppercase (cyp2d6 → CYP2D6)
  - Replace all `data["key"]` with `data.get("key")` for safety
  - Replace all `data["key"]["subkey"]` with `data.get("key", {}).get("subkey")`

### Phase 3: Protein Structure & PDF Generation
- [ ] **PART 5**: Fix `protein_structure.py` example sequences
  - Change `get_example_sequences()` to return dict with "fasta", "name", "description", "length" keys
  - Add `residue_count` and `sequence_length` aliases in `model_protein_from_fasta`

- [ ] **PART 6**: Fix `pdf_report.py` missing function
  - Define `_generate_minimal_pdf(patient_id)` before `generate_quantamed_pdf`
  - Add try/except around `get_quantamed_patient_summary` for unknown patient IDs
  - Add try/except around `recommend_quantamed_candidates` for unknown patient IDs

### Phase 4: Data Layer Fixes
- [ ] **PART 7**: Add aliases to `kaggle_data.py`
  - Add `FAERS_ADVERSE_EVENTS = FAERS_SIGNALS`
  - Add `CHEMBL_BINDING = OFF_TARGET_BINDING`
  - Verify all TOX21_DATA entries have `hepatotoxicity_probability` field

- [ ] **PART 8**: Fix protein sequence mapping in `ProteinFoldingAdapter`
  - Add drug_id → target protein sequence mapping
  - Use real sequences for VPA (GABA-A), LTG (Nav1.2), LEV (SV2A), TPM (CA-II), ZNS (Nav1.2)

### Phase 5: Configuration & Domain Fixes
- [ ] **PART 9**: Fix `requirements.txt`
  - Remove any bare `-e ` lines (with nothing after them)
  - Verify `python-multipart>=0.0.9` is present
  - Verify `aiofiles>=23.0.0` is present

- [ ] **PART 10**: Fix gender enum handling in `patient_router.py`
  - Change `p.basic_info.gender.value` to `getattr(p.basic_info.gender, 'value', str(p.basic_info.gender))`
  - Fix `InMemoryPatientRepository.find_all()` to return `list(self._store.values())`

- [ ] **PART 11**: Fix `environment/actions.py` fixture loading
  - Wrap each fixture load in try/except
  - Log warning and continue instead of raising FileNotFoundError
  - Add null check in `_submit`: `if answer is None: answer = {}`

### Phase 6: Gradio & Frontend Integration
- [ ] **PART 12**: Fix `app.py` `_gr_analyze_patient` function
  - Add TARGET_SEQUENCES dict mapping drug_id to real protein sequences
  - Use correct sequence for each drug in `analyze_protein_dynamics` call
  - Fix except block to return exactly 3 values (not 2)

- [ ] **PART 13**: Fix 3D visualization in `index.html`
  - Call `initProteinFolding()` lazily when panel becomes visible
  - Add forced canvas dimension assignment before drawing
  - Fix `bakeColors()` calls to only occur inside OBJLoader callback

- [ ] **PART 14**: Implement dual-canvas molecular binding
  - Create two separate WebGLRenderer instances
  - Add independent scenes, cameras, lights for left/right canvas
  - Generate drug molecules procedurally (no external files)
  - Implement 3-phase animation (approach, binding, off-target)

### Phase 7: Verification & Testing
- [ ] **PART 15**: Run all 10 verification steps
  1. `pip install -r requirements.txt` → zero errors
  2. Import `run_full_analysis` from `scoring_engine` → OK
  3. Import all kaggle_data constants → OK
  4. Generate PDF with `generate_quantamed_pdf("test")` → valid PDF bytes
  5. Get protein examples → dict with "fasta" keys
  6. Build patient from dict with mixed CYP case → normalized
  7. Start uvicorn server → zero import errors
  8. POST patient JSON upload → response contains "analysis" with rankings
  9. GET protein examples → dict values are dicts not strings
  10. POST protein model → response contains "residue_count"

---

## 🔧 DETAILED IMPLEMENTATION GUIDE

### PART 1: service_adapters.py Import Fixes

**File**: `drug-triage-env/server/infrastructure/service_adapters.py`

**Current Code (Lines 17-20)**:
```python
from server import scoring_engine
from server import protein_dynamics
from server import pdf_report
```

**Fixed Code**:
```python
from server.scoring_engine import (
    run_full_analysis,
    pipeline_pk,
    pipeline_composite,
    pipeline_off_target,
    pipeline_admet,
    pipeline_faers
)
from server.protein_dynamics import analyze_protein_dynamics
from server.pdf_report import generate_quantamed_pdf
```

**Method Updates Required**:
- Line 68: Change `scoring_engine.run_full_analysis()` → `run_full_analysis()`
- Line 377: Change `pdf_report.generate_quantamed_pdf()` → `generate_quantamed_pdf()`
- Any calls to `protein_dynamics.analyze_protein_dynamics()` → `analyze_protein_dynamics()`

---

### PART 2: DrugAnalysisAdapter Missing Methods

**File**: `drug-triage-env/server/infrastructure/service_adapters.py`

**Add after line 158** (after existing `_has_interaction` method):

```python
def _calculate_pharmacokinetics(
    self,
    patient: Patient,
    drug_name: str,
    dose_mg: float
) -> Dict[str, Any]:
    """Calculate pharmacokinetic parameters using scoring engine"""
    from server.patient_schema import build_patient_from_dict
    
    # Map drug name to drug_id
    drug_id_map = {
        "valproic acid": "vpa",
        "lamotrigine": "ltg",
        "levetiracetam": "lev",
        "topiramate": "tpm",
        "zonisamide": "zns"
    }
    drug_id = drug_id_map.get(drug_name.lower(), drug_name.lower()[:3])
    
    # Convert domain Patient to PatientProfile
    patient_dict = {
        "basic_info": {
            "age": patient.basic_info.age,
            "gender": patient.basic_info.gender.value if hasattr(patient.basic_info.gender, 'value') else str(patient.basic_info.gender),
            "weight_kg": patient.basic_info.weight_kg,
            "height_cm": patient.basic_info.height_cm,
        },
        "genetics": {
            "CYP2D6": patient.genetics.cyp2d6.value if hasattr(patient.genetics.cyp2d6, 'value') else str(patient.genetics.cyp2d6),
            "CYP2C9": patient.genetics.cyp2c9.value if hasattr(patient.genetics.cyp2c9, 'value') else str(patient.genetics.cyp2c9),
        },
        "labs": {
            "ALT": patient.labs.alt_u_l,
            "AST": patient.labs.ast_u_l,
            "eGFR": patient.labs.egfr_ml_min,
        }
    }
    
    profile = build_patient_from_dict(patient_dict)
    pk_result = pipeline_pk(drug_id, profile)
    
    return pk_result

def _generate_drug_recommendations(
    self,
    patient: Patient,
    warnings: List[str]
) -> List[str]:
    """Generate plain-language clinical recommendations"""
    if not warnings:
        return ["No significant pharmacogenomic concerns identified for this patient."]
    
    recommendations = []
    for warning in warnings:
        if "poor metabolizer" in warning.lower():
            recommendations.append(
                "Start with 50% of standard dose due to reduced metabolic capacity. "
                "Monitor drug levels closely and titrate based on clinical response."
            )
        elif "hepatic" in warning.lower():
            recommendations.append(
                "Monitor liver enzymes (ALT/AST) weekly for first month, then monthly. "
                "Consider dose reduction if transaminases exceed 3× upper limit of normal."
            )
        elif "renal" in warning.lower():
            recommendations.append(
                "Adjust dose based on creatinine clearance using Cockcroft-Gault equation. "
                "Monitor renal function every 3-6 months."
            )
        elif "interaction" in warning.lower():
            recommendations.append(
                "Review all concomitant medications for potential drug-drug interactions. "
                "Consider therapeutic drug monitoring if multiple interacting agents present."
            )
    
    return recommendations
```

**Update existing `_has_interaction` method (line 140-158)** to use known interaction pairs:

```python
def _has_interaction(self, drug1: str, drug2: str) -> bool:
    """Check if two drugs have known major interaction"""
    # Known major interaction pairs
    known_pairs = {
        frozenset({"valproic acid", "lamotrigine"}),  # VPA inhibits LTG glucuronidation
        frozenset({"valproic acid", "carbamazepine"}),  # Mutual enzyme induction
        frozenset({"valproic acid", "aspirin"}),  # Protein binding displacement
        frozenset({"warfarin", "aspirin"}),
        frozenset({"warfarin", "nsaid"}),
        frozenset({"metformin", "contrast"}),
    }
    
    pair = frozenset({drug1.lower(), drug2.lower()})
    return pair in known_pairs
```

---

### PART 3: Patient Upload Pipeline Integration

**File**: `drug-triage-env/server/api/patient_router.py`

**Modify `upload_patient_json` endpoint (after line 87)**:

```python
result = create_patient_use_case.execute(patient_data)
logger.info(f"Created patient session from upload: {result['session_id']}")

# Run full analysis pipeline
from server.patient_schema import build_patient_from_dict
from server.scoring_engine import run_full_analysis

try:
    profile = build_patient_from_dict(patient_data)
    analysis = run_full_analysis(profile)
    result["analysis"] = analysis
    logger.info(f"Completed analysis for session {result['session_id']}")
except Exception as e:
    logger.error(f"Analysis failed: {e}")
    result["analysis"] = {"error": str(e), "rankings": []}

return result
```

**Modify `create_patient_session` endpoint (after line 67)**:

```python
result = create_patient_use_case.execute(patient_data)
logger.info(f"Created patient session: {result['session_id']}")

# Run full analysis pipeline
from server.patient_schema import build_patient_from_dict
from server.scoring_engine import run_full_analysis

try:
    profile = build_patient_from_dict(patient_data)
    analysis = run_full_analysis(profile)
    result["analysis"] = analysis
    logger.info(f"Completed analysis for session {result['session_id']}")
except Exception as e:
    logger.error(f"Analysis failed: {e}")
    result["analysis"] = {"error": str(e), "rankings": []}

return result
```

---

### PART 4: patient_schema.py Safety Fixes

**File**: `drug-triage-env/server/patient_schema.py`

**Add CYP normalization in `build_patient_from_dict` (after line 398)**:

```python
# Genetics
g = data.get("genetics", {})

# Normalize CYP keys to uppercase
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
```

**Replace all direct dict access with .get()** throughout the function:
- Line 365: `bi = data.get("basic_info", {})`
- Line 376: `c = data.get("condition", {})`
- Line 387: `s = data.get("symptoms", {})`
- Line 409: `lb = data.get("labs", {})`
- Line 417: `bm = data.get("biomarkers", {})`
- And so on for all nested accesses

---

### PART 5: protein_structure.py Format Fix

**File**: `drug-triage-env/server/protein_structure.py`

**Replace `get_example_sequences()` function (lines 909-932)**:

```python
def get_example_sequences() -> dict[str, dict[str, str]]:
    """Return available example FASTA sequences with metadata."""
    examples = {}
    
    for key, fasta_text in EXAMPLE_SEQUENCES.items():
        header, sequence = parse_fasta(fasta_text)
        examples[key] = {
            "name": _extract_protein_info(header).get("name", "Unknown Protein"),
            "fasta": fasta_text,
            "description": f"{len(sequence)}-residue fragment",
            "length": len(sequence)
        }
    
    return examples
```

**Add aliases in `model_protein_from_fasta` (before return statement, line 885)**:

```python
result_dict = result.to_dict()
result_dict['residue_count'] = result_dict.get('length', 0)
result_dict['sequence_length'] = result_dict.get('length', 0)
return result_dict
```

---

### PART 6: pdf_report.py Missing Function

**File**: `drug-triage-env/server/pdf_report.py`

**Add before `generate_quantamed_pdf` (line 46)**:

```python
def _generate_minimal_pdf(patient_id: str) -> bytes:
    """Fallback minimal PDF when fpdf2 is not installed."""
    return b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 595 842] /Contents 5 0 R >>\nendobj\n4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n5 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n50 750 Td\n(Report Unavailable) Tj\nET\nendstream\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF'
```

**Wrap patient data fetching (lines 54-56)**:

```python
try:
    patient = get_quantamed_patient_summary(patient_id)
    recs = recommend_quantamed_candidates(patient_id)
    ranked = recs["recommendations"]
except ValueError:
    # Unknown patient ID - create minimal data
    patient = {
        "name": patient_id,
        "condition": "Unknown",
        "age": "N/A",
        "sex": "N/A",
        "weight_kg": "N/A",
        "cyp_variant": "N/A",
        "current_drug": "N/A",
        "alt_u_l": "N/A",
        "liver_function": "N/A",
        "target_protein": "N/A"
    }
    ranked = []
```

---

## 🎯 SUCCESS CRITERIA

1. ✅ Server starts with zero import errors
2. ✅ Patient JSON upload returns analysis with drug rankings
3. ✅ All API endpoints return real computed data (no mock/hardcoded values)
4. ✅ PDF generation works for any patient ID
5. ✅ Protein structure modeling returns correct format
6. ✅ All 10 verification steps pass
7. ✅ Frontend displays uploaded patient data correctly
8. ✅ 3D visualizations render without errors
9. ✅ Drug recommendations are personalized per patient
10. ✅ Zero AttributeError, KeyError, or ImportError in logs

---

## 📊 PROGRESS TRACKING

- **Phase 1**: 0/2 complete (0%)
- **Phase 2**: 0/2 complete (0%)
- **Phase 3**: 0/2 complete (0%)
- **Phase 4**: 0/2 complete (0%)
- **Phase 5**: 0/3 complete (0%)
- **Phase 6**: 0/3 complete (0%)
- **Phase 7**: 0/1 complete (0%)

**Overall**: 0/15 parts complete (0%)

---

**Next Action**: Switch to Code mode and begin implementing fixes starting with Phase 1 (Critical Import Errors).