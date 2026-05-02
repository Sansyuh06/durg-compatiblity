"""
Patient Use Cases - Application Business Logic
Orchestrates patient creation, analysis, and management
"""
from typing import Dict, Any, List
from datetime import datetime
import logging

from server.domain.patient import Patient
from server.domain.interfaces import (
    IPatientRepository,
    IDrugAnalysisService,
    IProteinFoldingService,
    IScoringEngine,
    IReportGenerator
)

logger = logging.getLogger(__name__)


class CreatePatientSessionUseCase:
    """Use Case: Create a new patient session from JSON or manual input"""
    
    def __init__(self, patient_repository: IPatientRepository):
        self.patient_repository = patient_repository
    
    def execute(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new patient session
        
        Args:
            patient_data: Complete patient profile data
            
        Returns:
            {
                "session_id": str,
                "patient": Dict,
                "created_at": str,
                "message": str
            }
        """
        try:
            # Create patient aggregate from data
            patient = Patient.create_new(patient_data)
            
            # Save to repository
            self.patient_repository.save(patient)
            
            logger.info(f"Created patient session: {patient.session_id}")
            
            return {
                "session_id": patient.session_id,
                "patient": patient.to_dict(),
                "created_at": patient.created_at,
                "message": "Patient session created successfully"
            }
            
        except ValueError as e:
            logger.error(f"Validation error creating patient: {e}")
            raise ValueError(f"Invalid patient data: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating patient session: {e}")
            raise RuntimeError(f"Failed to create patient session: {str(e)}")


class GetPatientSessionUseCase:
    """Use Case: Retrieve patient session by ID"""
    
    def __init__(self, patient_repository: IPatientRepository):
        self.patient_repository = patient_repository
    
    def execute(self, session_id: str) -> Dict[str, Any]:
        """
        Get patient session
        
        Args:
            session_id: Patient session ID
            
        Returns:
            Patient data dictionary
        """
        patient = self.patient_repository.find_by_session_id(session_id)
        
        if not patient:
            raise ValueError(f"Patient session not found: {session_id}")
        
        return patient.to_dict()


class AnalyzeDrugCompatibilityUseCase:
    """Use Case: Analyze drug compatibility for a patient"""
    
    def __init__(
        self,
        patient_repository: IPatientRepository,
        drug_analysis_service: IDrugAnalysisService,
        protein_folding_service: IProteinFoldingService,
        scoring_engine: IScoringEngine
    ):
        self.patient_repository = patient_repository
        self.drug_analysis_service = drug_analysis_service
        self.protein_folding_service = protein_folding_service
        self.scoring_engine = scoring_engine
    
    def execute(
        self,
        session_id: str,
        drug_name: str,
        dose_mg: float,
        include_protein_simulation: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze drug compatibility for patient
        
        Args:
            session_id: Patient session ID
            drug_name: Drug to analyze
            dose_mg: Proposed dose in mg
            include_protein_simulation: Whether to run quantum protein folding
            
        Returns:
            Complete analysis results
        """
        # Get patient
        patient = self.patient_repository.find_by_session_id(session_id)
        if not patient:
            raise ValueError(f"Patient session not found: {session_id}")
        
        logger.info(f"Analyzing {drug_name} for patient {session_id}")
        
        # Check basic compatibility using domain logic
        can_take, domain_reasons = patient.can_take_drug(drug_name)
        
        # Get patient risk score
        patient_risk_score = patient.get_risk_score()
        
        # Perform drug analysis
        drug_analysis = self.drug_analysis_service.analyze_drug_compatibility(
            patient, drug_name, dose_mg
        )
        
        # Calculate drug-specific risk score
        drug_risk_score = self.scoring_engine.calculate_risk_score(
            patient, drug_name
        )
        
        # Evaluate efficacy
        efficacy_analysis = self.scoring_engine.evaluate_efficacy(
            patient, drug_name
        )
        
        # Protein folding simulation (if requested)
        protein_simulation = None
        if include_protein_simulation:
            try:
                # Get target protein for condition
                target_protein = self._get_target_protein(patient.condition.primary_diagnosis)
                
                protein_simulation = self.protein_folding_service.simulate_protein_folding(
                    protein_sequence=target_protein["sequence"],
                    drug_molecule=drug_name
                )
                
                logger.info(f"Protein simulation completed for {drug_name}")
            except Exception as e:
                logger.warning(f"Protein simulation failed: {e}")
                protein_simulation = {"error": str(e)}
        
        # Get alternative drugs
        alternatives = self.drug_analysis_service.get_alternative_drugs(
            patient, patient.condition.primary_diagnosis
        )
        
        # Compile complete analysis
        analysis_result = {
            "session_id": session_id,
            "drug_name": drug_name,
            "dose_mg": dose_mg,
            "analyzed_at": datetime.now().isoformat(),
            "patient_summary": {
                "age": patient.basic_info.age,
                "gender": patient.basic_info.gender.value,
                "condition": patient.condition.primary_diagnosis,
                "severity": patient.condition.severity.value,
                "risk_score": patient_risk_score
            },
            "compatibility": {
                "can_take": can_take and drug_analysis["compatible"],
                "overall_risk_score": (patient_risk_score + drug_risk_score) / 2,
                "domain_warnings": domain_reasons,
                "drug_warnings": drug_analysis["warnings"],
                "contraindications": self._identify_contraindications(
                    patient, drug_analysis
                )
            },
            "pharmacokinetics": drug_analysis.get("pharmacokinetics", {}),
            "drug_interactions": drug_analysis.get("interactions", []),
            "efficacy": efficacy_analysis,
            "protein_simulation": protein_simulation,
            "recommendations": self._generate_recommendations(
                patient, drug_analysis, efficacy_analysis, can_take
            ),
            "alternative_drugs": alternatives[:5]  # Top 5 alternatives
        }
        
        logger.info(f"Analysis complete for {drug_name}: compatible={analysis_result['compatibility']['can_take']}")
        
        return analysis_result
    
    def _get_target_protein(self, condition: str) -> Dict[str, str]:
        """Get target protein for condition"""
        # Simplified mapping - would use database in production
        protein_targets = {
            "Juvenile Myoclonic Epilepsy": {
                "name": "GABA_A Receptor",
                "sequence": "MSKRKPGTVLVLGITTVLTMTTQSSGSRASLPKVSYVKAIDIWMAVCLLFVFSALLEYAAVNFVSRQHKELLRFRRKRRHHKSPMLNLFEEDPGFLS"
            },
            "Type 2 Diabetes": {
                "name": "Insulin Receptor",
                "sequence": "MATGGRRGAAAAPLLVAVAALLLGAAGHLYPGEVCPGMDIRNNLTRLHELENCSVIEGHLQILLMFKTRPEDFRDLSFPKLIMITDYLLLFRVYGLESLKDLFPNLTVIRGSRLFFNYALVIFEMVHLKELGLYNLMNITRGSVRIEKNNELCYLATIDWSRILDSVEDNHIVLNKDDNEECGDICPGTAKGKTNCPATVINGQFVERCWTHSHCQKVCPTICKSHGCTAEGLCCHSECLGNCSQPDDPTKCVACRNFYLDGRCVETCPPPYYHFQDWRCVNFSFCQDLHHKCKNSRRQGCHQYVIHNNKCIPECPSGYTMNSSNLLCTPCLGPCPKVCHLLEGEKTIDSVTSAQELRGCTVINGSLIINIRGGNNLAAELEANLGLIEEISGYLKIRRSYALVSLSFFRKLRLIRGETLEIGNYSFYALDNQNLRQLWDWSKHNLTITQGKLFFHYNPKLCLSEIHKMEEVSGTKGRQERNDIALKTNGDQASCENELLKFSYIRTSFDKILLRWEPYWPPDFRDLLGFMLFYKEAPYQNVTEFDGQDACGSNSWTVVDIDPPLRSNDPKSQNHPGWLMRGLKPWTQYAIFVKTLVTFSDERRTYGAKSDIIYVQTDATNPSVPLDPISVSNSSSQIILKWKPPSDPNGNITHYLVFWERQAEDSELFELDYCLKGLKLPSRTWSPPFESEDSQKHNQSEYEDSAGECCSCPKTDSQILKELEESSFRKTFEDYLHNVVFVPRKTSSGTGAEDPRPSRKRRSLGDVGNVTVAVPTVAAFPNTSSTSVPTSPEEHRPFEKVVNKESLVISGLRHFTGYRIELQACNQDTPEERCSVAAYVSARTMPEAKADDIVGPVTHEIFENNVVHLMWQEPKEPNGLIVLYEVSYRRYGDEELHLCVSRKHFALERGCRLRGLSPGNYSVRIRATSLAGNGSWTEPTYFYVTDYLDVPSNIAKIIIGPLIFVFLFSVVIGSIYLFLRKRQPDGPLGPLYASSNPEYLSASDVFPCSVYVPDEWEVSREKITLLRELGQGSFGMVYEGNARDIIKGEAETRVAVKTVNESASLRERIEFLNEASVMKGFTCHHVVRLLGVVSKGQPTLVVMELMAHGDLKSYLRSLRPEAENNPGRPPPTLQEMIQMAAEIADGMAYLNAKKFVHRDLAARNCMVAHDFTVKIGDFGMTRDIYETDYYRKGGKGLLPVRWMAPESLKDGVFTTSSDMWSFGVVLWEITSLAEQPYQGLSNEQVLKFVMDGGYLDQPDNCPERVTDLMRMCWQFNPKMRPTFLEIVNLLKDDLHPSFPEVSFFHSEENKAPESEELEMEFEDMENVPLDRSSHCQREEAGGRDGGSSLGFKRSYEEHIPYTHMNGGKKNGRILTLPRSNPS"
            },
            "Hypertension": {
                "name": "ACE (Angiotensin Converting Enzyme)",
                "sequence": "MGAASGRRGPGLLLPLPLLLLLPPQPALALDPGLQPGNFSADEAGAQLFAQSYNSSAEQVLFQSVAASWAHDTNITAENARRQEEAALLSQEFAEAWGQKAKELYEPIWQNFTDPQLRRIIGAVRTLGSANLPLAKRQQYNALLSNMSRIYSTAKVCLPNKTATCWSLDPDLTNILASSRSYAMLLFAWEGWHNAAGIPLKPLYEDFTALSNEAYKQDGFTDTGAYWRSWYNSPTFEDDLEHLYQQVVKLKNGNRTLSTELVQLTPTEGFNASNIVTSVPRATTVDTFFQNLGQTFTCNHPQTKLYDVAQTDLLQCGPGGSLITGMVDNTWRLAWETFKPGWSSEACSSLHFNGTSLSGSTSFSFQNETEINFLLKQALTIVGTLPFTYEFSVDDIKAIQAQNLQNLQIKKTNAFLNFGCNFNVSVQPTSRPVSLQNLSITETTGVVNHLYDPDTGRSYFGAAVKFGMNINEKSYPALLATIHEFSDDTFNSHNNNFQLTGVQNPRPNHTKDTDTPKGPKVYAGQDFQPVVSMLQAAAVSNFGYDLYDECNMGVNLTSMSKGLFMNYQNDPELRPWMQVKVEEANNLKVAKQEYGIPQISTGDMLRAAVKSGSMVLTGAKPADTERGLEWILSKVNYGDLGNVAVKVSSSDPETQTQKFYLMLDDTSLSGKGFPSNVAVKVSIPKFYQPGDKVVVQEVKLNGTGKITVNEASRPYAWESVFHVPGEHQGKGSPGRDSSPPGPPRR"
            },
            "Depression": {
                "name": "Serotonin Transporter (SERT)",
                "sequence": "MDNCTTMDSQNNTANPPQNQSQGNLPGQGLLDLLLPQVQYGSIFRAAALCGFRCNRLCTPNVPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPGPG"
            }
        }
        
        return protein_targets.get(condition, {
            "name": "Generic Target",
            "sequence": "MSKRKPGTVLVLGITTVLTMTTQSSGSRASLPKVSYVKAIDIWMAVCLLFVFSALLEYAAVNFVSRQHKELLRFRRKRRHHKSPMLNLFEEDPGFLS"
        })
    
    def _identify_contraindications(
        self,
        patient: Patient,
        drug_analysis: Dict[str, Any]
    ) -> List[str]:
        """Identify absolute contraindications"""
        contraindications = []
        
        # Allergy contraindication
        if not drug_analysis["compatible"] and "allerg" in " ".join(drug_analysis["warnings"]).lower():
            contraindications.append("Drug allergy - ABSOLUTE CONTRAINDICATION")
        
        # Severe organ dysfunction
        if patient.labs.has_hepatic_impairment() and patient.labs.alt_u_l > 200:
            contraindications.append("Severe hepatic impairment - use with extreme caution")
        
        if patient.labs.has_renal_impairment() and patient.labs.egfr_ml_min < 30:
            contraindications.append("Severe renal impairment - dose adjustment required")
        
        return contraindications
    
    def _generate_recommendations(
        self,
        patient: Patient,
        drug_analysis: Dict[str, Any],
        efficacy_analysis: Dict[str, Any],
        can_take: bool
    ) -> List[str]:
        """Generate clinical recommendations"""
        recommendations = []
        
        if can_take:
            recommendations.append("✅ Drug is compatible with patient profile")
            
            # Dosing recommendations
            if patient.basic_info.age > 65:
                recommendations.append("🔸 Consider reduced starting dose due to age")
            
            if patient.labs.has_renal_impairment():
                recommendations.append("🔸 Adjust dose for renal function")
            
            if patient.genetics.is_poor_metabolizer("cyp2d6"):
                recommendations.append("🔸 Start with 50% of standard dose (CYP2D6 poor metabolizer)")
            
            # Monitoring recommendations
            if patient.labs.has_hepatic_impairment():
                recommendations.append("📊 Monitor liver function tests closely")
            
            if len(patient.medications.current_medications) > 3:
                recommendations.append("📊 Monitor for drug interactions")
            
        else:
            recommendations.append("❌ Drug NOT recommended for this patient")
            recommendations.append("🔄 Consider alternative medications")
        
        # Efficacy-based recommendations
        if efficacy_analysis.get("predicted_response", 0) < 0.6:
            recommendations.append("⚠️ Lower predicted efficacy - consider alternative")
        
        return recommendations


class GeneratePatientReportUseCase:
    """Use Case: Generate comprehensive patient report"""
    
    def __init__(
        self,
        patient_repository: IPatientRepository,
        report_generator: IReportGenerator
    ):
        self.patient_repository = patient_repository
        self.report_generator = report_generator
    
    def execute(
        self,
        session_id: str,
        analysis_results: Dict[str, Any],
        format_type: str = "pdf"
    ) -> bytes:
        """
        Generate patient report
        
        Args:
            session_id: Patient session ID
            analysis_results: Drug analysis results
            format_type: "pdf" or "summary"
            
        Returns:
            Report content as bytes
        """
        patient = self.patient_repository.find_by_session_id(session_id)
        if not patient:
            raise ValueError(f"Patient session not found: {session_id}")
        
        if format_type == "pdf":
            return self.report_generator.generate_pdf_report(patient, analysis_results)
        else:
            summary = self.report_generator.generate_summary(patient, analysis_results)
            return summary.encode('utf-8')

# Made with Bob
