"""Test the AlphaFold integration."""
import sys
sys.path.insert(0, '.')
from server.protein_structure import model_protein_from_fasta
import numpy as np

fasta = """>sp|P42212|GFP_AEQVI Green fluorescent protein OS=Aequorea victoria OX=6100 GN=GFP PE=1 SV=1
MSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTL
VTTFSYGVQCFSRYPDHMKQHDFFKSAMPEGYVQERTIFFKDDGNYKTRAEVKFEGDTLV
NRIELKGIDFKEDGNILGHKLEYNYNSHNVYIMADKQKNGIKVNFKIRHNIEDGSVQLAD
HYQQNTPIGDGPVLLPDNHYLSTQSALSKDPNEKRDHMVLLEFVTAAGITHGMDELYK"""

result = model_protein_from_fasta(fasta)
if "error" in result:
    print("Error:", result["error"])
else:
    print("Project ID:", result["project_id"])
    print("Length:", result["length"])
    print("Residues:", len(result["residues"]))
    print("SS composition:", result["ss_composition"])
    tmpl = result["template"]
    print("Template:", tmpl["pdb_id"], "-", tmpl.get("method", "?"))
    print("Source:", tmpl.get("source", "?"))
    cas = np.array([r["atoms"]["CA"] for r in result["residues"]])
    print(f"CA range: x=[{cas[:,0].min():.1f},{cas[:,0].max():.1f}] y=[{cas[:,1].min():.1f},{cas[:,1].max():.1f}] z=[{cas[:,2].min():.1f},{cas[:,2].max():.1f}]")
    span = cas.max(axis=0) - cas.min(axis=0)
    print(f"CA span: {span}")
    print("First 3 residues SS:", "".join(r["ss"] for r in result["residues"][:3]))
    print("Full SS:", result["secondary_structure"][:60])
