"""
Domain Interfaces (Ports)
Define contracts for external dependencies using Hexagonal Architecture
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from .patient import Patient


class IPatientRepository(ABC):
    """Port for patient data persistence"""
    
    @abstractmethod
    def save(self, patient: Patient) -> None:
        """Save or update patient"""
        pass
    
    @abstractmethod
    def find_by_session_id(self, session_id: str) -> Optional[Patient]:
        """Find patient by session ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Patient]:
        """Get all patients"""
        pass
    
    @abstractmethod
    def delete(self, session_id: str) -> bool:
        """Delete patient by session ID"""
        pass


class IDrugAnalysisService(ABC):
    """Port for drug compatibility analysis"""
    
    @abstractmethod
    def analyze_drug_compatibility(
        self,
        patient: Patient,
        drug_name: str,
        dose_mg: float
    ) -> Dict[str, Any]:
        """
        Analyze drug compatibility for patient
        Returns: {
            "compatible": bool,
            "risk_score": float,
            "warnings": List[str],
            "recommendations": List[str],
            "pharmacokinetics": Dict,
            "interactions": List[Dict]
        }
        """
        pass
    
    @abstractmethod
    def get_alternative_drugs(
        self,
        patient: Patient,
        condition: str
    ) -> List[Dict[str, Any]]:
        """Get alternative drug options for condition"""
        pass


class IProteinFoldingService(ABC):
    """Port for quantum protein folding simulation"""
    
    @abstractmethod
    def simulate_protein_folding(
        self,
        protein_sequence: str,
        drug_molecule: str
    ) -> Dict[str, Any]:
        """
        Run quantum protein folding simulation
        Returns: {
            "binding_energy": float,
            "binding_affinity": float,
            "stability_score": float,
            "rmsf_data": List[float],
            "rmsd_data": List[float],
            "pca_clusters": List[Dict],
            "cryptic_pockets": List[Dict]
        }
        """
        pass
    
    @abstractmethod
    def analyze_molecular_dynamics(
        self,
        protein_pdb: str,
        simulation_time_ns: float
    ) -> Dict[str, Any]:
        """Run molecular dynamics analysis"""
        pass


class IScoringEngine(ABC):
    """Port for drug scoring and risk assessment"""
    
    @abstractmethod
    def calculate_risk_score(
        self,
        patient: Patient,
        drug_name: str
    ) -> float:
        """Calculate overall risk score (0-100)"""
        pass
    
    @abstractmethod
    def evaluate_efficacy(
        self,
        patient: Patient,
        drug_name: str
    ) -> Dict[str, Any]:
        """Evaluate drug efficacy for patient"""
        pass


class IReportGenerator(ABC):
    """Port for generating patient reports"""
    
    @abstractmethod
    def generate_pdf_report(
        self,
        patient: Patient,
        analysis_results: Dict[str, Any]
    ) -> bytes:
        """Generate PDF report"""
        pass
    
    @abstractmethod
    def generate_summary(
        self,
        patient: Patient,
        analysis_results: Dict[str, Any]
    ) -> str:
        """Generate text summary"""
        pass

# Made with Bob
