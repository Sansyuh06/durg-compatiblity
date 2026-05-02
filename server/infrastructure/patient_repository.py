"""
In-Memory Patient Repository
Implements IPatientRepository for session-based storage
"""
from typing import Optional, List, Dict
import logging

from server.domain.patient import Patient
from server.domain.interfaces import IPatientRepository

logger = logging.getLogger(__name__)


class InMemoryPatientRepository(IPatientRepository):
    """
    In-memory implementation of patient repository
    Stores patients in a dictionary keyed by session_id
    """
    
    def __init__(self):
        self._patients: Dict[str, Patient] = {}
        logger.info("Initialized InMemoryPatientRepository")
    
    def save(self, patient: Patient) -> None:
        """Save or update patient"""
        self._patients[patient.session_id] = patient
        logger.info(f"Saved patient: {patient.session_id}")
    
    def find_by_session_id(self, session_id: str) -> Optional[Patient]:
        """Find patient by session ID"""
        patient = self._patients.get(session_id)
        if patient:
            logger.debug(f"Found patient: {session_id}")
        else:
            logger.debug(f"Patient not found: {session_id}")
        return patient
    
    def find_all(self) -> List[Patient]:
        """Get all patients"""
        patients = list(self._patients.values())
        logger.debug(f"Retrieved {len(patients)} patients")
        return patients
    
    def delete(self, session_id: str) -> bool:
        """Delete patient by session ID"""
        if session_id in self._patients:
            del self._patients[session_id]
            logger.info(f"Deleted patient: {session_id}")
            return True
        logger.warning(f"Cannot delete - patient not found: {session_id}")
        return False
    
    def count(self) -> int:
        """Get total number of patients"""
        return len(self._patients)
    
    def clear(self) -> None:
        """Clear all patients (for testing)"""
        count = len(self._patients)
        self._patients.clear()
        logger.info(f"Cleared {count} patients from repository")

# Made with Bob
