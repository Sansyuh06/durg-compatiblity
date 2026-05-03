#!/usr/bin/env python3
"""
Test script to verify cancer patient file upload works correctly
"""

import json
import sys
from pathlib import Path

def test_cancer_patient_file():
    """Validate cancer patient JSON file"""
    
    print("=" * 60)
    print("CANCER PATIENT FILE VALIDATION TEST")
    print("=" * 60)
    
    # 1. Check file exists
    file_path = Path("patient_cancer_targeted_therapy.json")
    print(f"\n1. Checking file exists: {file_path}")
    
    if not file_path.exists():
        print(f"   ❌ FAILED: File not found at {file_path.absolute()}")
        return False
    print(f"   ✅ PASSED: File exists")
    
    # 2. Validate JSON format
    print(f"\n2. Validating JSON format")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            patient_data = json.load(f)
        print(f"   ✅ PASSED: Valid JSON")
    except json.JSONDecodeError as e:
        print(f"   ❌ FAILED: Invalid JSON - {e}")
        return False
    except Exception as e:
        print(f"   ❌ FAILED: Error reading file - {e}")
        return False
    
    # 3. Validate required fields
    print(f"\n3. Validating required fields")
    required_fields = ['patientId', 'name', 'age', 'conditions', 'genetics']
    missing_fields = [field for field in required_fields if field not in patient_data]
    
    if missing_fields:
        print(f"   ❌ FAILED: Missing required fields: {missing_fields}")
        return False
    print(f"   ✅ PASSED: All required fields present")
    
    # 4. Validate patient details
    print(f"\n4. Validating patient details")
    print(f"   Patient ID: {patient_data.get('patientId')}")
    print(f"   Name: {patient_data.get('name')}")
    print(f"   Age: {patient_data.get('age')}")
    print(f"   Sex: {patient_data.get('sex')}")
    
    if patient_data.get('name') != 'Sarah Chen':
        print(f"   ⚠️  WARNING: Expected name 'Sarah Chen', got '{patient_data.get('name')}'")
    else:
        print(f"   ✅ PASSED: Patient name correct")
    
    # 5. Validate conditions
    print(f"\n5. Validating conditions")
    conditions = patient_data.get('conditions', [])
    print(f"   Number of conditions: {len(conditions)}")
    
    if len(conditions) > 0:
        primary_condition = conditions[0].get('name', 'Unknown')
        print(f"   Primary condition: {primary_condition}")
        
        if 'HER2' in primary_condition or 'Breast Cancer' in primary_condition:
            print(f"   ✅ PASSED: Cancer condition found")
        else:
            print(f"   ⚠️  WARNING: Expected cancer condition")
    else:
        print(f"   ❌ FAILED: No conditions found")
        return False
    
    # 6. Validate genetics
    print(f"\n6. Validating genetics data")
    genetics = patient_data.get('genetics', {})
    print(f"   Number of genetic markers: {len(genetics)}")
    
    key_markers = ['CYP2D6', 'ERBB2', 'PIK3CA', 'UGT1A1']
    found_markers = [marker for marker in key_markers if marker in genetics or marker.lower() in genetics]
    
    print(f"   Key markers found: {found_markers}")
    
    if len(found_markers) >= 3:
        print(f"   ✅ PASSED: Sufficient genetic markers")
    else:
        print(f"   ⚠️  WARNING: Expected more genetic markers")
    
    # 7. Validate quantum considerations
    print(f"\n7. Validating quantum protein targets")
    quantum = patient_data.get('quantumConsiderations', {})
    
    if 'proteinTargets' in quantum:
        targets = quantum['proteinTargets']
        print(f"   Protein targets: {targets}")
        print(f"   ✅ PASSED: Quantum targets defined")
    else:
        print(f"   ⚠️  WARNING: No quantum targets defined")
    
    if 'drugCandidates' in quantum:
        candidates = quantum['drugCandidates']
        print(f"   Drug candidates: {len(candidates)}")
        for drug in candidates:
            print(f"     - {drug.get('name')}: {drug.get('mechanism')}")
        print(f"   ✅ PASSED: Drug candidates defined")
    else:
        print(f"   ⚠️  WARNING: No drug candidates defined")
    
    # 8. File size check
    print(f"\n8. File size check")
    file_size = file_path.stat().st_size
    print(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    if file_size > 1024 * 1024:  # 1 MB
        print(f"   ⚠️  WARNING: File is quite large (>{file_size/1024/1024:.1f} MB)")
    else:
        print(f"   ✅ PASSED: File size reasonable")
    
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    print("\n✅ Cancer patient file is valid and ready to upload!")
    print("\nNext steps:")
    print("1. Start server: python server/app.py")
    print("2. Open browser: http://localhost:7860/quantamed/")
    print("3. Click 'UPLOAD PATIENT JSON'")
    print("4. Select: patient_cancer_targeted_therapy.json")
    print("5. Verify patient name changes to 'Sarah Chen'")
    
    return True

def test_backend_api():
    """Test backend API if server is running"""
    print("\n" + "=" * 60)
    print("BACKEND API TEST (Optional)")
    print("=" * 60)
    
    try:
        import requests
        
        # Check if server is running
        try:
            response = requests.get('http://localhost:7860/quantamed/', timeout=2)
            print("\n✅ Server is running")
        except requests.exceptions.ConnectionError:
            print("\n⚠️  Server not running - skipping API test")
            print("   Start server with: python server/app.py")
            return
        
        # Load patient file
        with open('patient_cancer_targeted_therapy.json', 'r') as f:
            patient_data = json.load(f)
        
        # Test API endpoint
        print("\nTesting POST /api/patients/sessions...")
        response = requests.post(
            'http://localhost:7860/api/patients/sessions',
            json=patient_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API test PASSED")
            print(f"   Session ID: {result.get('session_id')}")
            print(f"   Patient Name: {result.get('patient_name')}")
        else:
            print(f"❌ API test FAILED: Status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except ImportError:
        print("\n⚠️  'requests' library not installed - skipping API test")
        print("   Install with: pip install requests")
    except Exception as e:
        print(f"\n❌ API test error: {e}")

if __name__ == '__main__':
    try:
        # Run file validation
        success = test_cancer_patient_file()
        
        # Optionally test backend API
        test_backend_api()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
