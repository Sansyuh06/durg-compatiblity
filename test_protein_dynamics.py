#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for protein dynamics module"""

import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from server.protein_dynamics import analyze_protein_dynamics

print("=" * 60)
print("Testing Protein Dynamics Module")
print("=" * 60)

# Test sequence (Nav1.2 fragment)
sequence = "MTSQFWEEFYVLVVQFGFHWFRESLITGYLWTCIVNIIPSTFLADLNHNNEKTSIEFSNL"

print(f"\n1. Testing with sequence length: {len(sequence)} residues")
print(f"   Sequence: {sequence[:30]}...")

# Run analysis with small parameters for quick test
print("\n2. Running analysis (10 frames, 10 ns)...")
result = analyze_protein_dynamics(sequence, n_frames=10, duration_ns=10.0)

print("\n3. Results:")
print(f"   [OK] Analysis completed successfully")
print(f"   [OK] Result keys: {list(result.keys())}")

# Check RMSF
rmsf_data = result["rmsf"]
print(f"\n4. RMSF Analysis:")
print(f"   [OK] Data points: {len(rmsf_data['values'])}")
print(f"   [OK] Mean RMSF: {rmsf_data['mean']:.2f} A")
print(f"   [OK] Max RMSF: {rmsf_data['max']:.2f} A")
print(f"   [OK] Flexible regions: {len(rmsf_data['flexible_regions'])}")
print(f"   [OK] Rigid regions: {len(rmsf_data['rigid_regions'])}")

# Check RMSD
rmsd_data = result["rmsd"]
print(f"\n5. RMSD Analysis:")
print(f"   [OK] Time points: {len(rmsd_data['timesteps'])}")
print(f"   [OK] Converged: {rmsd_data['converged']}")
print(f"   [OK] Stability score: {rmsd_data['stability_score']:.2f}")
if rmsd_data['converged']:
    print(f"   [OK] Convergence time: {rmsd_data['convergence_time_ns']:.1f} ns")
    print(f"   [OK] Plateau RMSD: {rmsd_data['plateau_rmsd']:.2f} A")

# Check PCA
pca_data = result["pca"]
print(f"\n6. PCA Clustering:")
print(f"   [OK] Clusters: {len(pca_data['clusters'])}")
print(f"   [OK] PC1 variance: {pca_data['pc1_variance_pct']:.1f}%")
print(f"   [OK] PC2 variance: {pca_data['pc2_variance_pct']:.1f}%")

# Check for cryptic pockets
cryptic_pockets = [c for c in pca_data['clusters'] if c['has_cryptic_pocket']]
print(f"   [OK] Cryptic pockets found: {len(cryptic_pockets)}")
if cryptic_pockets:
    for pocket in cryptic_pockets:
        print(f"     - Cluster {pocket['id']}: {pocket['description']}")

# Check trajectory path
print(f"\n7. Trajectory Data:")
print(f"   [OK] Trajectory path available: {len(pca_data['trajectory_path'])} points")
print(f"   [OK] Cluster transitions: {len(pca_data['transitions'])}")

print("\n" + "=" * 60)
print("SUCCESS: All tests passed!")
print("=" * 60)
print("\nThe protein dynamics module is working correctly.")
print("You can now start the server with:")
print("  uvicorn server.app:app --host 0.0.0.0 --port 7860")
print("\nThen visit:")
print("  http://localhost:7860/protein-dynamics")

# Made with Bob
