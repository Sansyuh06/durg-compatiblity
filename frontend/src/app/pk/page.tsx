"use client";
import { useState } from "react";
import { Loader2 } from "lucide-react";
import { getPKCurve } from "@/lib/api";
import type { PKCurve } from "@/types";
import PKChart from "@/components/PKChart";
import ErrorBoundary from "@/components/ErrorBoundary";
import EmptyState from "@/components/EmptyState";

const DRUGS = [
  { id: "vpa", label: "Valproic Acid" },
  { id: "ltg", label: "Lamotrigine" },
  { id: "lev", label: "Levetiracetam" },
  { id: "tpm", label: "Topiramate" },
  { id: "zns", label: "Zonisamide" },
];

export default function PKPage() {
  const [drug, setDrug] = useState("vpa");
  const [dose, setDose] = useState("1000");
  const [doses, setDoses] = useState("2");
  const [cyp, setCyp] = useState("normal");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<PKCurve | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true); setError(null);
    try {
      const result = await getPKCurve(drug, Number(dose), Number(doses), cyp);
      setData(result);
    } catch (e) { setError(e instanceof Error ? e.message : "PK simulation failed"); }
    finally { setLoading(false); }
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <h1 className="text-lg text-white/80 font-medium mb-1">Pharmacokinetic Modeling</h1>
      <p className="text-xs text-white/30 mb-6">Steady-state concentration curves with therapeutic range validation</p>

      <div className="panel p-4 mb-6">
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div>
            <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Drug</label>
            <select value={drug} onChange={e => setDrug(e.target.value)}
              className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none">
              {DRUGS.map(d => <option key={d.id} value={d.id}>{d.label}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Daily Dose (mg)</label>
            <input type="number" value={dose} onChange={e => setDose(e.target.value)}
              className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none" />
          </div>
          <div>
            <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Doses/Day</label>
            <select value={doses} onChange={e => setDoses(e.target.value)}
              className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none">
              <option value="1">QD (1x)</option>
              <option value="2">BID (2x)</option>
              <option value="3">TID (3x)</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">CYP2C9</label>
            <select value={cyp} onChange={e => setCyp(e.target.value)}
              className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none">
              {["normal", "intermediate", "poor"].map(v => <option key={v}>{v}</option>)}
            </select>
          </div>
        </div>
        <button onClick={run} disabled={loading}
          className="inline-flex items-center gap-2 px-5 py-2 bg-[#4AFA9A] text-[#080A0F] text-xs font-mono font-semibold rounded hover:bg-[#3de88a] disabled:opacity-50 transition-colors">
          {loading ? <><Loader2 size={14} className="animate-spin" /> Simulating...</> : "Generate PK Curve →"}
        </button>
      </div>

      {error && <p className="text-xs text-red-400/70 mb-4">{error}</p>}

      <ErrorBoundary fallbackLabel="PK chart failed to load.">
        {!data && !loading && <EmptyState label="Configure drug parameters and generate PK curve" icon="📈" />}
        {data && <PKChart data={data} />}
      </ErrorBoundary>
    </div>
  );
}
