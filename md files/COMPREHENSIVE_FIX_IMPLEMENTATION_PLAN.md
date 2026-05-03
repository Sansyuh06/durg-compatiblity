# Comprehensive Fix Implementation Plan

## Executive Summary
The root cause of "Unknown Patient" issue is schema mismatch between:
- **Expected**: Nested schema (`patient_data["basic_info"]["age"]`)
- **Actual**: Flat schema (`patient_data["age"]`)

## Implementation Order (Critical Path)

### Phase 1: Core Backend Fixes (A1-A8)
These must be done first as they fix the data pipeline.

#### A1: Patient.create_new() Schema Normalization ✅ PRIORITY 1
**File**: `drug-triage-env/server/domain/patient.py`
**Changes**:
1. Add `name: str = ""` field to Patient dataclass (line 155)
2. Create helper function `_extract_phenotype()` to parse genetics strings
3. Create helper function `_normalize_flat_schema()` to convert flat→nested
4. Modify `Patient.create_new()` to detect schema type and normalize
5. Add name extraction and storage
6. Update `to_dict()` to include name field
7. Fix gender normalization (M→male, F→female)
8. Fix severity stage mapping (Stage IIIA→severe)

#### A2: PatientRepository Alias ✅ PRIORITY 2
**File**: `drug-triage-env/server/infrastructure/patient_repository.py`
**Changes**: Add alias at bottom: `PatientRepository = InMemoryPatientRepository`

#### A8: requirements.txt ✅ PRIORITY 3
**File**: `drug-triage-env/requirements.txt`
**Changes**:
1. Add `python-multipart>=0.0.9`
2. Comment out qiskit: `# qiskit==0.46.3  # optional`
3. Remove bare `-e ` line if present

#### A7: build_patient_from_dict() Flat Schema Support ✅ PRIORITY 4
**File**: `drug-triage-env/server/patient_schema.py`
**Changes**: Add pre-normalization using same `_normalize_flat_schema()` logic

#### A5: Condition-Specific Drug Candidates ✅ PRIORITY 5
**File**: `drug-triage-env/server/scoring_engine.py`
**Changes**:
1. Add 5 drug candidate dicts at module level:
   - CANCER_DRUG_CANDIDATES (trastuzumab, pertuzumab, lapatinib, neratinib, tucatinib)
   - EPILEPSY_DRUG_CANDIDATES (existing vpa, ltg, lev, tpm, zns)
   - DIABETES_DRUG_CANDIDATES (metformin, empagliflozin, semaglutide, sitagliptin, pioglitazone)
   - HYPERTENSION_DRUG_CANDIDATES (lisinopril, amlodipine, losartan, metoprolol, hydrochlorothiazide)
   - DEPRESSION_DRUG_CANDIDATES (escitalopram, sertraline, bupropion, venlafaxine, mirtazapine)
2. Modify `run_full_analysis()` to detect diagnosis and select appropriate drug set
3. Update `pipeline_composite()` signature to accept drug_candidates parameter

#### A3: service_adapters.py Imports ✅ PRIORITY 6
**File**: `drug-triage-env/server/infrastructure/service_adapters.py`
**Changes**: Change absolute imports to relative imports (`.scoring_engine`, `.protein_dynamics`, `.pdf_report`)

#### A4: patient_router.py Fixes ✅ PRIORITY 7
**File**: `drug-triage-env/server/api/patient_router.py`
**Changes**:
1. Fix import to use alias
2. Add patient_name and patient_diagnosis to upload response

#### A6: Mount Router + New Endpoint ✅ PRIORITY 8
**File**: `drug-triage-env/server/app.py`
**Changes**:
1. Import patient_router
2. Call `app.include_router(patient_router)`
3. Add new endpoint `/api/quantamed/analyze-uploaded` that:
   - Accepts raw patient JSON (any schema)
   - Normalizes via Patient.create_new()
   - Runs run_full_analysis()
   - Returns results with patient_name and patient_diagnosis

### Phase 2: Frontend Fixes (B1-B5)
These improve UX but depend on Phase 1 working.

#### B2: Patient Upload Flow ✅ PRIORITY 9
**File**: `drug-triage-env/server/quantamed/index.html`
**Changes**: Update handleJsonUpload() to extract and display patient_name and patient_diagnosis from response

#### B1: UI Redesign ✅ PRIORITY 10
**File**: `drug-triage-env/server/quantamed/index.html`
**Changes**: Complete CSS overhaul with AlphaFold aesthetic (can be done incrementally)

#### B3: Molecular Binding Ribbons ✅ PRIORITY 11
**File**: `drug-triage-env/server/quantamed/molecular_binding.js`
**Changes**: Upgrade to realistic protein ribbons (already partially done)

#### B4 & B5: Canvas Fixes ✅ PRIORITY 12
**Files**: `drug-triage-env/server/quantamed/index.html`
**Changes**: Verify TRIBE v2 and protein folding canvas initialization fixes

### Phase 3: Verification (C1-C6)
Run all test scripts to confirm fixes work.

## Current Status
- Server is running on port 7860
- Need to stop server before making changes
- After changes, restart with PYTHONPATH set

## Next Steps
1. Stop running server (Ctrl+C in terminal)
2. Implement A1 (Patient schema normalization) - MOST CRITICAL
3. Implement A2, A8 (quick wins)
4. Implement A7, A5 (data processing)
5. Implement A3, A4, A6 (API layer)
6. Restart server and test
7. Implement B2 (upload flow)
8. Test with cancer patient JSON
9. Implement remaining UI fixes
10. Run full verification suite

## Files to Modify (in order)
1. ✅ drug-triage-env/server/domain/patient.py (A1)
2. ✅ drug-triage-env/server/infrastructure/patient_repository.py (A2)
3. ✅ drug-triage-env/requirements.txt (A8)
4. ✅ drug-triage-env/server/patient_schema.py (A7)
5. ✅ drug-triage-env/server/scoring_engine.py (A5)
6. ✅ drug-triage-env/server/infrastructure/service_adapters.py (A3)
7. ✅ drug-triage-env/server/api/patient_router.py (A4)
8. ✅ drug-triage-env/server/app.py (A6)
9. ✅ drug-triage-env/server/quantamed/index.html (B2, B1, B4, B5)
10. ✅ drug-triage-env/server/quantamed/molecular_binding.js (B3)

## Success Criteria
- Upload patient_cancer_targeted_therapy.json
- See "Sarah Chen" (not "Unknown Patient")
- See "HER2-Positive Breast Cancer" diagnosis
- See cancer drugs (Trastuzumab, Pertuzumab) in rankings
- All 6 verification steps pass