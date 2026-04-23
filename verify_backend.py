"""Full backend verification script - uses correct API names."""

def run():
    errors = []

    # 1. Protein Structure
    try:
        from server.protein_structure import model_protein_from_fasta
        result = model_protein_from_fasta(">test\nMVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH")
        print(f"  OK: Protein model - {len(result['residues'])} residues")
    except Exception as e:
        errors.append(f"protein_structure: {e}")
        print(f"  FAIL: protein_structure - {e}")

    # 2. Patient Schema
    try:
        from server.patient_schema import PatientProfile
        p = PatientProfile()
        alerts = p.clinical_alerts()
        print(f"  OK: PatientProfile - {len(alerts)} alerts")
    except Exception as e:
        errors.append(f"patient_schema: {e}")
        print(f"  FAIL: patient_schema - {e}")

    # 3. QuantaMed Sim
    try:
        from server.quantamed_sim import get_quantamed_candidates, recommend_quantamed_candidates
        c = get_quantamed_candidates()
        print(f"  OK: Candidates - {len(c)} drugs")
        r = recommend_quantamed_candidates("juvenile_myoclonic_epilepsy")
        print(f"  OK: Recommendations - {len(r['recommendations'])} ranked")
    except Exception as e:
        errors.append(f"quantamed_sim: {e}")
        print(f"  FAIL: quantamed_sim - {e}")

    # 4. Scoring Engine
    try:
        from server.scoring_engine import run_full_analysis
        s = run_full_analysis("vpa", "juvenile_myoclonic_epilepsy")
        print(f"  OK: Scoring - composite={s['composite_score']}")
    except Exception as e:
        errors.append(f"scoring_engine: {e}")
        print(f"  FAIL: scoring_engine - {e}")

    # 5. PDF Report
    try:
        from server.pdf_report import generate_quantamed_pdf
        pdf = generate_quantamed_pdf(patient_id="juvenile_myoclonic_epilepsy")
        print(f"  OK: PDF Report - {len(pdf)} bytes")
    except Exception as e:
        errors.append(f"pdf_report: {e}")
        print(f"  FAIL: pdf_report - {e}")

    # 6. Kaggle Data
    try:
        from server.kaggle_data import get_drug_properties, get_faers_signals
        d = get_drug_properties("vpa")
        f = get_faers_signals("vpa")
        print(f"  OK: Kaggle Data - props={len(d)} keys, faers={len(f)} signals")
    except Exception as e:
        errors.append(f"kaggle_data: {e}")
        print(f"  FAIL: kaggle_data - {e}")

    # 7. Environment
    try:
        from environment.env import DrugTriageEnv
        env = DrugTriageEnv()
        obs = env.reset()
        print(f"  OK: Environment - reset returns {type(obs).__name__}")
    except Exception as e:
        errors.append(f"environment: {e}")
        print(f"  FAIL: environment - {e}")

    print(f"\n{'='*50}")
    if errors:
        print(f"RESULT: {len(errors)} ERRORS FOUND")
        for e in errors:
            print(f"  - {e}")
    else:
        print("RESULT: ALL BACKEND CHECKS PASSED - ZERO ERRORS")

if __name__ == "__main__":
    run()
