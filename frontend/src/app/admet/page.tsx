"use client";
import { useState } from "react";
import { Loader2, Pill } from "lucide-react";
import { getDrugProperties, getToxicity, getFaersSignals, getProteinTarget } from "@/lib/api";
import AdmetPanel from "@/components/AdmetPanel";
import FaersPanel from "@/components/FaersPanel";
import OffTargetPanel from "@/components/OffTargetPanel";
import ErrorBoundary from "@/components/ErrorBoundary";
import EmptyState from "@/components/EmptyState";

const DRUGS = [
  { id: "vpa", name: "Valproic Acid" },
  { id: "ltg", name: "Lamotrigine" },
  { id: "lev", name: "Levetiracetam" },
  { id: "tpm", name: "Topiramate" },
  { id: "zns", name: "Zonisamide" },
];

export default function AdmetPage() {
  const [drugId, setDrugId] = useState("vpa");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [props, setProps] = useState<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [tox, setTox] = useState<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [faers, setFaers] = useState<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [target, setTarget] = useState<any>(null);

  const run = async () => {
    setLoading(true); setError(null);
    try {
      const [p, t, f, pt] = await Promise.all([
        getDrugProperties(drugId),
        getToxicity(drugId),
        getFaersSignals(drugId),
        getProteinTarget(drugId),
      ]);
      setProps(p); setTox(t); setFaers(f); setTarget(pt);
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to load data"); }
    finally { setLoading(false); }
  };

  const drugName = DRUGS.find(d => d.id === drugId)?.name ?? drugId;

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      <div>
        <h1 className="text-lg text-white/80 font-medium mb-1 flex items-center gap-2">
          <Pill size={20} className="text-[#38BDF8]" />
          ADMET & Toxicology Dashboard
        </h1>
        <p className="text-xs text-white/30">
          Drug absorption, distribution, metabolism, excretion, toxicity · FAERS signals · Off-target binding
        </p>
      </div>

      {/* Drug selector */}
      <div className="panel p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Select Drug</label>
            <select value={drugId} onChange={e => setDrugId(e.target.value)}
              className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none">
              {DRUGS.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <button onClick={run} disabled={loading}
            className="inline-flex items-center gap-2 px-5 py-2 bg-[#4AFA9A] text-[#080A0F] text-xs font-mono font-semibold rounded hover:bg-[#3de88a] disabled:opacity-50 transition-colors mt-4">
            {loading ? <><Loader2 size={14} className="animate-spin" /> Loading...</> : "Analyze Drug →"}
          </button>
        </div>
        {error && <p className="text-xs text-red-400/70 mt-2">{error}</p>}
      </div>

      <ErrorBoundary fallbackLabel="ADMET analysis failed to load">
        {!props && !loading && <EmptyState label="Select a drug and click Analyze to view ADMET profile" icon="💊" />}

        {/* Drug Properties */}
        {props && (
          <div className="panel p-4">
            <h3 className="text-xs font-mono tracking-wider text-white/40 mb-3 uppercase">
              Drug Properties — {drugName}
            </h3>
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: "Mol. Weight", value: `${(props.molecular_weight ?? 0).toFixed(1)} Da` },
                { label: "LogP", value: (props.logp ?? 0).toFixed(2) },
                { label: "PSA", value: `${(props.psa ?? 0).toFixed(1)} Å²` },
                { label: "Class", value: props.therapeutic_class ?? "—" },
              ].map(m => (
                <div key={m.label} className="bg-white/[0.03] rounded p-2 text-center">
                  <span className="block text-[9px] font-mono text-white/30 uppercase">{m.label}</span>
                  <span className="text-xs font-mono text-white/70">{m.value}</span>
                </div>
              ))}
            </div>
            {props.smiles && (
              <div className="mt-3 bg-white/[0.02] rounded p-2">
                <span className="text-[9px] font-mono text-white/20">SMILES: </span>
                <code className="text-[10px] font-mono text-white/40 break-all">{props.smiles}</code>
              </div>
            )}
          </div>
        )}

        {/* Toxicology */}
        {tox && (
          <div className="panel p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-mono tracking-wider text-white/40 uppercase">
                Tox21 / EPA Toxicity Profile — {drugName}
              </h3>
              <span className="tag text-[8px]" style={{
                color: tox.overall_risk === "LOW" ? "#4AFA9A" : tox.overall_risk === "MODERATE" ? "#FACC15" : "#EF4444",
                borderColor: tox.overall_risk === "LOW" ? "rgba(74,250,154,0.2)" : tox.overall_risk === "MODERATE" ? "rgba(250,204,21,0.2)" : "rgba(239,68,68,0.2)",
              }}>
                {tox.overall_risk ?? "—"} RISK
              </span>
            </div>
            {tox.endpoints && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {(tox.endpoints as { name: string; active: boolean; confidence: number }[]).map(
                  (ep: { name: string; active: boolean; confidence: number }) => (
                  <div key={ep.name} className="bg-white/[0.03] rounded p-2 flex items-center justify-between">
                    <span className="text-[10px] font-mono text-white/40 truncate">{ep.name}</span>
                    <span className={`text-[10px] font-mono ${ep.active ? "text-[#EF4444]" : "text-[#4AFA9A]"}`}>
                      {ep.active ? "ACTIVE" : "INACTIVE"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* FAERS */}
        {faers && <FaersPanel data={faers} />}

        {/* Off-Target */}
        {target && <OffTargetPanel data={target} drugName={drugName} />}
      </ErrorBoundary>
    </div>
  );
}
