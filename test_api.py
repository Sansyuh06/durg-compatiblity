import httpx

BASE = "http://127.0.0.1:7860"

# Test 1: Gabi recommendations
print("=" * 60)
print("TEST 1: Recommendations for Gabi (juvenile_myoclonic_epilepsy)")
print("=" * 60)
r = httpx.get(f"{BASE}/api/quantamed/recommendations", params={"patient": "juvenile_myoclonic_epilepsy"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(f"Patient: {d['patient_name']} ({d['condition']})")
    for i, x in enumerate(d["recommendations"]):
        s = x["scores"]
        print(f"  {i+1}. {x['label']:20s}  composite={s['composite']:.4f}  eff={s['efficacy']}  safe={s['safety']}  bbb={s['bbb']}")
else:
    print(f"ERROR: {r.text}")

# Test 2: PK for VPA
print()
print("=" * 60)
print("TEST 2: PK curve for VPA (Gabi's CYP2C9 intermediate)")
print("=" * 60)
r = httpx.get(f"{BASE}/api/quantamed/pk", params={"drug": "vpa", "daily_dose_mg": 1000, "cyp2c9": "intermediate"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    derived = d["derived"]
    print(f"  Cavg: {derived['cavg_ug_ml']:.1f} ug/mL")
    print(f"  Cmax: {derived['cmax_ug_ml']:.1f} ug/mL")
    print(f"  Cmin: {derived['cmin_ug_ml']:.1f} ug/mL")
    print(f"  Status: {derived['status']}")

# Test 3: PK for ZNS (new drug)
print()
print("=" * 60)
print("TEST 3: PK curve for ZNS (Zonisamide)")
print("=" * 60)
r = httpx.get(f"{BASE}/api/quantamed/pk", params={"drug": "zns", "daily_dose_mg": 300, "cyp2c9": "normal"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    derived = d["derived"]
    print(f"  Cavg: {derived['cavg_ug_ml']:.1f} ug/mL")
    print(f"  Status: {derived['status']}")

# Test 4: VQE demo
print()
print("=" * 60)
print("TEST 4: VQE convergence payload")
print("=" * 60)
r = httpx.get(f"{BASE}/api/quantamed/vqe")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(f"  Datasets: {len(d['datasets'])} drugs")
    for ds in d["datasets"]:
        print(f"    - {ds['label']:25s}  final_energy={ds['data'][-1]:.4f}")

# Test 5: Protein folding
print()
print("=" * 60)
print("TEST 5: Protein folding simulation")
print("=" * 60)
r = httpx.get(f"{BASE}/api/quantamed/protein-folding")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(f"  Backend: {d.get('backend', 'unknown')}")
    print(f"  Bitstring: {d.get('bitstring', 'N/A')}")
    print(f"  Energy: {d.get('energy_ev', 'N/A')}")
    print(f"  Frames: {len(d.get('frames', []))}")

# Test 6: PDF report
print()
print("=" * 60)
print("TEST 6: PDF report generation")
print("=" * 60)
r = httpx.get(f"{BASE}/api/quantamed/report", params={"patient": "juvenile_myoclonic_epilepsy"})
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('content-type', 'N/A')}")
print(f"PDF size: {len(r.content)} bytes")
if r.content[:5] == b"%PDF-":
    print("  Valid PDF header detected!")

print()
print("ALL TESTS COMPLETE")
