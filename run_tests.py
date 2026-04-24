#!/usr/bin/env python3
"""Comprehensive backend functional test suite for Foldables/QuantaMed."""
import sys
import traceback
sys.path.insert(0, '.')

errors = []
passed = []

def ok(label):
    passed.append(label)
    print(f"  [PASS] {label}")

def fail(label, exc):
    errors.append((label, str(exc)))
    print(f"  [FAIL] {label} -> {exc}")

# ── Module imports ────────────────────────────────────────────────────────
print("\n=== 1. Module Imports ===")
try:
    from server.patient_schema import (
        build_patient_from_dict, GABI_PRESET, PatientProfile,
        BasicInfo, Condition, Genetics, Labs, classify_liver, classify_kidney
    )
    ok("patient_schema import")
except Exception as e:
    fail("patient_schema import", e)

try:
    from server.kaggle_data import (
        get_drug_properties, get_all_drug_ids, get_tox21_profile,
        get_faers_signals, lookup_protein_target,
        DRUG_PROPERTIES, DRUGBANK_PK, OFF_TARGET_BINDING, BBBP_DATA, TOX21_DATA, FAERS_SIGNALS
    )
    ok("kaggle_data import")
except Exception as e:
    fail("kaggle_data import", e)

try:
    from server.quantamed_sim import (
        compute_pk_curve, get_quantamed_candidates, get_quantamed_patient_profiles,
        get_quantamed_drug_summary, get_quantamed_patient_summary,
        recommend_quantamed_candidates, quantum_protein_folding_payload,
        vqe_demo_payload, score_quantamed_candidate, simulate_tribe_response
    )
    ok("quantamed_sim import")
except Exception as e:
    fail("quantamed_sim import", e)

try:
    from server.scoring_engine import run_full_analysis, pipeline_pk, pipeline_admet, pipeline_faers
    ok("scoring_engine import")
except Exception as e:
    fail("scoring_engine import", e)

try:
    from server.protein_structure import model_protein_from_fasta, get_example_sequences
    ok("protein_structure import")
except Exception as e:
    fail("protein_structure import", e)

try:
    from server.pdf_report import generate_quantamed_pdf
    ok("pdf_report import")
except Exception as e:
    fail("pdf_report import", e)

# ── patient_schema tests ──────────────────────────────────────────────────
print("\n=== 2. Patient Schema ===")
try:
    assert classify_liver(42, None) == "mild_impairment"
    assert classify_liver(30, None) == "normal"
    assert classify_liver(None, None) == "unknown"
    ok("classify_liver")
except Exception as e:
    fail("classify_liver", e)

try:
    assert classify_kidney(95) == "normal"
    assert classify_kidney(50) == "moderate_impairment"
    assert classify_kidney(None) == "unknown"
    ok("classify_kidney")
except Exception as e:
    fail("classify_kidney", e)

try:
    p = build_patient_from_dict(GABI_PRESET)
    assert isinstance(p, PatientProfile)
    assert p.basic_info.age == 24
    assert p.basic_info.gender == "female"
    assert p.organs.liver_status == "mild_impairment"
    ok("build_patient_from_dict (GABI_PRESET)")
except Exception as e:
    fail("build_patient_from_dict (GABI_PRESET)", e)

try:
    p = build_patient_from_dict(GABI_PRESET)
    c = p.completeness()
    assert "percentage" in c
    assert c["percentage"] > 0
    ok("PatientProfile.completeness()")
except Exception as e:
    fail("PatientProfile.completeness()", e)

try:
    p = build_patient_from_dict(GABI_PRESET)
    alerts = p.clinical_alerts()
    assert isinstance(alerts, list)
    ok(f"PatientProfile.clinical_alerts() -> {len(alerts)} alert(s)")
except Exception as e:
    fail("PatientProfile.clinical_alerts()", e)

try:
    p = build_patient_from_dict({})
    assert p.basic_info.age is None
    ok("build_patient_from_dict (empty dict)")
except Exception as e:
    fail("build_patient_from_dict (empty dict)", e)

# ── kaggle_data tests ─────────────────────────────────────────────────────
print("\n=== 3. Kaggle Data ===")
try:
    ids = get_all_drug_ids()
    assert set(ids) == {"vpa", "ltg", "lev", "tpm", "zns"}
    ok("get_all_drug_ids")
except Exception as e:
    fail("get_all_drug_ids", e)

for drug in ["vpa", "ltg", "lev", "tpm", "zns"]:
    try:
        props = get_drug_properties(drug)
        assert "name" in props
        assert "pk" in props
        assert "cyp" in props
        assert "off_target" in props
        ok(f"get_drug_properties({drug})")
    except Exception as e:
        fail(f"get_drug_properties({drug})", e)

try:
    get_drug_properties("invalid_drug_xyz")
    fail("get_drug_properties(invalid)", "Should have raised ValueError")
except ValueError:
    ok("get_drug_properties(invalid) -> ValueError as expected")
except Exception as e:
    fail("get_drug_properties(invalid)", e)

for drug in ["vpa", "ltg", "lev", "tpm", "zns"]:
    try:
        tox = get_tox21_profile(drug)
        assert "teratogenicity" in tox
        ok(f"get_tox21_profile({drug})")
    except Exception as e:
        fail(f"get_tox21_profile({drug})", e)

for drug in ["vpa", "ltg", "lev", "tpm", "zns"]:
    try:
        faers = get_faers_signals(drug)
        assert "total_reports" in faers
        ok(f"get_faers_signals({drug})")
    except Exception as e:
        fail(f"get_faers_signals({drug})", e)

try:
    t = lookup_protein_target("SCN2A")
    assert t is not None
    assert "uniprot" in t
    ok("lookup_protein_target(SCN2A)")
except Exception as e:
    fail("lookup_protein_target(SCN2A)", e)

try:
    t = lookup_protein_target("NONEXISTENT_GENE")
    assert t is None
    ok("lookup_protein_target(nonexistent) -> None")
except Exception as e:
    fail("lookup_protein_target(nonexistent)", e)

# ── quantamed_sim tests ───────────────────────────────────────────────────
print("\n=== 4. QuantaMed Sim ===")
for drug in ["vpa", "ltg", "lev", "tpm", "zns"]:
    try:
        r = compute_pk_curve(drug_id=drug, daily_dose_mg=1000)
        assert "series" in r
        assert len(r["series"]["t_h"]) > 0
        cmax = r["derived"]["cmax_ug_ml"]
        ok(f"compute_pk_curve({drug}) cmax={cmax:.2f}")
    except Exception as e:
        fail(f"compute_pk_curve({drug})", e)

try:
    compute_pk_curve(drug_id="invalid_drug", daily_dose_mg=1000)
    fail("compute_pk_curve(invalid_drug)", "Should have raised ValueError")
except ValueError:
    ok("compute_pk_curve(invalid_drug) -> ValueError as expected")
except Exception as e:
    fail("compute_pk_curve(invalid_drug)", e)

try:
    candidates = get_quantamed_candidates()
    assert len(candidates) == 5
    ok(f"get_quantamed_candidates -> {len(candidates)} candidates")
except Exception as e:
    fail("get_quantamed_candidates", e)

try:
    patients = get_quantamed_patient_profiles()
    assert len(patients) == 3
    ok(f"get_quantamed_patient_profiles -> {len(patients)} patients")
except Exception as e:
    fail("get_quantamed_patient_profiles", e)

PATIENT_IDS = [
    "juvenile_myoclonic_epilepsy",
    "treatment_resistant_depression",
    "anxiety_plus_depression"
]

for pid in PATIENT_IDS:
    try:
        r = get_quantamed_patient_summary(pid)
        assert "patient_id" in r
        ok(f"get_quantamed_patient_summary({pid[:20]})")
    except Exception as e:
        fail(f"get_quantamed_patient_summary({pid[:20]})", e)

try:
    get_quantamed_patient_summary("nonexistent_patient")
    fail("get_quantamed_patient_summary(invalid)", "Should have raised ValueError")
except ValueError:
    ok("get_quantamed_patient_summary(invalid) -> ValueError as expected")
except Exception as e:
    fail("get_quantamed_patient_summary(invalid)", e)

for drug in ["vpa", "ltg", "lev", "tpm", "zns"]:
    for pid in PATIENT_IDS:
        try:
            r = score_quantamed_candidate(drug, pid)
            assert "scores" in r
            composite = r["scores"]["composite"]
            assert 0 <= composite <= 1
            ok(f"score_candidate({drug},{pid[:15]}) composite={composite:.4f}")
        except Exception as e:
            fail(f"score_candidate({drug},{pid[:15]})", e)

for pid in PATIENT_IDS:
    try:
        r = recommend_quantamed_candidates(pid)
        assert "recommendations" in r
        assert len(r["recommendations"]) == 5
        top = r["recommendations"][0]["drug_id"]
        ok(f"recommend({pid[:20]}) -> top={top}")
    except Exception as e:
        fail(f"recommend({pid[:20]})", e)

for drug in ["vpa", "ltg", "lev"]:
    for pid in PATIENT_IDS:
        try:
            r = get_quantamed_drug_summary(drug, pid)
            assert "scores" in r
            ok(f"drug_summary({drug},{pid[:15]})")
        except Exception as e:
            fail(f"drug_summary({drug},{pid[:15]})", e)

for drug in ["ltg", "vpa", "lev"]:
    for pid in PATIENT_IDS:
        try:
            r = simulate_tribe_response(drug, pid)
            assert "brain_state" in r
            ok(f"tribe_response({drug},{pid[:15]})")
        except Exception as e:
            fail(f"tribe_response({drug},{pid[:15]})", e)

try:
    r = quantum_protein_folding_payload()
    has_frames = "frames" in r or "animation_frames" in r
    assert has_frames
    ok(f"quantum_protein_folding_payload -> backend={r['backend']}")
except Exception as e:
    fail("quantum_protein_folding_payload", e)

try:
    r = vqe_demo_payload()
    assert "datasets" in r
    assert len(r["datasets"]) == 5
    ok(f"vqe_demo_payload -> {len(r['datasets'])} datasets")
except Exception as e:
    fail("vqe_demo_payload", e)

# ── scoring_engine tests ──────────────────────────────────────────────────
print("\n=== 5. Scoring Engine ===")
try:
    p = build_patient_from_dict(GABI_PRESET)
    for drug in ["vpa", "ltg", "lev", "tpm", "zns"]:
        r = pipeline_pk(p, drug, 1000)
        assert "series" in r or "error" in r
        ok(f"pipeline_pk({drug})")
except Exception as e:
    fail("pipeline_pk", e)

try:
    for drug in ["vpa", "ltg", "lev", "tpm", "zns"]:
        r = pipeline_admet(drug)
        assert "score" in r
        ok(f"pipeline_admet({drug}) score={r['score']}")
except Exception as e:
    fail("pipeline_admet", e)

try:
    for drug in ["vpa", "ltg", "lev", "tpm", "zns"]:
        r = pipeline_faers(drug)
        assert "total_reports" in r or "events" in r
        ok(f"pipeline_faers({drug})")
except Exception as e:
    fail("pipeline_faers", e)

try:
    p = build_patient_from_dict(GABI_PRESET)
    result = run_full_analysis(p)
    assert "rankings" in result
    assert len(result["rankings"]) == 5
    top = result["rankings"][0]["drug_id"]
    score = result["rankings"][0]["composite_score"]
    ok(f"run_full_analysis -> top={top}, score={score}")
except Exception as e:
    fail("run_full_analysis", e)

# ── protein_structure tests ───────────────────────────────────────────────
print("\n=== 6. Protein Structure ===")
try:
    examples = get_example_sequences()
    assert isinstance(examples, (list, dict))
    assert len(examples) > 0
    ok(f"get_example_sequences -> {len(examples)} examples (type={type(examples).__name__})")
except Exception as e:
    fail("get_example_sequences", e)

TEST_FASTA = """>sp|P01308|INS_HUMAN Insulin OS=Homo sapiens GN=INS PE=1 SV=1
MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAEDLQVGQVELGG
GPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN"""

try:
    r = model_protein_from_fasta(TEST_FASTA)
    assert "residues" in r
    assert len(r["residues"]) > 0
    ok(f"model_protein_from_fasta -> {len(r['residues'])} residues")
except Exception as e:
    fail("model_protein_from_fasta", e)

try:
    r = model_protein_from_fasta("MKVLWAALLVTFLAGCQA")
    assert "residues" in r
    ok("model_protein_from_fasta (raw sequence)")
except Exception as e:
    fail("model_protein_from_fasta (raw sequence)", e)

try:
    r = model_protein_from_fasta("")
    assert "error" in r
    ok("model_protein_from_fasta (empty) -> error key as expected")
except Exception as e:
    fail("model_protein_from_fasta (empty)", e)

# ── pdf_report tests ──────────────────────────────────────────────────────
print("\n=== 7. PDF Report ===")
for pid in PATIENT_IDS:
    try:
        pdf_bytes = generate_quantamed_pdf(patient_id=pid)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100
        ok(f"generate_quantamed_pdf({pid[:20]}) -> {len(pdf_bytes)} bytes")
    except Exception as e:
        fail(f"generate_quantamed_pdf({pid[:20]})", e)

# ── Summary ───────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"RESULTS: {len(passed)} passed, {len(errors)} failed")
if errors:
    print("\nFAILURES:")
    for label, msg in errors:
        print(f"  - {label}: {msg}")
else:
    print("ALL TESTS PASSED - Backend is fully functional!")
print('='*60)
sys.exit(0 if not errors else 1)
