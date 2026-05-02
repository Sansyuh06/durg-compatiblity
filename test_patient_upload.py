"""
Quick test script to verify patient JSON upload functionality
"""
import requests
import json

# Load sample patient
with open('sample_patient.json', 'r') as f:
    patient_data = json.load(f)

# Test the endpoint
url = 'http://localhost:7860/api/patients/sessions'
response = requests.post(url, json=patient_data)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    print("\n✅ SUCCESS! Patient upload is working!")
    session_id = response.json().get('session_id')
    print(f"Session ID: {session_id}")
else:
    print("\n❌ FAILED! Error occurred")

# Made with Bob
