// ── QuantaMed TypeScript Interfaces ────────────────────────────────────

export interface PatientBasicInfo {
  age: number;
  gender: string;
  weight_kg: number;
  height_cm: number;
  ethnicity?: string;
  pregnancy_status?: string;
}

export interface PatientCondition {
  primary_diagnosis: string;
  subtype?: string;
  severity: string;
  duration_months?: number;
  comorbidities?: string[];
}

export interface PatientGenetics {
  CYP2D6?: string;
  CYP2C9?: string;
  CYP2C19?: string;
  CYP3A4?: string;
}

export interface MedEntry {
  drug_id: string;
  drug_name: string;
  dose_mg: number;
  frequency?: string;
}

export interface PatientInput {
  basic_info: PatientBasicInfo;
  condition: PatientCondition;
  genetics?: PatientGenetics;
  current_meds?: MedEntry[];
  labs?: Record<string, number | null>;
  lifestyle?: Record<string, unknown>;
}

export interface ClinicalAlert {
  type: "CRITICAL" | "WARNING" | "INFO";
  title: string;
  message: string;
  source: string;
}

export interface BreakdownEntry {
  score: number;
  weight: number;
  source: string;
  interactions?: DDIInteraction[];
  n_interactions?: number;
}

export interface DrugRanking {
  drug_id: string;
  drug_name: string;
  composite_score: number;
  recommendation: "RECOMMENDED" | "CONDITIONAL" | "NOT_RECOMMENDED";
  rank: number;
  flags: string[];
  breakdown: {
    efficacy: BreakdownEntry;
    safety: BreakdownEntry;
    genomic: BreakdownEntry;
    admet: BreakdownEntry;
    ddi: BreakdownEntry;
  };
  radar?: Record<string, number>;
}

export interface AnalysisResult {
  patient_name?: string;
  patient_diagnosis?: string;
  patient_completeness?: {
    percentage: number;
    confidence_level: string;
  };
  clinical_alerts: ClinicalAlert[];
  condition_type: string;
  diagnosis: string;
  rankings: DrugRanking[];
  data_sources: string[];
}

export interface DDIInteraction {
  drug_a: string;
  drug_b: string;
  severity: "MAJOR" | "MODERATE" | "MINOR";
  mechanism: string;
  effect: string;
  penalty: number;
  source: string;
}

export interface DDIResult {
  score: number;
  interactions: DDIInteraction[];
  n_interactions: number;
  severity_summary: Record<string, number>;
}

export interface CompareResult {
  results: DrugRanking[];
  winner: string | null;
  winner_name: string | null;
  avoid: string | null;
  avoid_name: string | null;
  patient_summary: Record<string, unknown>;
}

export interface TrialMatch {
  nct_id: string;
  title: string;
  phase: string;
  status: string;
  sponsor: string;
  drug: string;
  locations: string[];
  contact_email: string;
  match_score: number;
  match_pct: number;
  match_reasons: string[];
}

export interface TrialsResult {
  trials: TrialMatch[];
  total_screened: number;
  total_matched: number;
}

export interface AgentStep {
  step: number;
  action_type: string;
  parameters: Record<string, unknown>;
  reasoning: string;
  reward: number;
  done: boolean;
}

export interface AgentResult {
  transcript: AgentStep[];
  final_score: number;
  final_message: string;
  steps_taken: number;
  task_id: string;
}

export interface PKCurve {
  drug_id: string;
  drug_name: string;
  series: { t_h: number[]; c_ug_ml: number[] };
  derived: {
    cavg_ug_ml: number;
    cmax_ug_ml: number;
    cmin_ug_ml: number;
    t_half_h: number;
    t_half_adjusted_h: number;
    therapeutic_min: number;
    therapeutic_max: number;
    status: string;
  };
}

// ── VQE Quantum Simulation ────────────────────────────────────────
export interface VQEResult {
  drug_id: string;
  drug_name: string;
  iterations: number[];
  energies: number[];
  ground_state_energy: number;
  convergence_threshold: number;
  binding_affinity_score: number;
  qubit_count: number;
  ansatz: string;
}

// ── Off-Target Protein Panel ──────────────────────────────────────
export interface OffTargetResult {
  score: number;
  targets: { protein: string; activity: string; pchembl: number; source: string }[];
  confidence: string;
  data_sources: string[];
}

// ── ADMET / BBB Prediction ────────────────────────────────────────
export interface LipinskiRule {
  mw: number;
  logp: number;
  hbd: number;
  hba: number;
  violations: number;
  pass: boolean;
}

export interface AdmetResult {
  score: number;
  lipinski: LipinskiRule;
  bbb: { probability: number; permeable: boolean };
  psa: number;
  rotatable_bonds: number;
  solubility_mg_ml: number;
  confidence: string;
  data_sources: string[];
}

// ── FAERS Adverse Event Signals ───────────────────────────────────
export interface FaersEvent {
  event: string;
  count: number;
  pct: number;
}

export interface FaersResult {
  drug_id: string;
  drug_name: string;
  total_reports: number;
  events: FaersEvent[];
  confidence: string;
  data_sources: string[];
}

// ── PK Summary (within ranking) ───────────────────────────────────
export interface PKSummary {
  css_avg: number;
  status: string;
}

// ── Protein Dynamics ──────────────────────────────────────────────
export interface ProteinDynamicsResult {
  protein_id: string;
  rmsd_trajectory: number[];
  rmsf_per_residue: number[];
  radius_of_gyration: number[];
  secondary_structure: Record<string, number>;
  binding_pocket_volume: number;
  flexibility_score: number;
}

// ── Protein Modeling ──────────────────────────────────────────────
export interface ProteinModelResult {
  sequence_length: number;
  predicted_structure: string;
  confidence_scores: number[];
  secondary_structure: string;
  model_quality: number;
  ramachandran_favored: number;
}

// ── Drug Properties ───────────────────────────────────────────────
export interface DrugProperties {
  drug_id: string;
  drug_name: string;
  smiles: string;
  molecular_weight: number;
  logp: number;
  hbd: number;
  hba: number;
  psa: number;
  rotatable_bonds: number;
  therapeutic_class: string;
}

// ── Toxicity Profile (Tox21) ──────────────────────────────────────
export interface ToxicityResult {
  drug_id: string;
  drug_name: string;
  endpoints: { name: string; active: boolean; confidence: number }[];
  overall_risk: string;
}

// ── Extended DrugRanking (full pipeline) ──────────────────────────
export interface ExtendedDrugRanking extends DrugRanking {
  off_target?: OffTargetResult;
  admet?: AdmetResult;
  faers?: FaersResult;
  pk_summary?: PKSummary;
}

// ── Extended AnalysisResult with full pipeline ────────────────────
export interface FullAnalysisResult extends Omit<AnalysisResult, 'rankings'> {
  rankings: ExtendedDrugRanking[];
  disclaimer?: string;
  patient_id?: string;
}
