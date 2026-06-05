"use client";
import { useState } from "react";
import { Loader2 } from "lucide-react";
import { matchTrials, matchTrialsDemo } from "@/lib/api";
import { GABI_PRESET } from "@/lib/presets";
import type { TrialsResult } from "@/types";
import TrialCard from "@/components/TrialCard";
import ErrorBoundary from "@/components/ErrorBoundary";
import EmptyState from "@/components/EmptyState";

export default function TrialsPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TrialsResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runDemo = async () => {
    setLoading(true); setError(null);
    try {
      const data = await matchTrialsDemo();
      setResult(data);
    } catch (e) { setError(e instanceof Error ? e.message : "Trial matching failed"); }
    finally { setLoading(false); }
  };

  const runCustom = async () => {
    setLoading(true); setError(null);
    try {
      const data = await matchTrials(GABI_PRESET);
      setResult(data);
    } catch (e) { setError(e instanceof Error ? e.message : "Trial matching failed"); }
    finally { setLoading(false); }
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <h1 className="text-lg text-white/80 font-medium mb-1">Clinical Trial Matching</h1>
      <p className="text-xs text-white/30 mb-6">Match patients to eligible clinical trials from ClinicalTrials.gov</p>

      <div className="flex gap-3 mb-8">
        <button onClick={runDemo} disabled={loading}
          className="inline-flex items-center gap-2 px-5 py-2 bg-[#4AFA9A] text-[#080A0F] text-xs font-mono font-semibold rounded hover:bg-[#3de88a] disabled:opacity-50 transition-colors">
          {loading ? <><Loader2 size={14} className="animate-spin" /> Matching...</> : "Match Demo Patient (Gabi)"}
        </button>
        <button onClick={runCustom} disabled={loading}
          className="inline-flex items-center gap-2 px-5 py-2 border border-white/10 text-white/50 text-xs font-mono rounded hover:border-white/20 transition-colors">
          Custom Match
        </button>
      </div>

      {error && <p className="text-xs text-red-400/70 mb-4">{error}</p>}

      <ErrorBoundary fallbackLabel="Trial results failed to load.">
        {!result && !loading && <EmptyState label="Run trial matching to find eligible studies" icon="🏥" />}

        {result && (
          <div className="space-y-3">
            <div className="flex items-center gap-3 mb-4">
              <span className="tag">{result.total_screened} screened</span>
              <span className="tag tag-green">{result.total_matched} matched</span>
            </div>
            {result.trials.map((t, i) => <TrialCard key={t.nct_id} trial={t} index={i} />)}
          </div>
        )}
      </ErrorBoundary>
    </div>
  );
}
