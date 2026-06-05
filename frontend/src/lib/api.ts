// ── API Layer ─────────────────────────────────────────────────────────
import type {
  AnalysisResult, CompareResult, DDIResult,
  TrialsResult, AgentResult, PKCurve, PatientInput,
} from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:7860";

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...opts?.headers },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
  }
  return res.json();
}

export async function analyzePatient(patient: PatientInput): Promise<AnalysisResult> {
  return request("/api/quantamed/analyze-uploaded", {
    method: "POST",
    body: JSON.stringify(patient),
  });
}

export async function compareDrugs(patient: PatientInput, drugIds: string[]): Promise<CompareResult> {
  return request("/api/foldables/compare", {
    method: "POST",
    body: JSON.stringify({ patient, drug_ids: drugIds }),
  });
}

export async function checkDDI(patient: PatientInput, drug: string): Promise<DDIResult> {
  return request(`/api/foldables/ddi?drug=${encodeURIComponent(drug)}`, {
    method: "POST",
    body: JSON.stringify({ patient }),
  });
}

export async function matchTrials(patient: PatientInput): Promise<TrialsResult> {
  return request("/api/foldables/trials", {
    method: "POST",
    body: JSON.stringify({ patient }),
  });
}

export async function matchTrialsDemo(): Promise<TrialsResult> {
  return request("/api/foldables/trials/demo");
}

export async function runAgent(opts: {
  task_id: string;
  model: string;
  max_steps: number;
  anthropic_api_key?: string;
}): Promise<AgentResult> {
  return request("/api/agent/run", {
    method: "POST",
    body: JSON.stringify(opts),
  });
}

export async function getPKCurve(
  drug: string, dailyDose: number, dosesPerDay: number, cyp2c9: string
): Promise<PKCurve> {
  const params = new URLSearchParams({
    drug, daily_dose_mg: String(dailyDose),
    doses_per_day: String(dosesPerDay), cyp2c9,
  });
  return request(`/api/quantamed/pk?${params}`);
}

export async function getDemoPatient(): Promise<{ patient: PatientInput }> {
  return request("/api/foldables/demo-patient");
}

// ── VQE Quantum Binding ───────────────────────────────────────────
export async function getVQEConvergence(): Promise<Record<string, unknown>> {
  return request("/api/quantamed/vqe");
}

// ── Protein Folding ───────────────────────────────────────────────
export async function getProteinFolding(): Promise<Record<string, unknown>> {
  return request("/api/quantamed/protein-folding");
}

// ── Protein Dynamics ──────────────────────────────────────────────
export async function getProteinDynamics(): Promise<Record<string, unknown>> {
  return request("/api/quantamed/protein-dynamics");
}

// ── Protein Modeling ──────────────────────────────────────────────
export async function modelProtein(fasta: string): Promise<Record<string, unknown>> {
  return request("/api/quantamed/protein-model", {
    method: "POST",
    body: JSON.stringify({ fasta_sequence: fasta }),
  });
}

export async function getProteinExamples(): Promise<Record<string, unknown>> {
  return request("/api/quantamed/protein-examples");
}

// ── Drug Properties & Toxicology ──────────────────────────────────
export async function getDrugProperties(drugId: string): Promise<Record<string, unknown>> {
  return request(`/api/foldables/drug-properties?drug_id=${encodeURIComponent(drugId)}`);
}

export async function getToxicity(drugId: string): Promise<Record<string, unknown>> {
  return request(`/api/foldables/toxicity?drug_id=${encodeURIComponent(drugId)}`);
}

export async function getFaersSignals(drugId: string): Promise<Record<string, unknown>> {
  return request(`/api/foldables/faers?drug_id=${encodeURIComponent(drugId)}`);
}

export async function getProteinTarget(drugId: string): Promise<Record<string, unknown>> {
  return request(`/api/foldables/protein-target?drug_id=${encodeURIComponent(drugId)}`);
}

export async function getAllDrugIds(): Promise<Record<string, unknown>> {
  return request("/api/foldables/drugs");
}

// ── Full Analysis (returns extended pipeline data) ────────────────
export async function analyzePatientFull(patient: PatientInput): Promise<Record<string, unknown>> {
  return request("/api/quantamed/analyze-uploaded", {
    method: "POST",
    body: JSON.stringify({ patient }),
  });
}

// ── PDF Report ────────────────────────────────────────────────────
export async function getReport(drugId: string, patientId: string): Promise<Blob> {
  const res = await fetch(`${BASE}/api/quantamed/report?drug=${encodeURIComponent(drugId)}&patient=${encodeURIComponent(patientId)}`);
  if (!res.ok) throw new Error("Report generation failed");
  return res.blob();
}
