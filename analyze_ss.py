"""Analyze CA geometry to tune DSSP heuristic."""
import sys, math
sys.path.insert(0, '.')
import numpy as np
from server.protein_structure import _fetch_alphafold_pdb, _parse_pdb_to_residues, parse_fasta, _AA_1TO3

fasta = """>sp|P42212|GFP_AEQVI Green fluorescent protein OS=Aequorea victoria OX=6100 GN=GFP PE=1 SV=1
MSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTL
VTTFSYGVQCFSRYPDHMKQHDFFKSAMPEGYVQERTIFFKDDGNYKTRAEVKFEGDTLV
NRIELKGIDFKEDGNILGHKLEYNYNSHNVYIMADKQKNGIKVNFKIRHNIEDGSVQLAD
HYQQNTPIGDGPVLLPDNHYLSTQSALSKDPNEKRDHMVLLEFVTAAGITHGMDELYK"""

header, sequence = parse_fasta(fasta)

# Get real RCSB PDB (1EMA) which has HELIX/SHEET records
import urllib.request
url = 'https://files.rcsb.org/download/1EMA.pdb'
req = urllib.request.Request(url, headers={'User-Agent': 'QuantaMed/1.0'})
resp = urllib.request.urlopen(req, timeout=15)
pdb_text = resp.read().decode('utf-8')

# Parse HELIX and SHEET records from the real PDB to get ground truth
real_ss = ['C'] * len(sequence)
for line in pdb_text.split('\n'):
    if line.startswith('HELIX'):
        start = int(line[21:25].strip())
        end = int(line[33:37].strip())
        for i in range(start-1, min(end, len(sequence))):
            real_ss[i] = 'H'
    elif line.startswith('SHEET'):
        start = int(line[22:26].strip())
        end = int(line[33:37].strip())
        for i in range(start-1, min(end, len(sequence))):
            real_ss[i] = 'E'

print("Ground truth SS:")
print("".join(real_ss[:60]))
print("".join(real_ss[60:120]))
h_count = real_ss.count('H')
e_count = real_ss.count('E')
c_count = real_ss.count('C')
print(f"H={h_count} ({h_count/len(real_ss)*100:.1f}%) E={e_count} ({e_count/len(real_ss)*100:.1f}%) C={c_count} ({c_count/len(real_ss)*100:.1f}%)")

# Now analyze the AlphaFold CA geometry at known sheet positions
af_pdb = _fetch_alphafold_pdb('P42212')
residues, _ = _parse_pdb_to_residues(af_pdb, sequence)

# Re-add the centroid (undo centering)
all_ca_raw = []
for line in af_pdb.split('\n'):
    if line.startswith('ATOM') and line[12:16].strip() == 'CA' and line[21] == 'A':
        x = float(line[30:38])
        y = float(line[38:46])
        z = float(line[46:54])
        all_ca_raw.append([x, y, z])

cas = np.array(all_ca_raw)
n = len(cas)

print(f"\nAnalyzing {n} CA atoms...")
print("\ni, SS, d_ca(i-1,i+1), angle, d_ca_ca")

for i in range(1, min(n-2, len(real_ss)-2)):
    v1 = cas[i] - cas[i-1]
    v2 = cas[i+1] - cas[i]
    d_ca = np.linalg.norm(cas[i+1] - cas[i-1])
    d_ca_ca = np.linalg.norm(v2)
    cos_a = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    angle = math.degrees(math.acos(np.clip(cos_a, -1, 1)))
    
    if real_ss[i] != 'C':
        print(f"{i:3d} {real_ss[i]} d_ca={d_ca:.2f} angle={angle:.1f} d_ca_ca={d_ca_ca:.2f}")
