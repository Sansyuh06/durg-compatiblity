"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { compareDrugs } from "@/lib/api";
import { GABI_PRESET, DRUG_SETS } from "@/lib/presets";
import type { CompareResult, PatientInput } from "@/types";
import DrugCompareCard from "@/components/DrugCompareCard";
import ErrorBoundary from "@/components/ErrorBoundary";
import EmptyState from "@/components/EmptyState";

export default function ComparePage() {
  const [condition, setCondition] = useState("epilepsy");
  const [selected, setSelected] = useState<Set<string>>(new Set(["vpa", "ltg", "lev"]));
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const chips = DRUG_SETS[condition] || DRUG_SETS.epilepsy;

  const toggle = (id: string) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };

  const run = async () => {
    const ids = Array.from(selected);
    if (ids.length < 2) { setError("Select at least 2 drugs"); return; }
    setLoading(true); setError(null);
    try {
      const patient: PatientInput = { ...GABI_PRESET, condition: { ...GABI_PRESET.condition, primary_diagnosis: condition } };
      const data = await compareDrugs(patient, ids);
      setResult(data);
    } catch (e) { setError(e instanceof Error ? e.message : "Comparison failed"); }
    finally { setLoading(false); }
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <h1 className="text-lg text-white/80 font-medium mb-1">Drug Comparison</h1>
      <p className="text-xs text-white/30 mb-6">Select drugs to compare across all 9 pipelines</p>

      {/* Condition selector */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-[10px] font-mono text-white/30 uppercase">Condition:</span>
        {Object.keys(DRUG_SETS).map(c => (
          <button key={c} onClick={() => { setCondition(c); setSelected(new Set()); setResult(null); }}
            className={`text-[10px] font-mono px-2.5 py-1 rounded transition-colors ${c === condition ? "bg-[#4AFA9A]/10 text-[#4AFA9A] border border-[#4AFA9A]/30" : "text-white/30 border border-white/[0.07] hover:text-white/50"}`}>
            {c}
          </button>
        ))}
      </div>

      {/* Drug chips */}
      <div className="flex flex-wrap gap-2 mb-6">
        {chips.map(chip => (
          <button key={chip.id} onClick={() => toggle(chip.id)}
            className={`text-xs font-mono px-3 py-1.5 rounded border transition-colors ${selected.has(chip.id)
              ? "border-[#4AFA9A]/40 text-[#4AFA9A] bg-[#4AFA9A]/5"
              : "border-white/[0.07] text-white/40 hover:text-white/60"}`}>
            {chip.label}
          </button>
        ))}
      </div>

      <button onClick={run} disabled={loading || selected.size < 2}
        className="inline-flex items-center gap-2 px-5 py-2 bg-[#4AFA9A] text-[#080A0F] text-xs font-mono font-semibold rounded hover:bg-[#3de88a] disabled:opacity-40 transition-colors mb-8">
        {loading ? <><Loader2 size={14} className="animate-spin" /> Comparing...</> : `Compare ${selected.size} Drugs →`}
      </button>

      {error && <p className="text-xs text-red-400/70 mb-4">{error}</p>}

      <ErrorBoundary fallbackLabel="Comparison results failed to load.">
        {!result && !loading && <EmptyState label="Select drugs and run comparison" icon="⚖" />}

        {result && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {/* Winner / Avoid badges */}
            <div className="flex gap-3 mb-6">
              {result.winner_name && <span className="tag tag-green">Winner: {result.winner_name}</span>}
              {result.avoid_name && <span className="tag tag-red">Avoid: {result.avoid_name}</span>}
            </div>

            {/* Comparison cards */}
            <div className="flex gap-4 overflow-x-auto pb-4">
              {result.results.map((drug, i) => (
                <DrugCompareCard key={drug.drug_id} drug={drug} index={i} />
              ))}
            </div>
          </motion.div>
        )}
      </ErrorBoundary>
    </div>
  );
}
