"""
Protein Structure Generator — SWISS-MODEL-inspired homology modeling simulation.

Takes a FASTA sequence and produces:
- 3D backbone + side-chain atom coordinates
- Secondary structure assignment (helix / sheet / coil)
- Quality metrics (GMQE, QMEAN, Ramachandran)
- Template matching information
- Drug docking coordinates

This is a hackathon-grade simulation that produces visually convincing
protein structures for the Three.js viewer. Not for scientific use.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Any

import numpy as np


# ── Amino acid properties ──────────────────────────────────────────────

_AA_1TO3 = {
    "A": "ALA", "R": "ARG", "N": "ASN", "D": "ASP", "C": "CYS",
    "E": "GLU", "Q": "GLN", "G": "GLY", "H": "HIS", "I": "ILE",
    "L": "LEU", "K": "LYS", "M": "MET", "F": "PHE", "P": "PRO",
    "S": "SER", "T": "THR", "W": "TRP", "Y": "TYR", "V": "VAL",
}

_AA_COLORS = {
    "A": "#C8C8C8", "R": "#145AFF", "N": "#00DCDC", "D": "#E60A0A",
    "C": "#E6E600", "E": "#E60A0A", "Q": "#00DCDC", "G": "#EBEBEB",
    "H": "#8282D2", "I": "#0F820F", "L": "#0F820F", "K": "#145AFF",
    "M": "#E6E600", "F": "#3232AA", "P": "#DC9682", "S": "#FA9600",
    "T": "#FA9600", "W": "#B45AB4", "Y": "#3232AA", "V": "#0F820F",
}

# Chou-Fasman propensities (simplified)
_HELIX_PROPENSITY = {
    "A": 1.42, "R": 0.98, "N": 0.67, "D": 1.01, "C": 0.70,
    "E": 1.51, "Q": 1.11, "G": 0.57, "H": 1.00, "I": 1.08,
    "L": 1.21, "K": 1.16, "M": 1.45, "F": 1.13, "P": 0.57,
    "S": 0.77, "T": 0.83, "W": 1.08, "Y": 0.69, "V": 1.06,
}

_SHEET_PROPENSITY = {
    "A": 0.83, "R": 0.93, "N": 0.89, "D": 0.54, "C": 1.19,
    "E": 0.37, "Q": 1.10, "G": 0.75, "H": 0.87, "I": 1.60,
    "L": 1.30, "K": 0.74, "M": 1.05, "F": 1.38, "P": 0.55,
    "S": 0.75, "T": 1.19, "W": 1.37, "Y": 1.47, "V": 1.70,
}


# ── FASTA parser ───────────────────────────────────────────────────────

def parse_fasta(fasta_text: str) -> tuple[str, str]:
    """Parse FASTA input and return (header, sequence)."""
    lines = fasta_text.strip().split("\n")
    header = ""
    seq_parts = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            header = line[1:].strip()
        else:
            seq_parts.append(re.sub(r"[^A-Za-z]", "", line).upper())
    sequence = "".join(seq_parts)
    # Filter to valid amino acids
    sequence = "".join(c for c in sequence if c in _AA_1TO3)
    return header, sequence


def _extract_protein_info(header: str) -> dict[str, str]:
    """Extract protein name, organism, gene from a FASTA header."""
    info = {"name": "Unknown Protein", "organism": "", "gene": ""}
    # Try UniProt format: sp|P01308|INS_HUMAN Insulin OS=Homo sapiens ...
    m = re.match(r"(?:sp|tr)\|([A-Z0-9]+)\|(\S+)\s+(.*)", header)
    if m:
        info["accession"] = m.group(1)
        info["entry"] = m.group(2)
        rest = m.group(3)
        # Extract name (before OS=)
        nm = re.match(r"(.+?)\s+OS=", rest)
        if nm:
            info["name"] = nm.group(1)
        om = re.search(r"OS=(.+?)(?:\s+OX=|\s+GN=|\s+PE=|$)", rest)
        if om:
            info["organism"] = om.group(1).strip()
        gm = re.search(r"GN=(\S+)", rest)
        if gm:
            info["gene"] = gm.group(1)
        return info
    # Fallback: use full header as name
    if header:
        info["name"] = header[:80]
    return info


# ── Secondary structure prediction ─────────────────────────────────────

def predict_secondary_structure(sequence: str) -> list[str]:
    """
    Simplified Chou-Fasman secondary structure prediction.

    Returns a list of 'H' (helix), 'E' (sheet), 'C' (coil) per residue.
    """
    n = len(sequence)
    if n == 0:
        return []

    ss = ["C"] * n
    window = 6

    # Pass 1: Find helix nucleation sites
    for i in range(n - window + 1):
        segment = sequence[i : i + window]
        helix_score = sum(_HELIX_PROPENSITY.get(c, 1.0) for c in segment) / window
        if helix_score > 1.03:
            for j in range(i, min(i + window, n)):
                if ss[j] == "C":
                    ss[j] = "H"

    # Pass 2: Extend helices
    for i in range(1, n - 1):
        if ss[i] == "C" and ss[i - 1] == "H" and i + 1 < n and ss[i + 1] == "H":
            if _HELIX_PROPENSITY.get(sequence[i], 1.0) > 0.9:
                ss[i] = "H"

    # Pass 3: Find sheet nucleation sites (only in coil regions)
    for i in range(n - 4):
        segment = sequence[i : i + 5]
        sheet_score = sum(_SHEET_PROPENSITY.get(c, 1.0) for c in segment) / 5
        if sheet_score > 1.05:
            for j in range(i, min(i + 5, n)):
                if ss[j] == "C":
                    ss[j] = "E"

    # Pass 4: Remove short runs (< 3 residues)
    result = list(ss)
    i = 0
    while i < n:
        j = i
        while j < n and result[j] == result[i]:
            j += 1
        run_len = j - i
        if run_len < 3 and result[i] != "C":
            for k in range(i, j):
                result[k] = "C"
        i = j

    # Proline breaks helices
    for i in range(n):
        if sequence[i] == "P" and result[i] == "H":
            result[i] = "C"

    return result


# ── 3D coordinate generation ──────────────────────────────────────────

def _generate_backbone(sequence: str, ss: list[str]) -> list[dict[str, Any]]:
    """
    Generate 3D backbone coordinates (N, CA, C, O atoms per residue).

    Uses ideal geometry:
    - Alpha helix: phi=-57°, psi=-47°, 3.6 residues/turn, rise 1.5Å
    - Beta sheet: phi=-135°, psi=+135°, rise 3.3Å
    - Coil: phi=-60°, psi=-30° with slight randomization
    """
    n = len(sequence)
    if n == 0:
        return []

    # Use deterministic seed from sequence hash
    seed = int(hashlib.md5(sequence.encode()).hexdigest()[:8], 16) % (2**31)
    rng = np.random.RandomState(seed)

    # Bond lengths and angles (Å)
    N_CA = 1.47
    CA_C = 1.52
    C_O = 1.24

    residues: list[dict[str, Any]] = []

    for i in range(n):
        aa = sequence[i]
        sec = ss[i]

        # Parameters based on secondary structure
        if sec == "H":
            # Alpha helix: 3.6 residues per turn, rise 1.5Å per residue
            turn_angle = 2 * math.pi / 3.6
            rise = 1.5
            radius = 2.3
            theta = i * turn_angle
            x = radius * math.cos(theta)
            y = i * rise
            z = radius * math.sin(theta)
            ca_pos = np.array([x, y, z])
        elif sec == "E":
            # Beta sheet: extended, slight zigzag
            x = i * 3.3
            y = (i % 2) * 0.8 - 0.4
            z = rng.uniform(-0.3, 0.3)
            ca_pos = np.array([x, y, z])
        else:
            # Coil: semi-random walk with reasonable geometry
            if i == 0:
                ca_pos = np.array([0.0, 0.0, 0.0])
            else:
                prev_ca = residues[-1]["atoms"]["CA"]
                # Random direction but keeping chain connected
                phi = rng.uniform(-math.pi, math.pi)
                psi = rng.uniform(-math.pi / 2, math.pi / 2)
                dx = 3.8 * math.cos(phi) * math.cos(psi)
                dy = 3.8 * math.sin(phi)
                dz = 3.8 * math.cos(phi) * math.sin(psi)
                ca_pos = np.array([
                    prev_ca[0] + dx,
                    prev_ca[1] + dy,
                    prev_ca[2] + dz,
                ])

        # Generate N, C, O from CA position
        if i > 0:
            prev_c = np.array(residues[-1]["atoms"]["C"])
            n_dir = ca_pos - prev_c
            n_dir = n_dir / (np.linalg.norm(n_dir) + 1e-9)
            n_pos = ca_pos - n_dir * N_CA
        else:
            n_pos = ca_pos - np.array([N_CA, 0, 0])

        # C atom
        if i < n - 1:
            c_offset = rng.randn(3) * 0.3
            c_offset[0] += CA_C
            c_pos = ca_pos + c_offset / (np.linalg.norm(c_offset) + 1e-9) * CA_C
        else:
            c_pos = ca_pos + np.array([CA_C, 0, 0])

        # O atom (perpendicular to CA-C bond)
        ca_c_dir = c_pos - ca_pos
        ca_c_dir = ca_c_dir / (np.linalg.norm(ca_c_dir) + 1e-9)
        perp = np.cross(ca_c_dir, np.array([0, 1, 0]))
        if np.linalg.norm(perp) < 0.1:
            perp = np.cross(ca_c_dir, np.array([1, 0, 0]))
        perp = perp / (np.linalg.norm(perp) + 1e-9)
        o_pos = c_pos + perp * C_O

        # Side chain CB (simplified - single atom)
        ca_n_dir = n_pos - ca_pos
        ca_n_dir = ca_n_dir / (np.linalg.norm(ca_n_dir) + 1e-9)
        cb_dir = np.cross(ca_c_dir, ca_n_dir)
        cb_dir = cb_dir / (np.linalg.norm(cb_dir) + 1e-9)
        cb_pos = ca_pos + cb_dir * 1.52 if aa != "G" else None

        atoms = {
            "N": n_pos.tolist(),
            "CA": ca_pos.tolist(),
            "C": c_pos.tolist(),
            "O": o_pos.tolist(),
        }
        if cb_pos is not None:
            atoms["CB"] = cb_pos.tolist()

        residues.append({
            "index": i,
            "aa1": aa,
            "aa3": _AA_1TO3.get(aa, "UNK"),
            "color": _AA_COLORS.get(aa, "#808080"),
            "ss": sec,
            "atoms": atoms,
        })

    # Center the structure at origin
    all_ca = np.array([r["atoms"]["CA"] for r in residues])
    center = all_ca.mean(axis=0)
    for r in residues:
        for atom_name in r["atoms"]:
            r["atoms"][atom_name] = [
                round(r["atoms"][atom_name][0] - center[0], 3),
                round(r["atoms"][atom_name][1] - center[1], 3),
                round(r["atoms"][atom_name][2] - center[2], 3),
            ]

    return residues


# ── Quality metrics ────────────────────────────────────────────────────

def _compute_quality_metrics(
    sequence: str, ss: list[str], seed: int
) -> dict[str, Any]:
    """Generate realistic-looking quality metrics."""
    rng = np.random.RandomState(seed)
    n = len(sequence)

    # GMQE (0-1): Global Model Quality Estimation
    # Longer sequences with more secondary structure → higher quality
    ss_pct = sum(1 for s in ss if s != "C") / max(1, n)
    gmqe = min(0.95, max(0.25, 0.55 + ss_pct * 0.3 + rng.uniform(-0.08, 0.08)))

    # QMEAN scores (-4 to 0, closer to 0 is better)
    qmean_global = round(-0.5 - rng.uniform(0, 2.5), 2)
    qmean_local = [
        round(max(-4, min(0, -0.3 - rng.uniform(0, 1.5))), 2)
        for _ in range(n)
    ]

    # Ramachandran distribution
    favored = round(rng.uniform(85, 96), 1)
    allowed = round(rng.uniform(2, 10), 1)
    outlier = round(100 - favored - allowed, 1)

    # Sequence identity to "template"
    seq_identity = round(rng.uniform(30, 100), 1)

    # Coverage
    coverage = round(rng.uniform(0.75, 1.0), 2)

    return {
        "gmqe": round(gmqe, 2),
        "qmean": {
            "global": qmean_global,
            "local": qmean_local,
            "z_score": round(qmean_global * 0.8 + rng.uniform(-0.3, 0.3), 2),
        },
        "ramachandran": {
            "favored": favored,
            "allowed": allowed,
            "outlier": max(0, outlier),
        },
        "molprobity": round(rng.uniform(1.0, 2.8), 2),
        "clash_score": round(rng.uniform(0.5, 15.0), 1),
        "rotamer_outliers": round(rng.uniform(0.5, 5.0), 1),
        "seq_identity": seq_identity,
        "coverage": coverage,
    }


# ── Template matching ──────────────────────────────────────────────────

_KNOWN_TEMPLATES = {
    "INS": {
        "pdb_id": "6GV0",
        "name": "Insulin",
        "chain": "A",
        "resolution": 1.95,
        "method": "X-Ray Diffraction",
        "organism": "Homo sapiens",
    },
    "NAV": {
        "pdb_id": "6J8E",
        "name": "Nav1.2 Voltage-Gated Sodium Channel",
        "chain": "A",
        "resolution": 3.0,
        "method": "Cryo-EM",
        "organism": "Rattus norvegicus",
    },
    "HERG": {
        "pdb_id": "5VA2",
        "name": "hERG Potassium Channel",
        "chain": "A",
        "resolution": 3.8,
        "method": "Cryo-EM",
        "organism": "Homo sapiens",
    },
    "AR": {
        "pdb_id": "1E3G",
        "name": "Androgen Receptor LBD",
        "chain": "A",
        "resolution": 2.4,
        "method": "X-Ray Diffraction",
        "organism": "Homo sapiens",
    },
}


def _find_template(header: str, sequence: str, seed: int) -> dict[str, Any]:
    """Find a matching template (or generate a plausible one)."""
    rng = np.random.RandomState(seed)

    # Check known proteins
    header_upper = header.upper()
    for key, tmpl in _KNOWN_TEMPLATES.items():
        if key in header_upper:
            return {
                "pdb_id": tmpl["pdb_id"],
                "name": tmpl["name"],
                "chain": tmpl["chain"],
                "resolution": tmpl["resolution"],
                "method": tmpl["method"],
                "organism": tmpl["organism"],
                "seq_identity": round(rng.uniform(65, 100), 1),
                "coverage": round(rng.uniform(0.85, 1.0), 2),
                "source": "PDB",
            }

    # Generate a plausible template
    fake_pdb = f"{rng.randint(1, 9)}{chr(rng.randint(65, 90))}{chr(rng.randint(65, 90))}{rng.randint(0, 9)}"
    return {
        "pdb_id": fake_pdb,
        "name": "AlphaFold DB model",
        "chain": "A",
        "resolution": None,
        "method": "AlphaFold v2 Prediction",
        "organism": "Predicted",
        "seq_identity": round(rng.uniform(30, 85), 1),
        "coverage": round(rng.uniform(0.7, 1.0), 2),
        "source": "AlphaFoldDB",
    }


# ── Drug docking positions ────────────────────────────────────────────

def _generate_docking_data(
    residues: list[dict], sequence: str, seed: int
) -> list[dict[str, Any]]:
    """Generate drug docking positions relative to the protein structure."""
    rng = np.random.RandomState(seed + 42)
    n = len(residues)
    if n < 5:
        return []

    # Find the binding pocket (cluster of hydrophobic residues)
    hydrophobic = set("AILMFVWP")
    pocket_center = None
    best_score = 0

    for i in range(2, n - 2):
        window = sequence[max(0, i - 2) : min(n, i + 3)]
        score = sum(1 for c in window if c in hydrophobic)
        if score > best_score:
            best_score = score
            pocket_center = i

    if pocket_center is None:
        pocket_center = n // 2

    pocket_ca = np.array(residues[pocket_center]["atoms"]["CA"])

    drugs: list[dict[str, Any]] = [
        {
            "drug_id": "ltg",
            "label": "Lamotrigine",
            "color": "#00e676",
            "binding_energy": -8.4 + rng.uniform(-1, 1),
            "atoms": _generate_drug_atoms(pocket_ca, rng, "ltg"),
        },
        {
            "drug_id": "vpa",
            "label": "Valproic Acid",
            "color": "#ffab40",
            "binding_energy": -6.2 + rng.uniform(-1, 1),
            "atoms": _generate_drug_atoms(pocket_ca + np.array([3, 0, 0]), rng, "vpa"),
        },
    ]

    for d in drugs:
        d["binding_energy"] = round(float(d["binding_energy"]), 2)
        d["pocket_residues"] = [
            {
                "index": residues[j]["index"],
                "aa3": residues[j]["aa3"],
                "interaction": rng.choice(["H-bond", "Hydrophobic", "Van der Waals", "Pi-stacking"]),
                "distance": round(rng.uniform(2.0, 4.5), 1),
            }
            for j in range(max(0, pocket_center - 3), min(n, pocket_center + 4))
        ]

    return drugs


def _generate_drug_atoms(
    center: np.ndarray, rng: np.random.RandomState, drug_id: str
) -> list[dict[str, Any]]:
    """Generate simplified drug molecule atoms around a center point."""
    if drug_id == "ltg":
        # Lamotrigine: triazine ring + dichlorophenyl
        atoms = []
        # Ring 1 (triazine)
        for k in range(6):
            angle = k * math.pi / 3
            atoms.append({
                "element": "N" if k % 2 == 0 else "C",
                "x": round(center[0] + 1.4 * math.cos(angle), 3),
                "y": round(center[1] + 1.4 * math.sin(angle), 3),
                "z": round(center[2] + rng.uniform(-0.2, 0.2), 3),
            })
        # Ring 2 (phenyl)
        for k in range(6):
            angle = k * math.pi / 3
            atoms.append({
                "element": "Cl" if k in (2, 4) else "C",
                "x": round(center[0] + 3.5 + 1.4 * math.cos(angle), 3),
                "y": round(center[1] + 1.4 * math.sin(angle), 3),
                "z": round(center[2] + rng.uniform(-0.2, 0.2), 3),
            })
        # Amino groups
        atoms.append({"element": "N", "x": round(center[0] - 1.8, 3), "y": round(center[1] + 0.5, 3), "z": round(center[2], 3)})
        atoms.append({"element": "N", "x": round(center[0] - 1.8, 3), "y": round(center[1] - 1.2, 3), "z": round(center[2], 3)})
        return atoms
    else:
        # Valproic acid: branched chain carboxylic acid
        atoms = [
            {"element": "C", "x": round(center[0], 3), "y": round(center[1], 3), "z": round(center[2], 3)},
            {"element": "O", "x": round(center[0] - 1.2, 3), "y": round(center[1] + 0.8, 3), "z": round(center[2], 3)},
            {"element": "O", "x": round(center[0] - 1.2, 3), "y": round(center[1] - 0.8, 3), "z": round(center[2], 3)},
        ]
        # Propyl chains
        for branch in [1, -1]:
            for k in range(1, 4):
                atoms.append({
                    "element": "C",
                    "x": round(center[0] + k * 1.54, 3),
                    "y": round(center[1] + branch * (0.5 + k * 0.3), 3),
                    "z": round(center[2] + rng.uniform(-0.3, 0.3), 3),
                })
        return atoms


# ── Main API ───────────────────────────────────────────────────────────

@dataclass
class ProteinModelResult:
    """Full result of a protein modeling run."""
    project_id: str
    header: str
    protein_info: dict[str, str]
    sequence: str
    length: int
    secondary_structure: list[str]
    residues: list[dict[str, Any]]
    quality: dict[str, Any]
    template: dict[str, Any]
    docking: list[dict[str, Any]]
    status: str = "completed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "status": self.status,
            "header": self.header,
            "protein_info": self.protein_info,
            "sequence": self.sequence,
            "length": self.length,
            "secondary_structure": "".join(self.secondary_structure),
            "ss_composition": {
                "helix": round(self.secondary_structure.count("H") / max(1, self.length) * 100, 1),
                "sheet": round(self.secondary_structure.count("E") / max(1, self.length) * 100, 1),
                "coil": round(self.secondary_structure.count("C") / max(1, self.length) * 100, 1),
            },
            "residues": self.residues,
            "quality": self.quality,
            "template": self.template,
            "docking": self.docking,
        }


def model_protein_from_fasta(fasta_text: str) -> dict[str, Any]:
    """
    Main entry point: takes FASTA text and returns a full protein model.

    Simulates the SWISS-MODEL pipeline:
    1. Parse FASTA sequence
    2. Predict secondary structure
    3. Generate 3D coordinates
    4. Compute quality metrics
    5. Find template match
    6. Generate drug docking data
    """
    header, sequence = parse_fasta(fasta_text)
    if not sequence:
        return {"error": "No valid amino acid sequence found in FASTA input."}
    if len(sequence) < 5:
        return {"error": "Sequence too short — minimum 5 residues required."}
    if len(sequence) > 2000:
        return {"error": "Sequence too long — maximum 2000 residues for demo."}

    # Generate deterministic project ID
    seq_hash = hashlib.md5(sequence.encode()).hexdigest()[:8]
    project_id = f"QM{seq_hash.upper()}"
    seed = int(seq_hash, 16) % (2**31)

    # Pipeline
    protein_info = _extract_protein_info(header)
    ss = predict_secondary_structure(sequence)
    residues = _generate_backbone(sequence, ss)
    quality = _compute_quality_metrics(sequence, ss, seed)
    template = _find_template(header, sequence, seed)
    docking = _generate_docking_data(residues, sequence, seed)

    result = ProteinModelResult(
        project_id=project_id,
        header=header,
        protein_info=protein_info,
        sequence=sequence,
        length=len(sequence),
        secondary_structure=ss,
        residues=residues,
        quality=quality,
        template=template,
        docking=docking,
    )

    return result.to_dict()


# ── Pre-built examples ─────────────────────────────────────────────────

EXAMPLE_SEQUENCES = {
    "insulin": """>sp|P01308|INS_HUMAN Insulin OS=Homo sapiens OX=9606 GN=INS PE=1 SV=1
MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAED
LQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN""",

    "nav1.2": """>Nav1.2_binding_pocket SCN2A Voltage-gated sodium channel fragment
MTSQFWEEFYVLVVQFGFHWFRESLITGYLWTCIVNIIPSTFLADLNHNNEKTSIEFSNL
SAVYGNLLILLMSSHYALISDIFHVTFEYLYIMVYTLAELSF""",

    "androgen_receptor": """>sp|P10275|ANDR_HUMAN Androgen receptor LBD OS=Homo sapiens GN=AR
LLQQQQQQQQQQQQQQQQQQQQQETSPRQQQQQQGEDGSPSNAAQELAKYGVSKRYKCLQS
SSTLKLPEQLQEMQNQLYSAL""",

    "herg_channel": """>hERG_K_channel KCNH2 potassium channel fragment
MMGAGEEALVAYGSDEQPVVFDMRKLLGSVWQFSSALRLSQSEAMRQAHYRPVDGAMFPI
CGHLANFRNQNQLATIFPELIAIPVFSNIHSLAYVFVIISVL""",
}


def get_example_sequences() -> dict[str, str]:
    """Return available example FASTA sequences."""
    return {k: v for k, v in EXAMPLE_SEQUENCES.items()}
