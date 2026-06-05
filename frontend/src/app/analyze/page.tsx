"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Loader2, Download } from "lucide-react";
import { analyzePatient } from "@/lib/api";
import { GABI_PRESET } from "@/lib/presets";
import type { FullAnalysisResult, PatientInput, ExtendedDrugRanking } from "@/types";
import AlertBanner from "@/components/AlertBanner";
import DrugRankingTable from "@/components/DrugRankingTable";
import AdmetPanel from "@/components/AdmetPanel";
import FaersPanel from "@/components/FaersPanel";
import OffTargetPanel from "@/components/OffTargetPanel";
import FinalVerdict from "@/components/FinalVerdict";
import TribeBrain from "@/components/TribeBrain";
import MolecularDocking from "@/components/MolecularDocking";
import ErrorBoundary from "@/components/ErrorBoundary";
import EmptyState from "@/components/EmptyState";

export default function AnalyzePage() {
  const [collapsed, setCollapsed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FullAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedDrug, setSelectedDrug] = useState<string | null>(null);

  // Form state
  const [age, setAge] = useState("24");
  const [gender, setGender] = useState("female");
  const [weight, setWeight] = useState("58");
  const [height, setHeight] = useState("165");
  const [diagnosis, setDiagnosis] = useState("epilepsy");
  const [severity, setSeverity] = useState("moderate");
  const [subtype, setSubtype] = useState("Juvenile Myoclonic Epilepsy");
  const [cyp2d6, setCyp2d6] = useState("Poor");
  const [cyp2c9, setCyp2c9] = useState("Intermediate");
  const [cyp2c19, setCyp2c19] = useState("Normal");
  const [cyp3a4, setCyp3a4] = useState("Normal");

  const buildPatient = (): PatientInput => ({
    basic_info: { age: Number(age), gender, weight_kg: Number(weight), height_cm: Number(height) },
    condition: { primary_diagnosis: diagnosis, severity, subtype },
    genetics: { CYP2D6: cyp2d6, CYP2C9: cyp2c9, CYP2C19: cyp2c19, CYP3A4: cyp3a4 },
    current_meds: [{ drug_id: "vpa", drug_name: "Valproic Acid", dose_mg: 1000, frequency: "BID" }],
    labs: { ALT: 42, AST: 38, eGFR: 95 },
  });

  const handleAnalyze = async () => {
    setLoading(true); setError(null); setSelectedDrug(null);
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const data = await analyzePatient(buildPatient()) as any;
      setResult(data);
      if (data.rankings?.length) setSelectedDrug(data.rankings[0].drug_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally { setLoading(false); }
  };

  const loadGabi = async () => {
    setLoading(true); setError(null); setSelectedDrug(null);
    setAge("24"); setGender("female"); setWeight("58"); setHeight("165");
    setDiagnosis("epilepsy"); setSeverity("moderate"); setSubtype("Juvenile Myoclonic Epilepsy");
    setCyp2d6("Poor"); setCyp2c9("Intermediate"); setCyp2c19("Normal"); setCyp3a4("Normal");
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const data = await analyzePatient(GABI_PRESET) as any;
      setResult(data);
      if (data.rankings?.length) setSelectedDrug(data.rankings[0].drug_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally { setLoading(false); }
  };

  const selected: ExtendedDrugRanking | undefined = result?.rankings?.find(r => r.drug_id === selectedDrug);

  return (
    <div className="flex min-h-[calc(100vh-56px)]">
      {/* Sidebar — collapsible */}
      <aside
        className="flex-shrink-0 border-r border-white/[0.05] bg-[#0A0E15] transition-all duration-300 overflow-y-auto"
        style={{ width: collapsed ? 48 : 300 }}
      >
        <div className="p-4 flex items-center justify-between">
          {!collapsed && <span className="text-xs font-mono tracking-wider text-white/30 uppercase">Patient Profile</span>}
          <button onClick={() => setCollapsed(!collapsed)} className="text-white/25 hover:text-white/50 transition-colors">
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        {!collapsed && (
          <div className="px-4 pb-4 space-y-3">
            {/* Quick load */}
            <button onClick={loadGabi} className="w-full text-xs font-mono px-3 py-2 rounded border border-[#4AFA9A]/20 text-[#4AFA9A]/70 hover:bg-[#4AFA9A]/5 transition-colors">
              Load Demo (Gabi)
            </button>

            {/* Basic Info */}
            <div className="text-[9px] font-mono text-white/20 uppercase tracking-wider pt-2">Basic Info</div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Age</label>
                <input value={age} onChange={e => setAge(e.target.value)} type="number"
                  className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none focus:border-[#4AFA9A]/30" />
              </div>
              <div>
                <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Gender</label>
                <select value={gender} onChange={e => setGender(e.target.value)}
                  className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none">
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Weight (kg)</label>
                <input value={weight} onChange={e => setWeight(e.target.value)} type="number"
                  className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none focus:border-[#4AFA9A]/30" />
              </div>
              <div>
                <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Height (cm)</label>
                <input value={height} onChange={e => setHeight(e.target.value)} type="number"
                  className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none focus:border-[#4AFA9A]/30" />
              </div>
            </div>

            {/* Condition */}
            <div className="text-[9px] font-mono text-white/20 uppercase tracking-wider pt-2">Condition</div>
            <div>
              <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Diagnosis</label>
              <input value={diagnosis} onChange={e => setDiagnosis(e.target.value)}
                className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none focus:border-[#4AFA9A]/30" />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Severity</label>
                <select value={severity} onChange={e => setSeverity(e.target.value)}
                  className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none">
                  <option value="mild">Mild</option>
                  <option value="moderate">Moderate</option>
                  <option value="severe">Severe</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Subtype</label>
                <input value={subtype} onChange={e => setSubtype(e.target.value)}
                  className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-2 py-1.5 text-xs text-white/70 outline-none focus:border-[#4AFA9A]/30" />
              </div>
            </div>

            {/* Pharmacogenomics */}
            <div className="text-[9px] font-mono text-white/20 uppercase tracking-wider pt-2">Pharmacogenomics</div>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: "CYP2D6", value: cyp2d6, set: setCyp2d6 },
                { label: "CYP2C9", value: cyp2c9, set: setCyp2c9 },
                { label: "CYP2C19", value: cyp2c19, set: setCyp2c19 },
                { label: "CYP3A4", value: cyp3a4, set: setCyp3a4 },
              ].map(cyp => (
                <div key={cyp.label}>
                  <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">{cyp.label}</label>
                  <select value={cyp.value} onChange={e => cyp.set(e.target.value)}
                    className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-2 py-1.5 text-xs text-white/70 outline-none">
                    {["Normal", "Poor", "Intermediate", "Ultrarapid"].map(v => <option key={v}>{v}</option>)}
                  </select>
                </div>
              ))}
            </div>

            <button onClick={handleAnalyze} disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[#4AFA9A] text-[#080A0F] text-xs font-mono font-semibold rounded hover:bg-[#3de88a] disabled:opacity-50 transition-colors mt-4">
              {loading ? <><Loader2 size={14} className="animate-spin" /> Running 9 Pipelines...</> : "Analyze →"}
            </button>

            {error && <p className="text-xs text-red-400/70 mt-2">{error}</p>}
          </div>
        )}
      </aside>

      {/* Results area */}
      <div className="flex-1 p-6 overflow-y-auto">
        <ErrorBoundary fallbackLabel="Analysis results failed to load.">
          {!result && !loading && <EmptyState label="Upload or configure a patient profile to begin analysis" icon="🧬" />}

          {result && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5 max-w-5xl">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg text-white/80 font-medium">
                    {result.patient_name && result.patient_name !== "Unknown Patient" ? result.patient_name + " — " : ""}
                    {result.diagnosis || result.condition_type}
                  </h2>
                  <span className="text-xs font-mono text-white/25">{result.rankings.length} candidates ranked · 9 pipelines</span>
                </div>
                {result.patient_completeness && (
                  <span className="tag tag-cyan">
                    {result.patient_completeness.percentage}% data · {result.patient_completeness.confidence_level}
                  </span>
                )}
              </div>

              {/* Clinical alerts */}
              {result.clinical_alerts.length > 0 && (
                <div className="space-y-2">
                  {result.clinical_alerts.map((a, i) => <AlertBanner key={i} alert={a} />)}
                </div>
              )}

              {/* Drug rankings */}
              <DrugRankingTable rankings={result.rankings} />

              {/* Drug selector for deep-dive */}
              {result.rankings.length > 0 && (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[10px] font-mono text-white/20 uppercase">Deep dive:</span>
                  {result.rankings.map(r => (
                    <button key={r.drug_id} onClick={() => setSelectedDrug(r.drug_id)}
                      className={`text-[10px] font-mono px-3 py-1 rounded border transition-colors ${
                        selectedDrug === r.drug_id
                          ? "border-[#4AFA9A]/40 text-[#4AFA9A] bg-[#4AFA9A]/5"
                          : "border-white/10 text-white/40 hover:border-white/20"
                      }`}>
                      #{r.rank} {r.drug_name}
                    </button>
                  ))}
                </div>
              )}

              {/* Deep-dive panels for selected drug */}
              {selected && (
                <motion.div key={selected.drug_id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                  {/* Tribe Brain Visualizer */}
                  <TribeBrain drugName={selected.drug_name} state={selected.drug_id === "vpa" ? "vpa" : "ltg"} />

                  {/* Molecular Docking */}
                  <MolecularDocking />

                  {/* ADMET */}
                  {selected.admet && <AdmetPanel data={selected.admet} drugName={selected.drug_name} />}

                  {/* Off-Target */}
                  {selected.off_target && <OffTargetPanel data={selected.off_target} drugName={selected.drug_name} />}

                  {/* FAERS */}
                  {selected.faers && <FaersPanel data={selected.faers} />}

                  {/* PK Summary */}
                  {selected.pk_summary && (
                    <div className="panel p-4">
                      <h4 className="text-xs font-mono tracking-wider text-white/40 mb-3 uppercase">
                        PK Summary — {selected.drug_name}
                      </h4>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="bg-white/[0.03] rounded p-3 text-center">
                          <span className="block text-[9px] font-mono text-white/30 uppercase">Css Average</span>
                          <span className="text-lg font-mono font-bold text-[#4AFA9A]">
                            {(selected.pk_summary.css_avg ?? 0).toFixed(2)} <span className="text-[10px] text-white/30">µg/mL</span>
                          </span>
                        </div>
                        <div className="bg-white/[0.03] rounded p-3 text-center">
                          <span className="block text-[9px] font-mono text-white/30 uppercase">Status</span>
                          <span className={`text-lg font-mono font-bold ${
                            selected.pk_summary.status === "OK" ? "text-[#4AFA9A]" : selected.pk_summary.status === "LOW" ? "text-[#FACC15]" : "text-[#EF4444]"
                          }`}>{selected.pk_summary.status}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {/* Final Verdict */}
              <FinalVerdict rankings={result.rankings} disclaimer={result.disclaimer} />

              {/* Data sources */}
              <div className="flex flex-wrap gap-2 pt-4 border-t border-white/[0.05]">
                {result.data_sources.map(s => <span key={s} className="tag text-[8px]">{s}</span>)}
              </div>
            </motion.div>
          )}
        </ErrorBoundary>
      </div>
    </div>
  );
}
