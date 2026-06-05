"use client";
import { useState } from "react";
import { Loader2 } from "lucide-react";
import { checkDDI } from "@/lib/api";
import { GABI_PRESET } from "@/lib/presets";
import type { DDIResult } from "@/types";
import DDICard from "@/components/DDICard";
import ErrorBoundary from "@/components/ErrorBoundary";
import EmptyState from "@/components/EmptyState";
import { scoreColor, formatScore } from "@/lib/utils";

const CANDIDATES = [
  { id: "ltg", label: "Lamotrigine" },
  { id: "lev", label: "Levetiracetam" },
  { id: "tpm", label: "Topiramate" },
  { id: "zns", label: "Zonisamide" },
  { id: "aspirin", label: "Aspirin" },
];

export default function DDIPage() {
  const [candidate, setCandidate] = useState("ltg");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DDIResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true); setError(null);
    try {
      const data = await checkDDI(GABI_PRESET, candidate);
      setResult(data);
    } catch (e) { setError(e instanceof Error ? e.message : "DDI check failed"); }
    finally { setLoading(false); }
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <h1 className="text-lg text-white/80 font-medium mb-1">Drug-Drug Interaction Check</h1>
      <p className="text-xs text-white/30 mb-6">Check candidate drugs against the patient&apos;s current medications</p>

      <div className="grid grid-cols-2 gap-6 mb-8">
        {/* Current meds */}
        <div className="panel p-4">
          <span className="text-[10px] font-mono text-white/30 uppercase block mb-2">Current Medications</span>
          {GABI_PRESET.current_meds?.map(m => (
            <div key={m.drug_id} className="flex items-center gap-2 py-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#4AFA9A]/50" />
              <span className="text-xs text-white/60">{m.drug_name}</span>
              <span className="text-[10px] font-mono text-white/25">{m.dose_mg}mg {m.frequency}</span>
            </div>
          ))}
        </div>

        {/* Candidate selector */}
        <div className="panel p-4">
          <span className="text-[10px] font-mono text-white/30 uppercase block mb-2">Candidate Drug</span>
          <div className="space-y-1.5">
            {CANDIDATES.map(c => (
              <button key={c.id} onClick={() => setCandidate(c.id)}
                className={`w-full text-left text-xs font-mono px-3 py-1.5 rounded border transition-colors ${candidate === c.id
                  ? "border-[#4AFA9A]/30 text-[#4AFA9A] bg-[#4AFA9A]/5"
                  : "border-white/[0.07] text-white/40 hover:text-white/60"}`}>
                {c.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <button onClick={run} disabled={loading}
        className="inline-flex items-center gap-2 px-5 py-2 bg-[#4AFA9A] text-[#080A0F] text-xs font-mono font-semibold rounded hover:bg-[#3de88a] disabled:opacity-50 transition-colors mb-6">
        {loading ? <><Loader2 size={14} className="animate-spin" /> Checking...</> : "Check DDI →"}
      </button>

      {error && <p className="text-xs text-red-400/70 mb-4">{error}</p>}

      <ErrorBoundary fallbackLabel="DDI results failed to load.">
        {!result && !loading && <EmptyState label="Select a candidate drug and run DDI check" icon="💊" />}

        {result && (
          <div className="space-y-3">
            {/* Score */}
            <div className="panel panel-accent p-4 text-center mb-4">
              <span className="text-3xl font-mono font-bold" style={{ color: scoreColor(result.score) }}>{formatScore(result.score)}</span>
              <span className="block text-[10px] font-mono text-white/30 mt-1">DDI Safety Score · {result.n_interactions} interaction{result.n_interactions !== 1 ? "s" : ""} found</span>
            </div>

            {result.interactions.length > 0
              ? result.interactions.map((int, i) => <DDICard key={i} interaction={int} index={i} />)
              : <div className="panel p-4 text-center"><span className="text-xs text-[#4AFA9A]/60 font-mono">No interactions detected ✓</span></div>
            }
          </div>
        )}
      </ErrorBoundary>
    </div>
  );
}
