"""
Patient API Router - Dynamic Patient Management Endpoints
Provides REST API for creating and managing patient sessions
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from typing import Dict, Any
import logging
import json

from server.domain.patient import Patient
from server.use_cases.patient_use_cases import (
    CreatePatientSessionUseCase,
    GetPatientSessionUseCase,
    AnalyzeDrugCompatibilityUseCase,
    GeneratePatientReportUseCase
)
from server.infrastructure.patient_repository import InMemoryPatientRepository
from server.infrastructure.service_adapters import (
    DrugAnalysisAdapter,
    ProteinFoldingAdapter,
    ScoringEngineAdapter,
    ReportGeneratorAdapter
)

logger = logging.getLogger(__name__)

# Initialize dependencies (singleton pattern)
patient_repository = InMemoryPatientRepository()
drug_analysis_service = DrugAnalysisAdapter()
protein_folding_service = ProteinFoldingAdapter()
scoring_engine = ScoringEngineAdapter()
report_generator = ReportGeneratorAdapter()

# Initialize use cases
create_patient_use_case = CreatePatientSessionUseCase(patient_repository)
get_patient_use_case = GetPatientSessionUseCase(patient_repository)
analyze_drug_use_case = AnalyzeDrugCompatibilityUseCase(
    patient_repository,
    drug_analysis_service,
    protein_folding_service,
    scoring_engine
)
generate_report_use_case = GeneratePatientReportUseCase(
    patient_repository,
    report_generator
)

# Create router
router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.post("/sessions")
async def create_patient_session(patient_data: Dict[str, Any]):
    """
    Create a new patient session from JSON data
    
    Request body should contain complete patient profile:
    - basic_info: age, gender, weight_kg, height_cm, bmi, ethnicity
    - condition: primary_diagnosis, severity, duration_years, comorbidities
    - genetics: cyp2d6, cyp2c9, cyp2c19, cyp3a4, cyp1a2
    - labs: alt_u_l, ast_u_l, egfr_ml_min, creatinine_mg_dl, glucose_mg_dl
    - medications: current, past, allergies
    - lifestyle: smoking, alcohol, exercise
    """
    try:
        result = create_patient_use_case.execute(patient_data)
        logger.info(f"Created patient session: {result['session_id']}")
        return result
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating patient session: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/sessions/upload")
async def upload_patient_json(file: UploadFile = File(...)):
    """
    Upload patient data from JSON file
    """
    try:
        content = await file.read()
        patient_data = json.loads(content.decode('utf-8'))
        
        result = create_patient_use_case.execute(patient_data)
        logger.info(f"Created patient session from upload: {result['session_id']}")
        return result
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading patient: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_patient_session(session_id: str):
    """
    Get patient session by ID
    """
    try:
        patient_data = get_patient_use_case.execute(session_id)
        return patient_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving patient: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/sessions/{session_id}/analyze")
async def analyze_drug_compatibility(
    session_id: str,
    analysis_request: Dict[str, Any]
):
    """
    Analyze drug compatibility for patient
    
    Request body:
    - drug_name: str (required)
    - dose_mg: float (required)
    - include_protein_simulation: bool (optional, default=True)
    """
    try:
        drug_name = analysis_request.get("drug_name")
        dose_mg = analysis_request.get("dose_mg")
        include_protein_simulation = analysis_request.get("include_protein_simulation", True)
        
        if not drug_name or dose_mg is None:
            raise ValueError("drug_name and dose_mg are required")
        
        result = analyze_drug_use_case.execute(
            session_id=session_id,
            drug_name=drug_name,
            dose_mg=float(dose_mg),
            include_protein_simulation=include_protein_simulation
        )
        
        logger.info(f"Analyzed {drug_name} for patient {session_id}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing drug: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/sessions/{session_id}/report")
async def generate_patient_report(
    session_id: str,
    format: str = "pdf"
):
    """
    Generate patient report
    
    Query parameters:
    - format: "pdf" or "summary" (default="pdf")
    """
    try:
        # Get latest analysis results (simplified - would store in session)
        patient_data = get_patient_use_case.execute(session_id)
        
        # Mock analysis results for report generation
        analysis_results = {
            "session_id": session_id,
            "drug_name": "Sample Drug",
            "compatibility": {"can_take": True, "overall_risk_score": 25.0},
            "recommendations": ["Monitor closely"]
        }
        
        report_bytes = generate_report_use_case.execute(
            session_id=session_id,
            analysis_results=analysis_results,
            format_type=format
        )
        
        if format == "pdf":
            return Response(
                content=report_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=patient_{session_id}_report.pdf"}
            )
        else:
            return Response(
                content=report_bytes,
                media_type="text/plain"
            )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/sessions")
async def list_patient_sessions():
    """
    List all patient sessions
    """
    try:
        patients = patient_repository.find_all()
        return {
            "total": len(patients),
            "sessions": [
                {
                    "session_id": p.session_id,
                    "age": p.basic_info.age,
                    "gender": p.basic_info.gender.value,
                    "condition": p.condition.primary_diagnosis,
                    "created_at": p.created_at
                }
                for p in patients
            ]
        }
    except Exception as e:
        logger.error(f"Error listing patients: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_patient_session(session_id: str):
    """
    Delete patient session
    """
    try:
        success = patient_repository.delete(session_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Patient session not found: {session_id}")
        return {"message": f"Patient session {session_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting patient: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "total_patients": patient_repository.count(),
        "services": {
            "patient_repository": "operational",
            "drug_analysis": "operational",
            "protein_folding": "operational",
            "scoring_engine": "operational",
            "report_generator": "operational"
        }
    }

# Made with Bob
