# Complete Patient Upload & Molecular Visualization Debug Guide

## Problem Analysis

Your screenshot shows "Unknown Patient" with Valproic Acid - this is the **default demo patient** that loads when no file is uploaded. The cancer patient file exists but hasn't been uploaded through the UI yet.

## Patient Data Flow Pipeline

```
JSON File → File Upload → handleJsonUpload() → Backend API → updatePatientUI() → Molecular Visualization
```

### Step-by-Step Data Flow

1. **File Selection** (`index.html` line 930)
   ```html
   <input type="file" id="json-upload" accept=".json" onchange="handleJsonUpload(event)">
   ```

2. **Upload Handler** (`index.html` lines 3815-3870)
   - Reads file with FileReader
   - Parses JSON
   - Calls `/api/patients/sessions` (POST)
   - Updates `window.patientData`
   - Calls `updatePatientUI(data)`
   - Calls `fetchDynamicRecommendations(data)`

3. **Backend Processing** (`server/app.py`)
   - Creates patient session
   - Normalizes genetics keys (lowercase)
   - Returns session_id

4. **UI Update** (`updatePatientUI` function)
   - Updates patient name, age, conditions
   - Updates genetics display
   - Updates drug recommendations

5. **Molecular Visualization** (`molecular_binding.js`)
   - Uses patient data for drug selection
   - Renders protein-drug interactions

## File Locations

### Patient Files
```
✅ drug-triage-env/patient_cancer_targeted_therapy.json (CREATED)
✅ drug-triage-env/patient_diabetes.json
✅ drug-triage-env/patient_hypertension.json
✅ drug-triage-env/patient_depression.json
✅ drug-triage-env/patient_asthma.json
```

### Code Files
```
✅ drug-triage-env/server/quantamed/index.html (lines 3815-3870: handleJsonUpload)
✅ drug-triage-env/server/quantamed/molecular_binding.js (lines 216-556: realistic ribbons)
✅ drug-triage-env/server/app.py (patient session API)
✅ drug-triage-env/server/domain/patient.py (genetics normalization)
```

## How to Upload Cancer Patient File

### Method 1: Through UI (Recommended)

1. **Start Server**
   ```bash
   cd drug-triage-env
   python server/app.py
   ```

2. **Open Browser**
   ```
   http://localhost:7860/quantamed/
   ```

3. **Upload File**
   - Click "UPLOAD PATIENT JSON" button
   - Navigate to: `D:\fyeshi\project\quantum\shiva vro\drug-triage-env\patient_cancer_targeted_therapy.json`
   - Select file
   - Wait for loading screen

4. **Verify Upload**
   - Patient name should change from "Unknown Patient" to "Sarah Chen"
   - Age should show "52"
   - Condition should show "HER2-Positive Breast Cancer"
   - Current drug should show cancer medications

### Method 2: Direct API Test

```bash
cd drug-triage-env
curl -X POST http://localhost:7860/api/patients/sessions \
  -H "Content-Type: application/json" \
  -d @patient_cancer_targeted_therapy.json
```

Expected response:
```json
{
  "session_id": "PT-2026-ONCO-7842",
  "patient_name": "Sarah Chen",
  "conditions": ["HER2-Positive Breast Cancer", "Type 2 Diabetes Mellitus", "Hypertension"]
}
```

## Debugging Checklist

### ✅ 1. Verify File Exists
```bash
cd drug-triage-env
dir patient_cancer_targeted_therapy.json
```
Should show: `patient_cancer_targeted_therapy.json`

### ✅ 2. Validate JSON Format
```bash
python -m json.tool patient_cancer_targeted_therapy.json > nul
```
No output = valid JSON

### ✅ 3. Check Server Running
```bash
curl http://localhost:7860/quantamed/
```
Should return HTML

### ✅ 4. Test Backend API
```bash
curl -X POST http://localhost:7860/api/patients/sessions \
  -H "Content-Type: application/json" \
  -d "{\"patientId\":\"test\",\"name\":\"Test\",\"age\":50,\"conditions\":[],\"genetics\":{}}"
```
Should return session_id

### ✅ 5. Check Browser Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Upload patient file
4. Look for:
   ```
   Loaded Patient JSON: {patientId: "PT-2026-ONCO-7842", ...}
   Patient session created: PT-2026-ONCO-7842
   ✅ Patient file uploaded and processed
   ```

### ✅ 6. Check Network Tab
1. Open DevTools → Network tab
2. Upload file
3. Look for POST to `/api/patients/sessions`
4. Status should be 200
5. Response should contain session_id

### ✅ 7. Verify Molecular Binding
1. After upload, scroll to "STEP 08: MOL BINDING"
2. Should show two canvases with 3D protein structures
3. Left: Current drug (from patient file)
4. Right: Recommended drug

## Cancer Patient Specific Features

### Expected Data Display

**Patient Profile:**
- Name: Sarah Chen
- Age: 52
- Sex: Female
- Ethnicity: East Asian

**Primary Condition:**
- HER2-Positive Breast Cancer (Stage IIIA)
- Tumor Markers: HER2 3+, ER 85%, PR 70%

**Genetics:**
- CYP2D6: *1/*4 (Intermediate Metabolizer)
- ERBB2: Amplified (HER2+)
- PIK3CA: E545K mutation
- UGT1A1: *1/*28 (Reduced Activity)

**Drug Candidates:**
- Trastuzumab (HER2 antibody)
- Pertuzumab (HER2 dimerization inhibitor)
- Alpelisib (PI3K inhibitor for PIK3CA mutation)
- Palbociclib (CDK4/6 inhibitor)

### Quantum Protein Targets

**HER2 (ERBB2):**
- PDB ID: 1N8Z
- Extracellular domain
- Trastuzumab binding site: Domain IV
- Pertuzumab binding site: Domain II

**PIK3CA (Mutant):**
- PDB ID: 4OVU
- E545K mutation
- Alpelisib binding site: ATP-binding pocket

## Molecular Visualization Features

### Realistic Protein Ribbons (Already Implemented)

**Alpha Helices:**
- Smooth twisted ribbons (not tubes)
- 3.6 residues per turn
- Proper helical geometry

**Beta Sheets:**
- Flat arrow-shaped ribbons
- Tapered ends
- Proper strand orientation

**Molecular Dynamics:**
- Thermal fluctuations (RMSF)
- Induced-fit binding
- Protein breathing
- Constrained motion in bound state

### Code Locations

**Ribbon Rendering:**
- File: `drug-triage-env/server/quantamed/molecular_binding.js`
- Lines: 216-556
- Functions: `createAlphaHelix()`, `createBetaSheet()`, `createLoop()`

**Molecular Dynamics:**
- File: `drug-triage-env/server/quantamed/molecular_binding.js`
- Lines: 493-656
- Features: Protein breathing, induced fit, thermal motion

## Troubleshooting Common Issues

### Issue 1: "Unknown Patient" Still Showing

**Cause:** File not uploaded yet (showing default demo)

**Solution:**
1. Click "UPLOAD PATIENT JSON" button
2. Select `patient_cancer_targeted_therapy.json`
3. Wait for loading screen to complete

### Issue 2: Upload Button Not Working

**Cause:** JavaScript error or file input not triggering

**Solution:**
1. Check browser console for errors
2. Try hard refresh: Ctrl+Shift+R
3. Clear browser cache
4. Restart server

### Issue 3: "Invalid JSON" Error

**Cause:** Malformed JSON file

**Solution:**
```bash
python -m json.tool patient_cancer_targeted_therapy.json
```
If error, check for:
- Missing commas
- Unclosed brackets
- Invalid escape sequences

### Issue 4: Molecular Binding Shows Simple Shapes

**Cause:** Browser cache or old JavaScript file

**Solution:**
1. Stop server (Ctrl+C)
2. Clear browser cache (Ctrl+Shift+Delete)
3. Hard refresh (Ctrl+Shift+R)
4. Restart server
5. Re-upload patient file

### Issue 5: Backend API Error

**Cause:** Server not running or port conflict

**Solution:**
```bash
# Check if port 7860 is in use
netstat -ano | findstr :7860

# Kill process if needed
taskkill /PID <process_id> /F

# Restart server
python server/app.py
```

### Issue 6: Genetics Not Displaying

**Cause:** Key normalization issue

**Solution:**
- Backend automatically normalizes genetics keys to lowercase
- Check `server/domain/patient.py` lines 199-215
- Verify genetics data in browser console:
  ```javascript
  console.log(window.patientData.genetics)
  ```

## Testing the Complete System

### Test Script

Create `test_cancer_patient_upload.py`:

```python
import requests
import json

# Load cancer patient file
with open('patient_cancer_targeted_therapy.json', 'r') as f:
    patient_data = json.load(f)

# Test backend API
response = requests.post(
    'http://localhost:7860/api/patients/sessions',
    json=patient_data
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Verify session created
assert response.status_code == 200
assert 'session_id' in response.json()
assert response.json()['patient_name'] == 'Sarah Chen'

print("✅ Cancer patient upload test PASSED")
```

Run:
```bash
python test_cancer_patient_upload.py
```

### Manual Verification Steps

1. **Upload File**
   - ✅ Loading screen appears
   - ✅ "PARSING PATIENT DATA..." message
   - ✅ "CREATING PATIENT SESSION..." message
   - ✅ "GENERATING PERSONALIZED RECOMMENDATIONS..." message

2. **Patient Profile Updated**
   - ✅ Name: "Sarah Chen" (not "Unknown Patient")
   - ✅ Age: 52
   - ✅ Condition: "HER2-Positive Breast Cancer"

3. **Genetics Display**
   - ✅ CYP2D6: *1/*4 (Intermediate Metabolizer)
   - ✅ ERBB2: Amplified
   - ✅ PIK3CA: E545K mutation

4. **Drug Recommendations**
   - ✅ Trastuzumab listed
   - ✅ Pertuzumab listed
   - ✅ Alpelisib listed (for PIK3CA mutation)

5. **Molecular Binding Visualization**
   - ✅ Realistic protein ribbons (not simple tubes)
   - ✅ Smooth animations
   - ✅ Drug approaching protein
   - ✅ Binding pocket visible

## Performance Optimization

### Browser Performance
- Clear cache regularly
- Use Chrome/Edge for best WebGL performance
- Close other tabs to free GPU memory

### Server Performance
- Restart server daily
- Monitor memory usage
- Check logs for errors

## Next Steps After Upload

1. **Explore Quantum VOE** (Step 01)
   - Voltage-gated sodium channel simulation
   - Drug binding energy calculations

2. **Review Off-Target Scan** (Step 02)
   - CYP450 interactions
   - Genomic predictions

3. **Check ADMET & BBB** (Step 04)
   - Blood-brain barrier penetration
   - Metabolism predictions

4. **View Drug Matrix** (Step 06)
   - Compare all candidate drugs
   - Safety vs efficacy trade-offs

5. **Analyze TRIBE v2 Brain** (Step 07)
   - Neural activation patterns
   - Hemisphere-specific effects

6. **Study Molecular Binding** (Step 08)
   - Realistic protein-drug interactions
   - Binding pocket dynamics

## Support & Documentation

### Key Files to Review
1. `REALISTIC_MOLECULAR_VISUALIZATION_GUIDE.md` - Visualization details
2. `DYNAMIC_PATIENT_IMPLEMENTATION.md` - Patient system architecture
3. `JSON_UPLOAD_FIX_REPORT.md` - Upload system fixes

### Code References
- Patient Upload: `index.html` lines 3815-3870
- Molecular Binding: `molecular_binding.js` lines 1-776
- Backend API: `server/app.py` lines 300-400
- Patient Domain: `server/domain/patient.py`

---

## Quick Start Summary

```bash
# 1. Start server
cd drug-triage-env
python server/app.py

# 2. Open browser
# Navigate to: http://localhost:7860/quantamed/

# 3. Upload file
# Click "UPLOAD PATIENT JSON"
# Select: patient_cancer_targeted_therapy.json

# 4. Verify
# Patient name should be "Sarah Chen"
# Condition should be "HER2-Positive Breast Cancer"
# Molecular binding should show realistic protein ribbons
```

**The system is ready - just upload the cancer patient file through the UI!**