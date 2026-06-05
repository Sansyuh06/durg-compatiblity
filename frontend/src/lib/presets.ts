// ── Presets & Drug Sets ────────────────────────────────────────────────
import type { PatientInput } from "@/types";

export const GABI_PRESET: PatientInput = {
  basic_info: {
    age: 24, gender: "female", weight_kg: 58, height_cm: 165,
    ethnicity: "Caucasian", pregnancy_status: "not_pregnant",
  },
  condition: {
    primary_diagnosis: "epilepsy",
    subtype: "Juvenile Myoclonic Epilepsy",
    severity: "moderate", duration_months: 36,
    comorbidities: ["PCOS"],
  },
  genetics: { CYP2D6: "Poor", CYP3A4: "Normal", CYP2C19: "Normal", CYP2C9: "Intermediate" },
  labs: { ALT: 42, AST: 38, creatinine: 0.8, eGFR: 95, glucose: 92 },
  current_meds: [
    { drug_id: "vpa", drug_name: "Valproic Acid", dose_mg: 1000, frequency: "BID" },
  ],
};

export interface DrugChip {
  id: string;
  label: string;
}

export const DRUG_SETS: Record<string, DrugChip[]> = {
  epilepsy: [
    { id: "vpa", label: "Valproic Acid" },
    { id: "ltg", label: "Lamotrigine" },
    { id: "lev", label: "Levetiracetam" },
    { id: "tpm", label: "Topiramate" },
    { id: "zns", label: "Zonisamide" },
  ],
  cancer: [
    { id: "trastuzumab", label: "Trastuzumab" },
    { id: "pertuzumab", label: "Pertuzumab" },
    { id: "lapatinib", label: "Lapatinib" },
    { id: "neratinib", label: "Neratinib" },
    { id: "tucatinib", label: "Tucatinib" },
  ],
  diabetes: [
    { id: "metformin", label: "Metformin" },
    { id: "empagliflozin", label: "Empagliflozin" },
    { id: "semaglutide", label: "Semaglutide" },
    { id: "sitagliptin", label: "Sitagliptin" },
    { id: "pioglitazone", label: "Pioglitazone" },
  ],
  hypertension: [
    { id: "lisinopril", label: "Lisinopril" },
    { id: "amlodipine", label: "Amlodipine" },
    { id: "losartan", label: "Losartan" },
    { id: "metoprolol", label: "Metoprolol" },
    { id: "hydrochlorothiazide", label: "HCTZ" },
  ],
  depression: [
    { id: "escitalopram", label: "Escitalopram" },
    { id: "sertraline", label: "Sertraline" },
    { id: "bupropion", label: "Bupropion" },
    { id: "venlafaxine", label: "Venlafaxine" },
    { id: "mirtazapine", label: "Mirtazapine" },
  ],
};

export const CONDITIONS = [
  "epilepsy", "cancer", "diabetes", "hypertension", "depression", "schizophrenia",
] as const;

export const DEMO_AGENT_TRANSCRIPT = [
  { step: 1, action_type: "search_faers", parameters: {}, reasoning: "Starting with FAERS adverse event database search to identify reported safety signals.", reward: 0.05, done: false },
  { step: 2, action_type: "fetch_label", parameters: {}, reasoning: "Retrieving the drug's FDA-approved label to check Black Box Warnings and known ADRs.", reward: 0.05, done: false },
  { step: 3, action_type: "analyze_signal", parameters: {}, reasoning: "Running statistical analysis on FAERS signal data — checking PRR and ROR for significance.", reward: 0.05, done: false },
  { step: 4, action_type: "check_literature", parameters: {}, reasoning: "Cross-referencing findings with published case reports and systematic reviews.", reward: 0.05, done: false },
  { step: 5, action_type: "submit", parameters: { drug_name: "metformin", primary_signal: "lactic acidosis", regulatory_action: "monitor" }, reasoning: "Evidence supports continued monitoring: lactic acidosis is rare (0.03/1000 PY), well-characterized, and adequately addressed by current Black Box Warning.", reward: 0.92, done: true },
];
