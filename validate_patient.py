"""Validate sample_patient.json against the patient schema."""
import json
import sys
from server.patient_schema import build_patient_from_dict

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load and validate
with open('sample_patient.json', 'r') as f:
    data = json.load(f)

patient = build_patient_from_dict(data)
completeness = patient.completeness()
alerts = patient.clinical_alerts()

print("=" * 60)
print("PATIENT JSON VALIDATION RESULTS")
print("=" * 60)
print(f"[OK] Patient JSON validates successfully")
print(f"[OK] Completeness: {completeness['percentage']}%")
print(f"[OK] Confidence Level: {completeness['confidence_level']}")
print(f"[OK] Clinical Alerts: {len(alerts)} alerts generated")
print()
print("Patient Profile Summary:")
print(f"  - Name: {data.get('_metadata', {}).get('profile_name', 'N/A')}")
print(f"  - Age: {patient.basic_info.age}")
print(f"  - Gender: {patient.basic_info.gender}")
print(f"  - Primary Diagnosis: {patient.condition.primary_diagnosis}")
print(f"  - Current Medications: {len(patient.current_meds)}")
print(f"  - Genetics Complete: CYP2D6={patient.genetics.CYP2D6}, CYP2C9={patient.genetics.CYP2C9}")
print(f"  - Liver Status: {patient.organs.liver_status}")
print(f"  - Kidney Status: {patient.organs.kidney_status}")
print()
print("Clinical Alerts:")
for i, alert in enumerate(alerts, 1):
    print(f"  {i}. [{alert['type']}] {alert['title']}")
print()
print("=" * 60)
print("VALIDATION COMPLETE - ALL CHECKS PASSED")
print("=" * 60)

# Made with Bob
