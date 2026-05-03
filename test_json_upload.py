#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify JSON upload fix works correctly
"""
import json
import requests
import sys
import io

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

# Test with patient_diabetes.json
with open('patient_diabetes.json', 'r', encoding='utf-8') as f:
    patient_data = json.load(f)

print("=" * 60)
print("Testing JSON Upload Fix")
print("=" * 60)
print(f"\n[FILE] Loaded patient_diabetes.json")
print(f"   Genetics keys: {list(patient_data['genetics'].keys())}")
print(f"   Primary diagnosis: {patient_data['condition']['primary_diagnosis']}")

# Test API endpoint
url = "http://localhost:7860/api/patients/sessions"
print(f"\n[API] Sending POST request to {url}")

try:
    response = requests.post(url, json=patient_data, timeout=10)
    
    print(f"\n[RESPONSE] Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"[SUCCESS] Patient session created!")
        print(f"   Session ID: {result.get('session_id')}")
        print(f"   Message: {result.get('message')}")
        
        if 'analysis' in result:
            analysis = result['analysis']
            if 'rankings' in analysis and len(analysis['rankings']) > 0:
                print(f"\n[DRUGS] Drug Rankings:")
                for i, drug in enumerate(analysis['rankings'][:3], 1):
                    print(f"   {i}. {drug.get('drug_name', 'Unknown')} - Score: {drug.get('final_score', 0):.3f}")
            else:
                print(f"\n[WARNING] No drug rankings in analysis")
                if 'error' in analysis:
                    print(f"   Error: {analysis['error']}")
        else:
            print(f"\n[WARNING] No analysis in response")
    else:
        print(f"[FAILED] Request failed!")
        print(f"   Error: {response.text}")
        
except requests.exceptions.ConnectionError:
    print(f"[ERROR] Connection Error: Server not running on port 7860")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "=" * 60)

# Made with Bob
