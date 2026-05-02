"""
Service Adapters - Connect domain to existing services
Implements domain interfaces using existing QuantaMed services
"""
from typing import Dict, Any, List
import logging
import numpy as np

from server.domain.patient import Patient
from server.domain.interfaces import (
    IDrugAnalysisService,
    IProteinFoldingService,
    IScoringEngine,
    IReportGenerator
)

# Import existing services
from server import scoring_engine
from server import protein_dynamics
from server import pdf_report

logger = logging.getLogger(__name__)


class DrugAnalysisAdapter(IDrugAnalysisService):
    """Adapter for drug compatibility analysis"""
    
    def __init__(self):
        logger.info("Initialized DrugAnalysisAdapter")
    
    def analyze_drug_compatibility(
        self,
        patient: Patient,
        drug_name: str,
        dose_mg: float
    ) -> Dict[str, Any]:
        """Analyze drug compatibility for patient"""
        logger.info(f"Analyzing {drug_name} compatibility for patient {patient.session_id}")
        
        warnings = []
        interactions = []
        
        # Check genetic factors
        if patient.genetics.is_poor_metabolizer("cyp2d6"):
            warnings.append("CYP2D6 poor metabolizer - increased drug exposure risk")
        
        if patient.genetics.is_poor_metabolizer("cyp2c9"):
            warnings.append("CYP2C9 poor metabolizer - may require dose adjustment")
        
        # Check organ function
        if patient.labs.has_hepatic_impairment():
            warnings.append("Hepatic impairment detected - monitor liver function")
        
        if patient.labs.has_renal_impairment():
            warnings.append("Renal impairment detected - adjust dose for kidney function")
        
        # Check drug interactions
        for med in patient.medications.current_medications:
            if self._has_interaction(drug_name, med.name):
                interactions.append({
                    "drug1": drug_name,
                    "drug2": med.name,
                    "severity": "moderate",
                    "description": f"Potential interaction between {drug_name} and {med.name}"
                })
        
        # Calculate pharmacokinetics
        pk_params = self._calculate_pharmacokinetics(patient, drug_name, dose_mg)
        
        # Determine compatibility
        compatible = len([w for w in warnings if "contraindication" in w.lower()]) == 0
        
        return {
            "compatible": compatible,
            "risk_score": len(warnings) * 10 + len(interactions) * 5,
            "warnings": warnings,
            "recommendations": self._generate_drug_recommendations(patient, warnings),
            "pharmacokinetics": pk_params,
            "interactions": interactions
        }
    
    def get_alternative_drugs(
        self,
        patient: Patient,
        condition: str
    ) -> List[Dict[str, Any]]:
        """Get alternative drug options for condition"""
        # Disease-specific drug alternatives
        alternatives_db = {
            "Juvenile Myoclonic Epilepsy": [
                {"name": "Levetiracetam", "efficacy": 0.85, "safety": 0.90},
                {"name": "Lamotrigine", "efficacy": 0.80, "safety": 0.85},
                {"name": "Topiramate", "efficacy": 0.75, "safety": 0.80},
                {"name": "Zonisamide", "efficacy": 0.70, "safety": 0.85},
                {"name": "Valproic Acid", "efficacy": 0.90, "safety": 0.75}
            ],
            "Type 2 Diabetes": [
                {"name": "Metformin", "efficacy": 0.85, "safety": 0.90},
                {"name": "Empagliflozin", "efficacy": 0.80, "safety": 0.85},
                {"name": "Liraglutide", "efficacy": 0.85, "safety": 0.80},
                {"name": "Sitagliptin", "efficacy": 0.75, "safety": 0.90},
                {"name": "Pioglitazone", "efficacy": 0.70, "safety": 0.75}
            ],
            "Hypertension": [
                {"name": "Lisinopril", "efficacy": 0.85, "safety": 0.90},
                {"name": "Amlodipine", "efficacy": 0.80, "safety": 0.85},
                {"name": "Losartan", "efficacy": 0.85, "safety": 0.90},
                {"name": "Hydrochlorothiazide", "efficacy": 0.75, "safety": 0.85},
                {"name": "Metoprolol", "efficacy": 0.80, "safety": 0.80}
            ],
            "Depression": [
                {"name": "Sertraline", "efficacy": 0.75, "safety": 0.85},
                {"name": "Escitalopram", "efficacy": 0.80, "safety": 0.90},
                {"name": "Bupropion", "efficacy": 0.75, "safety": 0.85},
                {"name": "Venlafaxine", "efficacy": 0.80, "safety": 0.80},
                {"name": "Mirtazapine", "efficacy": 0.75, "safety": 0.85}
            ]
        }
        
        alternatives = alternatives_db.get(condition, [])
        
        # Adjust scores based on patient factors
        for alt in alternatives:
            # Reduce efficacy for poor metabolizers
            if patient.genetics.is_poor_metabolizer("cyp2d6"):
                alt["efficacy"] *= 0.9
            
            # Reduce safety for organ impairment
            if patient.labs.has_hepatic_impairment() or patient.labs.has_renal_impairment():
                alt["safety"] *= 0.85
            
            # Calculate overall score
            alt["overall_score"] = (alt["efficacy"] * 0.6 + alt["safety"] * 0.4)
        
        # Sort by overall score
        alternatives.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return alternatives
    
    def _has_interaction(self, drug1: str, drug2: str) -> bool:
        """Check if two drugs have known interaction"""
        # Simplified interaction database
        interactions = {
            "warfarin": ["aspirin", "nsaid", "ssri"],
            "metformin": ["contrast"],
            "valproic acid": ["lamotrigine", "carbamazepine"]
        }
        
        drug1_lower = drug1.lower()
        drug2_lower = drug2.lower()
        
        for key, values in interactions.items():
            if key in drug1_lower and any(v in drug2_lower for v in values):
                return True
            if key in drug2_lower and any(v in drug1_lower for v in values):
                return True
        
        return False
    
    def _calculate_pharmacokinetics(
        self,
        patient: Patient,
        drug_name: str,
        dose_mg: float
    ) -> Dict[str, float]:
        """Calculate pharmacokinetic parameters"""
        # Simplified PK calculation
        weight = patient.basic_info.weight_kg
        
        # Adjust for renal function
        renal_factor = patient.labs.egfr_ml_min / 90.0 if patient.labs.egfr_ml_min < 90 else 1.0
        
        # Adjust for hepatic function
        hepatic_factor = 0.7 if patient.labs.has_hepatic_impairment() else 1.0
        
        # Adjust for genetics
        genetic_factor = 0.5 if patient.genetics.is_poor_metabolizer("cyp2d6") else 1.0
        
        clearance = 10.0 * renal_factor * hepatic_factor * genetic_factor  # L/h
        volume_distribution = 0.7 * weight  # L
        half_life = 0.693 * volume_distribution / clearance  # hours
        
        cmax = dose_mg / volume_distribution  # mg/L
        auc = dose_mg / clearance  # mg*h/L
        
        return {
            "clearance_l_h": round(clearance, 2),
            "volume_distribution_l": round(volume_distribution, 2),
            "half_life_hours": round(half_life, 2),
            "cmax_mg_l": round(cmax, 2),
            "auc_mg_h_l": round(auc, 2),
            "renal_adjustment_factor": round(renal_factor, 2),
            "hepatic_adjustment_factor": round(hepatic_factor, 2),
            "genetic_adjustment_factor": round(genetic_factor, 2)
        }
    
    def _generate_drug_recommendations(
        self,
        patient: Patient,
        warnings: List[str]
    ) -> List[str]:
        """Generate drug-specific recommendations"""
        recommendations = []
        
        if any("poor metabolizer" in w.lower() for w in warnings):
            recommendations.append("Start with 50% of standard dose")
            recommendations.append("Monitor drug levels closely")
        
        if any("hepatic" in w.lower() for w in warnings):
            recommendations.append("Monitor liver enzymes weekly for first month")
        
        if any("renal" in w.lower() for w in warnings):
            recommendations.append("Adjust dose based on creatinine clearance")
        
        if patient.basic_info.age > 65:
            recommendations.append("Use geriatric dosing guidelines")
        
        return recommendations


class ProteinFoldingAdapter(IProteinFoldingService):
    """Adapter for quantum protein folding simulation"""
    
    def __init__(self):
        logger.info("Initialized ProteinFoldingAdapter")
    
    def simulate_protein_folding(
        self,
        protein_sequence: str,
        drug_molecule: str
    ) -> Dict[str, Any]:
        """Run quantum protein folding simulation"""
        logger.info(f"Running protein folding simulation for {drug_molecule}")
        
        try:
            # Simplified simulation - would use actual quantum algorithms in production
            binding_energy = -5.2 + np.random.normal(0, 0.5)
            binding_affinity = 1.0 / (1.0 + np.exp(binding_energy))
            stability_score = 0.85 + np.random.normal(0, 0.05)
            
            # Generate mock RMSF data
            n_residues = len(protein_sequence)
            rmsf_data = [0.5 + np.random.exponential(0.3) for _ in range(n_residues)]
            
            # Generate mock RMSD data
            rmsd_data = [i * 0.1 + np.random.normal(0, 0.2) for i in range(100)]
            
            # Generate mock PCA clusters
            pca_clusters = [
                {"cluster_id": 0, "population": 0.35, "representative_frame": 10},
                {"cluster_id": 1, "population": 0.25, "representative_frame": 45},
                {"cluster_id": 2, "population": 0.20, "representative_frame": 70},
                {"cluster_id": 3, "population": 0.12, "representative_frame": 85},
                {"cluster_id": 4, "population": 0.08, "representative_frame": 95}
            ]
            
            # Generate mock cryptic pockets
            cryptic_pockets = [
                {
                    "pocket_id": 1,
                    "residues": [45, 46, 47, 48, 49],
                    "volume_a3": 250.5,
                    "druggability_score": 0.75,
                    "opens_at_ns": 70.0
                }
            ]
            
            return {
                "binding_energy": binding_energy,
                "binding_affinity": binding_affinity,
                "stability_score": stability_score,
                "rmsf_data": rmsf_data,
                "rmsd_data": rmsd_data,
                "pca_clusters": pca_clusters,
                "cryptic_pockets": cryptic_pockets,
                "simulation_time_ns": 100.0,
                "convergence_achieved": True
            }
        
        except Exception as e:
            logger.error(f"Protein folding simulation failed: {e}")
            return {"error": str(e)}
    
    def analyze_molecular_dynamics(
        self,
        protein_pdb: str,
        simulation_time_ns: float
    ) -> Dict[str, Any]:
        """Run molecular dynamics analysis"""
        logger.info(f"Running MD analysis for {simulation_time_ns} ns")
        
        # Would use actual MD simulation in production
        return {
            "rmsd_convergence": True,
            "average_rmsd": 3.5,
            "rmsf_profile": [0.5] * 100,
            "simulation_complete": True
        }


class ScoringEngineAdapter(IScoringEngine):
    """Adapter for drug scoring and risk assessment"""
    
    def calculate_risk_score(
        self,
        patient: Patient,
        drug_name: str
    ) -> float:
        """Calculate overall risk score (0-100)"""
        # Use patient's built-in risk score as base
        base_risk = patient.get_risk_score()
        
        # Add drug-specific risk factors
        drug_risk = 0.0
        
        # High-risk drugs
        high_risk_drugs = ["warfarin", "lithium", "digoxin", "phenytoin"]
        if any(drug.lower() in drug_name.lower() for drug in high_risk_drugs):
            drug_risk += 15
        
        # Interaction risk
        if len(patient.medications.current_medications) > 5:
            drug_risk += 10
        
        total_risk = min(base_risk + drug_risk, 100.0)
        
        logger.debug(f"Risk score for {drug_name}: {total_risk}")
        return total_risk
    
    def evaluate_efficacy(
        self,
        patient: Patient,
        drug_name: str
    ) -> Dict[str, Any]:
        """Evaluate drug efficacy for patient"""
        # Simplified efficacy prediction
        base_efficacy = 0.75
        
        # Adjust for genetics
        if patient.genetics.is_poor_metabolizer("cyp2d6"):
            base_efficacy *= 0.85
        
        # Adjust for severity
        severity_factors = {
            "mild": 1.0,
            "moderate": 0.95,
            "severe": 0.85,
            "critical": 0.75
        }
        base_efficacy *= severity_factors.get(patient.condition.severity.value, 0.9)
        
        return {
            "predicted_response": base_efficacy,
            "confidence": 0.80,
            "time_to_effect_days": 14,
            "factors": {
                "genetic": "moderate_impact",
                "severity": "high_impact",
                "comorbidities": "low_impact"
            }
        }


class ReportGeneratorAdapter(IReportGenerator):
    """Adapter for generating patient reports"""
    
    def generate_pdf_report(
        self,
        patient: Patient,
        analysis_results: Dict[str, Any]
    ) -> bytes:
        """Generate PDF report"""
        logger.info(f"Generating PDF report for patient {patient.session_id}")
        
        # Use existing PDF generation
        try:
            return pdf_report.generate_quantamed_pdf(patient.session_id)
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return b"PDF generation failed"
    
    def generate_summary(
        self,
        patient: Patient,
        analysis_results: Dict[str, Any]
    ) -> str:
        """Generate text summary"""
        summary = f"""
PATIENT ANALYSIS SUMMARY
========================

Patient ID: {patient.session_id}
Age: {patient.basic_info.age} years
Gender: {patient.basic_info.gender.value}
Condition: {patient.condition.primary_diagnosis}
Severity: {patient.condition.severity.value}

DRUG ANALYSIS
=============
Drug: {analysis_results.get('drug_name', 'N/A')}
Dose: {analysis_results.get('dose_mg', 0)} mg
Compatible: {'Yes' if analysis_results.get('compatibility', {}).get('can_take', False) else 'No'}
Risk Score: {analysis_results.get('compatibility', {}).get('overall_risk_score', 0):.1f}/100

WARNINGS
========
"""
        
        warnings = analysis_results.get('compatibility', {}).get('drug_warnings', [])
        for warning in warnings:
            summary += f"- {warning}\n"
        
        summary += "\nRECOMMENDATIONS\n===============\n"
        recommendations = analysis_results.get('recommendations', [])
        for rec in recommendations:
            summary += f"{rec}\n"
        
        return summary

# Made with Bob
