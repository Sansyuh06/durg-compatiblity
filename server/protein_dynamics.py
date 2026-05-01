"""
Protein Dynamics Analysis Module - RMSF, RMSD, PCA Clustering

Implements advanced molecular dynamics analysis for protein folding simulations:
- RMSF (Root Mean Square Fluctuation): Per-residue flexibility analysis
- RMSD (Root Mean Square Deviation): Overall structural stability tracking
- PCA + K-means: Conformational state clustering and cryptic pocket discovery

Based on the methodology from:
- Molecular Dynamics simulations (CHARMM36m force field)
- Principal Component Analysis for conformational sampling
- K-means clustering for state identification
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans


@dataclass
class MDTrajectory:
    """Molecular dynamics trajectory data."""
    timesteps: list[float]  # Time in nanoseconds
    coordinates: np.ndarray  # Shape: (n_frames, n_atoms, 3)
    residue_ids: list[int]
    residue_names: list[str]
    temperature: float = 310.0  # Kelvin (body temperature)
    force_field: str = "CHARMM36m"


@dataclass
class RMSFResult:
    """Root Mean Square Fluctuation analysis result."""
    residue_ids: list[int]
    residue_names: list[str]
    rmsf_values: list[float]  # Ångströms
    flexible_regions: list[tuple[int, int]]  # (start, end) residue indices
    rigid_regions: list[tuple[int, int]]
    mean_rmsf: float
    max_rmsf: float
    max_rmsf_residue: int


@dataclass
class RMSDResult:
    """Root Mean Square Deviation convergence analysis."""
    timesteps: list[float]  # Nanoseconds
    rmsd_values: list[float]  # Ångströms
    converged: bool
    convergence_time: Optional[float]  # ns
    plateau_rmsd: float  # Average RMSD after convergence
    stability_score: float  # 0-1, higher = more stable


@dataclass
class ConformationalCluster:
    """A distinct conformational state identified by clustering."""
    cluster_id: int
    label: str
    population: float  # Fraction of trajectory in this state
    representative_frame: int
    centroid_coords: np.ndarray
    energy_estimate: float
    description: str
    has_cryptic_pocket: bool = False


@dataclass
class PCAResult:
    """Principal Component Analysis result with clustering."""
    pc1_variance: float  # Percentage
    pc2_variance: float
    pc_coordinates: np.ndarray  # Shape: (n_frames, 2) - PC1 vs PC2
    clusters: list[ConformationalCluster]
    n_clusters: int
    trajectory_path: list[tuple[float, float]]  # PC1, PC2 path over time
    cluster_transitions: list[tuple[int, int, float]]  # (from, to, time)


def calculate_rmsf(trajectory: MDTrajectory) -> RMSFResult:
    """
    Calculate Root Mean Square Fluctuation for each residue.
    
    RMSF measures how much each residue fluctuates around its average position
    during the simulation. High RMSF = flexible region (loops, termini).
    Low RMSF = rigid region (helices, sheets, binding sites).
    
    Formula: RMSF_i = sqrt(mean((r_i(t) - <r_i>)^2))
    where r_i(t) is position of residue i at time t, <r_i> is average position.
    """
    coords = trajectory.coordinates  # (n_frames, n_atoms, 3)
    n_frames, n_atoms, _ = coords.shape
    
    # Calculate mean position for each atom
    mean_coords = coords.mean(axis=0)  # (n_atoms, 3)
    
    # Calculate squared deviations from mean
    deviations = coords - mean_coords[np.newaxis, :, :]
    squared_deviations = (deviations ** 2).sum(axis=2)  # (n_frames, n_atoms)
    
    # RMSF = sqrt(mean(squared_deviations))
    rmsf = np.sqrt(squared_deviations.mean(axis=0))  # (n_atoms,)
    
    # Group by residue (assuming 4 backbone atoms per residue: N, CA, C, O)
    atoms_per_residue = 4
    n_residues = n_atoms // atoms_per_residue
    residue_rmsf = []
    
    for i in range(n_residues):
        start_idx = i * atoms_per_residue
        end_idx = start_idx + atoms_per_residue
        # Use CA (alpha carbon) RMSF as representative
        ca_idx = start_idx + 1
        residue_rmsf.append(float(rmsf[ca_idx]))
    
    # Identify flexible vs rigid regions (threshold at mean + 0.5*std)
    mean_rmsf = float(np.mean(residue_rmsf))
    std_rmsf = float(np.std(residue_rmsf))
    threshold = mean_rmsf + 0.5 * std_rmsf
    
    flexible_regions = []
    rigid_regions = []
    
    in_flexible = False
    region_start = 0
    
    for i, val in enumerate(residue_rmsf):
        if val > threshold and not in_flexible:
            in_flexible = True
            region_start = i
        elif val <= threshold and in_flexible:
            flexible_regions.append((region_start, i - 1))
            in_flexible = False
        
        if val <= threshold and i > 0 and residue_rmsf[i-1] <= threshold:
            if not rigid_regions or rigid_regions[-1][1] < i - 1:
                rigid_start = i - 1 if not rigid_regions else rigid_regions[-1][1] + 1
                rigid_regions.append((rigid_start, i))
    
    max_rmsf_idx = int(np.argmax(residue_rmsf))
    
    return RMSFResult(
        residue_ids=trajectory.residue_ids[:n_residues],
        residue_names=trajectory.residue_names[:n_residues],
        rmsf_values=residue_rmsf,
        flexible_regions=flexible_regions,
        rigid_regions=rigid_regions,
        mean_rmsf=mean_rmsf,
        max_rmsf=float(np.max(residue_rmsf)),
        max_rmsf_residue=max_rmsf_idx,
    )


def calculate_rmsd(trajectory: MDTrajectory, reference_frame: int = 0) -> RMSDResult:
    """
    Calculate Root Mean Square Deviation from reference structure over time.
    
    RMSD measures how much the protein structure deviates from a reference
    (usually the starting structure). A stable simulation shows RMSD rising
    initially then plateauing. Continuously rising RMSD = unfolding/unstable.
    
    Formula: RMSD(t) = sqrt(mean((r(t) - r_ref)^2))
    """
    coords = trajectory.coordinates  # (n_frames, n_atoms, 3)
    ref_coords = coords[reference_frame]  # (n_atoms, 3)
    
    rmsd_values = []
    
    for frame_coords in coords:
        # Calculate RMSD for this frame
        diff = frame_coords - ref_coords
        squared_diff = (diff ** 2).sum(axis=1)  # Sum over x,y,z
        rmsd = float(np.sqrt(squared_diff.mean()))
        rmsd_values.append(rmsd)
    
    # Detect convergence: RMSD plateaus when std of last 20% < 0.3 Å
    n_frames = len(rmsd_values)
    last_20_percent = rmsd_values[int(0.8 * n_frames):]
    
    converged = False
    convergence_time = None
    plateau_rmsd = float(np.mean(last_20_percent))
    
    if np.std(last_20_percent) < 0.3:
        converged = True
        # Find convergence time (when RMSD first enters plateau range)
        plateau_range = (plateau_rmsd - 0.5, plateau_rmsd + 0.5)
        for i, rmsd in enumerate(rmsd_values):
            if plateau_range[0] <= rmsd <= plateau_range[1]:
                convergence_time = trajectory.timesteps[i]
                break
    
    # Stability score: 1.0 if converged with low plateau, 0.0 if diverging
    if converged:
        # Lower plateau RMSD = higher stability
        stability_score = max(0.0, min(1.0, 1.0 - (plateau_rmsd / 10.0)))
    else:
        # Penalize non-convergence
        stability_score = 0.3
    
    return RMSDResult(
        timesteps=trajectory.timesteps,
        rmsd_values=rmsd_values,
        converged=converged,
        convergence_time=convergence_time,
        plateau_rmsd=plateau_rmsd,
        stability_score=stability_score,
    )


def perform_pca_clustering(
    trajectory: MDTrajectory,
    n_clusters: int = 5,
    n_components: int = 2,
) -> PCAResult:
    """
    Perform PCA + K-means clustering to identify conformational states.
    
    This is the most advanced analysis - it reduces the high-dimensional
    protein motion to 2D (PC1 vs PC2) and identifies distinct conformational
    clusters. Each cluster represents a major "pose" the protein adopts.
    
    Cryptic pockets are discovered when a cluster shows significantly
    different geometry from the starting structure.
    """
    coords = trajectory.coordinates  # (n_frames, n_atoms, 3)
    n_frames, n_atoms, _ = coords.shape
    
    # Flatten coordinates: (n_frames, n_atoms * 3)
    coords_flat = coords.reshape(n_frames, -1)
    
    # Center the data
    coords_centered = coords_flat - coords_flat.mean(axis=0)
    
    # Perform PCA
    pca = PCA(n_components=n_components)
    pc_coords = pca.fit_transform(coords_centered)  # (n_frames, 2)
    
    # Variance explained by each PC
    pc1_variance = float(pca.explained_variance_ratio_[0] * 100)
    pc2_variance = float(pca.explained_variance_ratio_[1] * 100)
    
    # K-means clustering in PC space
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    cluster_labels = kmeans.fit_predict(pc_coords)
    
    # Build cluster objects
    clusters = []
    for cluster_id in range(n_clusters):
        # Find frames in this cluster
        cluster_mask = cluster_labels == cluster_id
        cluster_frames = np.where(cluster_mask)[0]
        
        if len(cluster_frames) == 0:
            continue
        
        population = float(len(cluster_frames) / n_frames)
        
        # Representative frame: closest to cluster centroid
        centroid = kmeans.cluster_centers_[cluster_id]
        distances = np.linalg.norm(pc_coords[cluster_mask] - centroid, axis=1)
        rep_frame_idx = cluster_frames[np.argmin(distances)]
        
        # Estimate energy (lower PC1 usually = lower energy)
        avg_pc1 = float(pc_coords[cluster_mask, 0].mean())
        energy_estimate = -2.0 - (avg_pc1 / 10.0)  # Arbitrary scaling
        
        # Detect cryptic pocket: cluster far from origin in PC space
        distance_from_origin = float(np.linalg.norm(centroid))
        has_cryptic_pocket = distance_from_origin > 15.0 and population > 0.1
        
        # Generate description
        if cluster_id == 0:
            label = "Closed/Native State"
            description = "Compact native conformation with minimal exposure"
        elif has_cryptic_pocket:
            label = "Open/Cryptic Pocket State"
            description = "Expanded conformation revealing hidden binding site"
        elif population > 0.3:
            label = "Major Intermediate State"
            description = "Frequently visited conformational intermediate"
        else:
            label = f"Minor State {cluster_id}"
            description = "Transient conformational state"
        
        clusters.append(ConformationalCluster(
            cluster_id=cluster_id,
            label=label,
            population=population,
            representative_frame=int(rep_frame_idx),
            centroid_coords=coords[rep_frame_idx],
            energy_estimate=energy_estimate,
            description=description,
            has_cryptic_pocket=has_cryptic_pocket,
        ))
    
    # Sort by population (most common first)
    clusters.sort(key=lambda c: c.population, reverse=True)
    
    # Build trajectory path in PC space
    trajectory_path = [(float(pc_coords[i, 0]), float(pc_coords[i, 1])) 
                       for i in range(n_frames)]
    
    # Detect cluster transitions
    transitions = []
    prev_cluster = cluster_labels[0]
    for i in range(1, n_frames):
        curr_cluster = cluster_labels[i]
        if curr_cluster != prev_cluster:
            transitions.append((int(prev_cluster), int(curr_cluster), 
                              trajectory.timesteps[i]))
            prev_cluster = curr_cluster
    
    return PCAResult(
        pc1_variance=pc1_variance,
        pc2_variance=pc2_variance,
        pc_coordinates=pc_coords,
        clusters=clusters,
        n_clusters=len(clusters),
        trajectory_path=trajectory_path,
        cluster_transitions=transitions,
    )


def generate_md_trajectory(
    sequence: str,
    n_frames: int = 100,
    duration_ns: float = 100.0,
    temperature: float = 310.0,
) -> MDTrajectory:
    """
    Generate a simulated MD trajectory for a protein sequence.
    
    This is a simplified simulation for demonstration. In production,
    this would interface with GROMACS, AMBER, or NAMD.
    """
    n_residues = len(sequence)
    atoms_per_residue = 4  # N, CA, C, O
    n_atoms = n_residues * atoms_per_residue
    
    # Use sequence hash for reproducibility
    seed = int(hashlib.md5(sequence.encode()).hexdigest()[:8], 16) % (2**31)
    rng = np.random.RandomState(seed)
    
    # Generate initial structure (extended chain)
    initial_coords = np.zeros((n_atoms, 3))
    for i in range(n_residues):
        base_idx = i * atoms_per_residue
        # Place residues along x-axis with slight randomization
        x = i * 3.8 + rng.randn() * 0.5
        y = rng.randn() * 0.3
        z = rng.randn() * 0.3
        
        # N, CA, C, O atoms
        initial_coords[base_idx] = [x - 0.5, y, z]
        initial_coords[base_idx + 1] = [x, y, z]  # CA
        initial_coords[base_idx + 2] = [x + 0.5, y, z]
        initial_coords[base_idx + 3] = [x + 0.7, y + 0.5, z]
    
    # Generate trajectory: protein gradually folds and fluctuates
    timesteps = np.linspace(0, duration_ns, n_frames).tolist()
    coordinates = np.zeros((n_frames, n_atoms, 3))
    
    for frame_idx in range(n_frames):
        t = frame_idx / n_frames  # 0 to 1
        
        # Folding progress: gradually compact the structure
        fold_factor = 1.0 - 0.6 * (1.0 - np.exp(-t * 3.0))
        
        # Add thermal fluctuations (decreases as structure stabilizes)
        fluctuation_amplitude = 2.0 * np.exp(-t * 2.0) + 0.5
        
        frame_coords = initial_coords.copy()
        
        # Apply folding (pull towards center)
        center = frame_coords.mean(axis=0)
        frame_coords = center + (frame_coords - center) * fold_factor
        
        # Add random fluctuations
        frame_coords += rng.randn(n_atoms, 3) * fluctuation_amplitude
        
        # Add residue-specific flexibility (loops more flexible)
        for i in range(n_residues):
            base_idx = i * atoms_per_residue
            # Termini and middle regions more flexible
            flexibility = 1.0 if (i < 3 or i > n_residues - 4 or 
                                 abs(i - n_residues//2) < 3) else 0.3
            frame_coords[base_idx:base_idx+4] += rng.randn(4, 3) * flexibility
        
        coordinates[frame_idx] = frame_coords
    
    residue_ids = list(range(n_residues))
    residue_names = [f"{sequence[i]}{i+1}" for i in range(n_residues)]
    
    return MDTrajectory(
        timesteps=timesteps,
        coordinates=coordinates,
        residue_ids=residue_ids,
        residue_names=residue_names,
        temperature=temperature,
        force_field="CHARMM36m",
    )


def analyze_protein_dynamics(
    sequence: str,
    n_frames: int = 100,
    duration_ns: float = 100.0,
) -> dict[str, Any]:
    """
    Complete protein dynamics analysis pipeline.
    
    Returns all three analyses: RMSF, RMSD, and PCA clustering.
    """
    # Generate trajectory
    trajectory = generate_md_trajectory(sequence, n_frames, duration_ns)
    
    # Run analyses
    rmsf_result = calculate_rmsf(trajectory)
    rmsd_result = calculate_rmsd(trajectory)
    pca_result = perform_pca_clustering(trajectory, n_clusters=5)
    
    return {
        "sequence": sequence,
        "n_residues": len(sequence),
        "duration_ns": duration_ns,
        "n_frames": n_frames,
        "temperature_k": trajectory.temperature,
        "force_field": trajectory.force_field,
        "rmsf": {
            "residue_ids": rmsf_result.residue_ids,
            "residue_names": rmsf_result.residue_names,
            "values": rmsf_result.rmsf_values,
            "mean": rmsf_result.mean_rmsf,
            "max": rmsf_result.max_rmsf,
            "max_residue": rmsf_result.max_rmsf_residue,
            "flexible_regions": rmsf_result.flexible_regions,
            "rigid_regions": rmsf_result.rigid_regions,
        },
        "rmsd": {
            "timesteps": rmsd_result.timesteps,
            "values": rmsd_result.rmsd_values,
            "converged": rmsd_result.converged,
            "convergence_time_ns": rmsd_result.convergence_time,
            "plateau_rmsd": rmsd_result.plateau_rmsd,
            "stability_score": rmsd_result.stability_score,
        },
        "pca": {
            "pc1_variance_pct": pca_result.pc1_variance,
            "pc2_variance_pct": pca_result.pc2_variance,
            "n_clusters": pca_result.n_clusters,
            "trajectory_path": pca_result.trajectory_path,
            "clusters": [
                {
                    "id": c.cluster_id,
                    "label": c.label,
                    "population": c.population,
                    "representative_frame": c.representative_frame,
                    "energy_ev": c.energy_estimate,
                    "description": c.description,
                    "has_cryptic_pocket": c.has_cryptic_pocket,
                }
                for c in pca_result.clusters
            ],
            "transitions": [
                {"from": t[0], "to": t[1], "time_ns": t[2]}
                for t in pca_result.cluster_transitions
            ],
        },
    }

# Made with Bob
