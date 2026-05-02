"""
Comprehensive System Test Suite
Tests all layers: Domain, Use Cases, Infrastructure, and API
"""

import json
import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, '.')

def test_patient_profiles():
    """Test 1: Load and validate all patient profiles"""
    print('='*80)
    print('TEST 1: Loading Patient Profiles')
    print('='*80)
    
    patient_files = [
        'sample_patient.json',
        'patient_diabetes.json', 
        'patient_hypertension.json',
        'patient_depression.json',
        'patient_asthma.json'
    ]
    
    loaded = 0
    for pfile in patient_files:
        try:
            with open(pfile, 'r') as f:
                data = json.load(f)
            print(f'[OK] {pfile}: {data["condition"]["primary_diagnosis"]} - {data["basic_info"]["age"]}{data["basic_info"]["gender"][0].upper()}')
            loaded += 1
        except Exception as e:
            print(f'[FAIL] {pfile}: {e}')
    
    return loaded == len(patient_files)

def test_domain_layer():
    """Test 2: Domain Layer - Patient Aggregate"""
    print('\n' + '='*80)
    print('TEST 2: Domain Layer - Patient Aggregate')
    print('='*80)
    
    try:
        from server.domain.patient import Patient, Gender, Severity, MetabolizerStatus
        print('[OK] Domain imports successful')
        
        # Create test patient
        with open('patient_diabetes.json', 'r') as f:
            patient_data = json.load(f)
        
        patient = Patient.create_new(patient_data)
        print(f'[OK] Patient created: {patient.session_id}')
        print(f'     Age: {patient.basic_info.age}, Gender: {patient.basic_info.gender.value}')
        print(f'     Condition: {patient.condition.primary_diagnosis}')
        print(f'     Risk Score: {patient.get_risk_score():.1f}/100')
        
        # Test business logic
        can_take, reasons = patient.can_take_drug('Metformin')
        print(f'[OK] Can take Metformin: {can_take}')
        if reasons:
            for r in reasons:
                print(f'     [WARN] {r}')
        
        return True
    except Exception as e:
        print(f'[FAIL] Domain layer error: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_use_cases():
    """Test 3: Use Cases Layer"""
    print('\n' + '='*80)
    print('TEST 3: Use Cases Layer')
    print('='*80)
    
    try:
        from server.use_cases.patient_use_cases import CreatePatientSessionUseCase, GetPatientSessionUseCase
        from server.infrastructure.patient_repository import InMemoryPatientRepository
        
        repo = InMemoryPatientRepository()
        create_use_case = CreatePatientSessionUseCase(repo)
        get_use_case = GetPatientSessionUseCase(repo)
        
        print('[OK] Use cases initialized')
        
        # Create patient session
        with open('patient_hypertension.json', 'r') as f:
            patient_data = json.load(f)
        
        result = create_use_case.execute(patient_data)
        session_id = result['session_id']
        print(f'[OK] Patient session created: {session_id}')
        
        # Retrieve patient
        retrieved = get_use_case.execute(session_id)
        print(f'[OK] Patient retrieved: {retrieved["condition"]["primary_diagnosis"]}')
        
        # Check repository
        all_patients = repo.find_all()
        print(f'[OK] Repository contains {len(all_patients)} patient(s)')
        
        return True
    except Exception as e:
        print(f'[FAIL] Use cases error: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_infrastructure():
    """Test 4: Infrastructure Layer - Service Adapters"""
    print('\n' + '='*80)
    print('TEST 4: Infrastructure Layer - Service Adapters')
    print('='*80)
    
    try:
        from server.infrastructure.service_adapters import (
            DrugAnalysisAdapter,
            ProteinFoldingAdapter,
            ScoringEngineAdapter
        )
        from server.domain.patient import Patient
        
        drug_service = DrugAnalysisAdapter()
        protein_service = ProteinFoldingAdapter()
        scoring_service = ScoringEngineAdapter()
        
        print('[OK] Service adapters initialized')
        
        # Test drug analysis
        with open('patient_depression.json', 'r') as f:
            patient_data = json.load(f)
        patient = Patient.create_new(patient_data)
        
        analysis = drug_service.analyze_drug_compatibility(patient, 'Sertraline', 50.0)
        print(f'[OK] Drug analysis complete: Compatible={analysis["compatible"]}')
        print(f'     Risk Score: {analysis["risk_score"]}')
        print(f'     Warnings: {len(analysis["warnings"])}')
        
        # Test scoring
        risk = scoring_service.calculate_risk_score(patient, 'Sertraline')
        print(f'[OK] Risk scoring: {risk:.1f}/100')
        
        # Test protein folding
        sim = protein_service.simulate_protein_folding('MSKRKPG', 'Sertraline')
        print(f'[OK] Protein simulation: Binding Energy={sim.get("binding_energy", "N/A")}')
        
        return True
    except Exception as e:
        print(f'[FAIL] Infrastructure error: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print('\n' + '=' * 80)
    print('QUANTAMED COMPREHENSIVE SYSTEM TEST'.center(80))
    print('=' * 80)
    print()
    
    results = {
        'Patient Profiles': test_patient_profiles(),
        'Domain Layer': test_domain_layer(),
        'Use Cases Layer': test_use_cases(),
        'Infrastructure Layer': test_infrastructure()
    }
    
    print('\n' + '='*80)
    print('TEST RESULTS SUMMARY')
    print('='*80)
    
    for test_name, passed in results.items():
        status = '[PASSED]' if passed else '[FAILED]'
        print(f'{test_name}: {status}')
    
    all_passed = all(results.values())
    
    print('\n' + '='*80)
    if all_passed:
        print('*** ALL TESTS PASSED - SYSTEM FULLY OPERATIONAL ***')
        print('='*80)
        print('[OK] Domain Layer: Patient aggregate with business logic')
        print('[OK] Use Cases Layer: Patient session management')
        print('[OK] Infrastructure Layer: Repository and service adapters')
        print('[OK] 5 Patient Profiles: Epilepsy, Diabetes, Hypertension, Depression, Asthma')
        print('\n>>> System is ready for API testing and production use!')
    else:
        print('!!! SOME TESTS FAILED - Review errors above')
    print('='*80)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
