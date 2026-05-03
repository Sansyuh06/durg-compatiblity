#!/usr/bin/env python3
"""Test script for dynamic patient recommendations"""

import json
from server.quantamed_sim import recommend_for_dynamic_patient

def test_patient(filename):
    print(f"\n{'='*60}")
    print(f"Testing: {filename}")
    print('='*60)
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    result = recommend_for_dynamic_patient(data)
    
    print(f"Patient: {result['patient_name']}")
    print(f"Condition: {result['condition']}")
    print(f"Patient ID: {result['patient_id']}")
    print(f"\nTop 5 Drug Recommendations:")
    print("-" * 60)
    
    for i, rec in enumerate(result['recommendations'][:5], 1):
        print(f"{i}. {rec['label']}")
        print(f"   Composite Score: {rec['composite_score']:.3f}")
        print(f"   Efficacy: {rec['scores']['efficacy']:.1f}")
        print(f"   Safety: {rec['scores']['safety']:.1f}")
        print(f"   BBB: {rec['scores']['bbb']:.1f}")
        print(f"   Exposure Modifier: {rec['scores']['exposure_modifier']:.2f}x")
        print()

if __name__ == "__main__":
    # Test all three patient types
    test_patient('patient_diabetes.json')
    test_patient('patient_hypertension.json')
    test_patient('patient_depression.json')
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)

# Made with Bob
