# Dynamic Patient Management System - Implementation Plan

## Problem Statement

**Current Issue**: The QuantaMed application is hardcoded to show a single "Custom Patient" (GABI_PRESET) with Valproic Acid and PCOS. Every user sees the same patient data regardless of their actual medical profile.

**Required Solution**: Transform the system into a dynamic, multi-patient platform where each user can:
1. Upload their own patient JSON file
2. Manually enter patient information through an intake wizard
3. Receive personalized drug compatibility analysis based on their unique profile
4. Support multiple diseases beyond just epilepsy/PCOS

## Architecture Overview

Using **Clean Architecture** + **Hexagonal Architecture** + **Domain-Driven Design** patterns from the agents directory to build a maintainable, scalable solution.

### Core Principles
- **Dependency Inversion**: Business logic independent of frameworks
- **Ports & Adapters**: Swappable implementations (in-memory, database, file storage)
- **Domain-Driven Design**: Patient as aggregate root with rich business logic
- **Session Management**: Each user session maintains its own patient context

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ JSON Upload  │  │ Manual Intake│  │ Session UI   │      │
│  │  Component   │  │    Wizard    │  │   Display    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Use Cases (Business Logic)              │   │
│  │  • CreatePatientSession                              │   │
│  │  • AnalyzePatientDrugCompatibility                   │   │
│  │  • GeneratePersonalizedReport                        │   │
│  │  • UpdatePatientProfile                              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Patient    │  │  DrugProfile │  │   Analysis   │      │
│  │  (Aggregate) │  │   (Entity)   │  │ (Value Obj)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Domain Interfaces (Ports)                  │   │
│  │  • IPatientRepository                                │   │
│  │  • IDrugAnalysisService                              │   │
│  │  • IProteinFoldingService                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  In-Memory   │  │   File-Based │  │   Database   │      │
│  │  Repository  │  │  Repository  │  │  Repository  │      │
│  │  (Session)   │  │   (JSON)     │  │  (Future)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Domain Layer (Core Business Logic)

#### 1.1 Patient Aggregate Root
**File**: `drug-triage-env/server/domain/patient.py`

```python
@dataclass
class Patient:
    """Aggregate root: Patient with complete medical profile."""
    id: str
    session_id: str
    basic_info: BasicInfo
    condition: Condition
    genetics: Genetics
    labs: Labs
    medications: Medications
    created_at: datetime
    
    def can_take_drug(self, drug_id: str) -> bool:
        """Business rule: Check if patient can take drug."""
        # Check allergies
        if drug_id in self.medications.allergies:
            return False
        # Check contraindications based on condition
        # Check drug interactions
        return True
    
    def get_recommended_drugs(self) -> List[str]:
        """Business rule: Get drugs suitable for patient's condition."""
        # Based on primary diagnosis, genetics, labs
        pass
    
    def calculate_risk_score(self) -> float:
        """Business rule: Calculate overall risk score."""
        # Combine liver, kidney, genetic factors
        pass
```

#### 1.2 Domain Interfaces (Ports)
**File**: `drug-triage-env/server/domain/interfaces.py`

```python
class IPatientRepository(ABC):
    """Port: Patient data access."""
    @abstractmethod
    async def save(self, patient: Patient) -> Patient:
        pass
    
    @abstractmethod
    async def find_by_session(self, session_id: str) -> Optional[Patient]:
        pass
    
    @abstractmethod
    async def delete(self, patient_id: str) -> bool:
        pass

class IDrugAnalysisService(ABC):
    """Port: Drug compatibility analysis."""
    @abstractmethod
    async def analyze_compatibility(
        self, patient: Patient, drug_id: str
    ) -> DrugAnalysisResult:
        pass

class IProteinFoldingService(ABC):
    """Port: Protein folding simulation."""
    @abstractmethod
    async def simulate_folding(
        self, sequence: str, patient: Patient
    ) -> ProteinFoldingResult:
        pass
```

### Phase 2: Use Cases (Application Logic)

#### 2.1 Create Patient Session
**File**: `drug-triage-env/server/use_cases/create_patient_session.py`

```python
class CreatePatientSessionUseCase:
    """Use case: Create new patient session from JSON or manual input."""
    
    def __init__(
        self,
        patient_repository: IPatientRepository,
        session_manager: ISessionManager
    ):
        self.patients = patient_repository
        self.sessions = session_manager
    
    async def execute(
        self, request: CreatePatientRequest
    ) -> CreatePatientResponse:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Build patient from input
        patient = Patient(
            id=str(uuid.uuid4()),
            session_id=session_id,
            basic_info=request.basic_info,
            condition=request.condition,
            genetics=request.genetics,
            labs=request.labs,
            medications=request.medications,
            created_at=datetime.now()
        )
        
        # Validate patient data
        if not patient.is_valid():
            return CreatePatientResponse(
                success=False,
                error="Invalid patient data"
            )
        
        # Save to repository
        saved_patient = await self.patients.save(patient)
        
        # Create session
        await self.sessions.create(session_id, saved_patient.id)
        
        return CreatePatientResponse(
            success=True,
            patient=saved_patient,
            session_id=session_id
        )
```

#### 2.2 Analyze Patient Drug Compatibility
**File**: `drug-triage-env/server/use_cases/analyze_drug_compatibility.py`

```python
class AnalyzeDrugCompatibilityUseCase:
    """Use case: Analyze drug compatibility for specific patient."""
    
    def __init__(
        self,
        patient_repository: IPatientRepository,
        drug_analysis_service: IDrugAnalysisService,
        protein_folding_service: IProteinFoldingService
    ):
        self.patients = patient_repository
        self.drug_analysis = drug_analysis_service
        self.protein_folding = protein_folding_service
    
    async def execute(
        self, request: AnalyzeDrugRequest
    ) -> AnalyzeDrugResponse:
        # Get patient from session
        patient = await self.patients.find_by_session(request.session_id)
        if not patient:
            return AnalyzeDrugResponse(
                success=False,
                error="Patient not found"
            )
        
        # Run drug compatibility analysis
        compatibility = await self.drug_analysis.analyze_compatibility(
            patient, request.drug_id
        )
        
        # Run protein folding simulation
        folding = await self.protein_folding.simulate_folding(
            request.protein_sequence, patient
        )
        
        # Generate personalized report
        report = self._generate_report(patient, compatibility, folding)
        
        return AnalyzeDrugResponse(
            success=True,
            patient=patient,
            compatibility=compatibility,
            folding=folding,
            report=report
        )
```

### Phase 3: Infrastructure Layer (Adapters)

#### 3.1 In-Memory Patient Repository (Session-Based)
**File**: `drug-triage-env/server/adapters/repositories/memory_patient_repository.py`

```python
class InMemoryPatientRepository(IPatientRepository):
    """Adapter: In-memory storage for patient sessions."""
    
    def __init__(self):
        self._patients: Dict[str, Patient] = {}
        self._session_index: Dict[str, str] = {}  # session_id -> patient_id
    
    async def save(self, patient: Patient) -> Patient:
        self._patients[patient.id] = patient
        self._session_index[patient.session_id] = patient.id
        return patient
    
    async def find_by_session(self, session_id: str) -> Optional[Patient]:
        patient_id = self._session_index.get(session_id)
        if not patient_id:
            return None
        return self._patients.get(patient_id)
    
    async def delete(self, patient_id: str) -> bool:
        if patient_id in self._patients:
            patient = self._patients[patient_id]
            del self._patients[patient_id]
            del self._session_index[patient.session_id]
            return True
        return False
```

#### 3.2 Drug Analysis Service Adapter
**File**: `drug-triage-env/server/adapters/services/drug_analysis_adapter.py`

```python
class DrugAnalysisAdapter(IDrugAnalysisService):
    """Adapter: Connects to existing scoring_engine."""
    
    async def analyze_compatibility(
        self, patient: Patient, drug_id: str
    ) -> DrugAnalysisResult:
        # Use existing scoring_engine functions
        analysis = await run_full_analysis(
            patient_dict=asdict(patient),
            drug_id=drug_id
        )
        
        return DrugAnalysisResult(
            drug_id=drug_id,
            compatibility_score=analysis["score"],
            warnings=analysis["warnings"],
            recommendations=analysis["recommendations"],
            pk_curve=analysis["pk_curve"],
            binding_energy=analysis["binding_energy"]
        )
```

### Phase 4: API Layer (Controllers)

#### 4.1 Patient Session Controller
**File**: `drug-triage-env/server/api/patient_controller.py`

```python
router = APIRouter(prefix="/api/patients", tags=["patients"])

@router.post("/sessions")
async def create_patient_session(
    dto: CreatePatientDTO,
    use_case: CreatePatientSessionUseCase = Depends(get_create_patient_use_case)
):
    """Create new patient session from JSON or manual input."""
    request = CreatePatientRequest(
        basic_info=dto.basic_info,
        condition=dto.condition,
        genetics=dto.genetics,
        labs=dto.labs,
        medications=dto.medications
    )
    
    response = await use_case.execute(request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error)
    
    return {
        "session_id": response.session_id,
        "patient_id": response.patient.id,
        "message": "Patient session created successfully"
    }

@router.get("/sessions/{session_id}")
async def get_patient_session(
    session_id: str,
    patient_repo: IPatientRepository = Depends(get_patient_repository)
):
    """Get patient data for session."""
    patient = await patient_repo.find_by_session(session_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"patient": asdict(patient)}

@router.post("/sessions/{session_id}/analyze")
async def analyze_patient_drugs(
    session_id: str,
    dto: AnalyzeDrugDTO,
    use_case: AnalyzeDrugCompatibilityUseCase = Depends(get_analyze_drug_use_case)
):
    """Analyze drug compatibility for patient session."""
    request = AnalyzeDrugRequest(
        session_id=session_id,
        drug_id=dto.drug_id,
        protein_sequence=dto.protein_sequence
    )
    
    response = await use_case.execute(request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error)
    
    return {
        "compatibility": response.compatibility,
        "folding": response.folding,
        "report": response.report
    }
```

### Phase 5: Frontend Integration

#### 5.1 Enhanced Patient Intake Wizard
**File**: `drug-triage-env/server/quantamed/intake.js` (Enhanced)

```javascript
// Session management
let currentSessionId = null;

async function submitPatientData(formData) {
    try {
        // Create patient session
        const response = await fetch('/api/patients/sessions', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        currentSessionId = data.session_id;
        
        // Store session ID in localStorage
        localStorage.setItem('quantamed_session_id', currentSessionId);
        
        // Navigate to analysis dashboard
        showAnalysisDashboard(currentSessionId);
    } catch (error) {
        console.error('Error creating patient session:', error);
        alert('Failed to create patient session');
    }
}

async function loadPatientFromJSON(file) {
    const reader = new FileReader();
    reader.onload = async (e) => {
        try {
            const patientData = JSON.parse(e.target.result);
            
            // Create session with uploaded data
            const response = await fetch('/api/patients/sessions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(patientData)
            });
            
            const data = await response.json();
            currentSessionId = data.session_id;
            localStorage.setItem('quantamed_session_id', currentSessionId);
            
            showAnalysisDashboard(currentSessionId);
        } catch (error) {
            console.error('Error loading patient JSON:', error);
            alert('Invalid patient JSON file');
        }
    };
    reader.readAsText(file);
}

async function analyzeCurrentPatient(drugId) {
    if (!currentSessionId) {
        alert('No active patient session');
        return;
    }
    
    try {
        const response = await fetch(
            `/api/patients/sessions/${currentSessionId}/analyze`,
            {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    drug_id: drugId,
                    protein_sequence: 'MTSQ...'  // From drug target
                })
            }
        );
        
        const analysis = await response.json();
        displayAnalysisResults(analysis);
    } catch (error) {
        console.error('Error analyzing patient:', error);
        alert('Analysis failed');
    }
}
```

#### 5.2 Dynamic Dashboard Updates
**File**: `drug-triage-env/server/quantamed/index.html` (Enhanced)

```html
<!-- Session indicator -->
<div id="session-indicator" class="session-info">
    <span id="patient-name">No Active Session</span>
    <button onclick="startNewSession()">New Patient</button>
</div>

<!-- Patient profile card (dynamic) -->
<div id="patient-profile-card" class="profile-card">
    <h3 id="profile-name">Loading...</h3>
    <div id="profile-details">
        <p><strong>Age:</strong> <span id="profile-age"></span></p>
        <p><strong>Condition:</strong> <span id="profile-condition"></span></p>
        <p><strong>Genetics:</strong> <span id="profile-genetics"></span></p>
    </div>
</div>

<script>
// Load patient profile on page load
window.addEventListener('DOMContentLoaded', async () => {
    const sessionId = localStorage.getItem('quantamed_session_id');
    if (sessionId) {
        await loadPatientProfile(sessionId);
    } else {
        showPatientIntakeScreen();
    }
});

async function loadPatientProfile(sessionId) {
    try {
        const response = await fetch(`/api/patients/sessions/${sessionId}`);
        const data = await response.json();
        
        // Update UI with patient data
        document.getElementById('patient-name').textContent = 
            `${data.patient.basic_info.gender}, ${data.patient.basic_info.age}y`;
        document.getElementById('profile-age').textContent = 
            data.patient.basic_info.age;
        document.getElementById('profile-condition').textContent = 
            data.patient.condition.primary_diagnosis;
        document.getElementById('profile-genetics').textContent = 
            `CYP2D6: ${data.patient.genetics.cyp2d6}`;
        
        // Enable analysis features
        enableAnalysisFeatures();
    } catch (error) {
        console.error('Error loading patient profile:', error);
        showPatientIntakeScreen();
    }
}
</script>
```

## Multi-Disease Support

### Disease-Specific Analysis Pipelines

```python
# drug-triage-env/server/domain/disease_profiles.py

DISEASE_PROFILES = {
    "epilepsy": {
        "drug_classes": ["anticonvulsants"],
        "target_proteins": ["Nav1.2", "GABA-A"],
        "key_labs": ["liver_function", "kidney_function"],
        "genetic_markers": ["CYP2C9", "CYP2C19"]
    },
    "diabetes": {
        "drug_classes": ["antidiabetics", "insulin"],
        "target_proteins": ["GLUT4", "insulin_receptor"],
        "key_labs": ["glucose", "hba1c", "kidney_function"],
        "genetic_markers": ["CYP2C9"]
    },
    "hypertension": {
        "drug_classes": ["antihypertensives", "diuretics"],
        "target_proteins": ["ACE", "AT1_receptor"],
        "key_labs": ["kidney_function", "electrolytes"],
        "genetic_markers": ["CYP2D6", "CYP3A4"]
    },
    "depression": {
        "drug_classes": ["antidepressants", "ssri"],
        "target_proteins": ["SERT", "5HT2A"],
        "key_labs": ["liver_function"],
        "genetic_markers": ["CYP2D6", "CYP2C19"]
    }
}

def get_disease_specific_analysis(patient: Patient) -> DiseaseAnalysis:
    """Get disease-specific analysis pipeline."""
    disease = patient.condition.primary_diagnosis.lower()
    profile = DISEASE_PROFILES.get(disease, DISEASE_PROFILES["epilepsy"])
    
    return DiseaseAnalysis(
        disease=disease,
        recommended_drug_classes=profile["drug_classes"],
        target_proteins=profile["target_proteins"],
        required_labs=profile["key_labs"],
        genetic_markers=profile["genetic_markers"]
    )
```

## Testing Strategy

### Test Patient Profiles

```python
# drug-triage-env/tests/test_patients/

# Patient 1: Epilepsy (existing)
EPILEPSY_PATIENT = {...}

# Patient 2: Type 2 Diabetes
DIABETES_PATIENT = {
    "basic_info": {"age": 55, "gender": "male", "weight_kg": 95},
    "condition": {"primary_diagnosis": "Type 2 Diabetes"},
    "genetics": {"cyp2c9": "normal_metabolizer"},
    "labs": {"glucose": 180, "hba1c": 8.5}
}

# Patient 3: Hypertension
HYPERTENSION_PATIENT = {
    "basic_info": {"age": 62, "gender": "female", "weight_kg": 70},
    "condition": {"primary_diagnosis": "Hypertension"},
    "genetics": {"cyp2d6": "intermediate_metabolizer"},
    "labs": {"kidney_egfr": 55}
}
```

## Implementation Timeline

### Week 1: Domain & Use Cases
- [ ] Create domain layer (Patient aggregate, interfaces)
- [ ] Implement use cases (CreatePatientSession, AnalyzeDrugCompatibility)
- [ ] Write unit tests for business logic

### Week 2: Infrastructure & API
- [ ] Build in-memory repository
- [ ] Create service adapters
- [ ] Implement API controllers
- [ ] Add session management

### Week 3: Frontend Integration
- [ ] Enhance patient intake wizard
- [ ] Add JSON upload functionality
- [ ] Implement dynamic dashboard updates
- [ ] Add session persistence

### Week 4: Multi-Disease & Testing
- [ ] Add disease-specific pipelines
- [ ] Create test patient profiles
- [ ] End-to-end testing
- [ ] Documentation

## Success Criteria

✅ Each user can create their own patient session
✅ JSON upload creates personalized analysis
✅ Manual intake wizard captures all patient data
✅ Analysis results are patient-specific (not hardcoded)
✅ Multiple diseases supported (epilepsy, diabetes, hypertension, depression)
✅ Session management works across page refreshes
✅ No hardcoded GABI_PRESET patient
✅ Clean architecture with testable components

## Migration Strategy

### Phase 1: Backward Compatibility
- Keep existing GABI_PRESET as default/demo patient
- Add new dynamic system alongside
- Gradual migration of features

### Phase 2: Full Migration
- Remove hardcoded patient references
- Make dynamic system primary
- Update all visualizations to use session data

### Phase 3: Enhancement
- Add patient history tracking
- Implement patient data export
- Add multi-session support (doctor viewing multiple patients)

## Documentation

- **Architecture Guide**: Clean Architecture patterns used
- **API Documentation**: OpenAPI/Swagger for all endpoints
- **User Guide**: How to upload JSON or use intake wizard
- **Developer Guide**: How to add new diseases/drugs

## Conclusion

This plan transforms QuantaMed from a single-patient demo into a production-ready, multi-patient platform using industry-standard architecture patterns. The system will be:

- **Scalable**: Easy to add new diseases, drugs, and features
- **Maintainable**: Clean separation of concerns
- **Testable**: Business logic independent of infrastructure
- **User-Friendly**: Simple JSON upload or guided intake
- **Flexible**: Support for any disease/drug combination

Ready for implementation! 🚀