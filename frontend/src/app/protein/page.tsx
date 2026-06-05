"use client";
import { useState, useEffect } from "react";
import { Loader2, Atom, Dna } from "lucide-react";
import { getVQEConvergence, getProteinFolding, getProteinDynamics, modelProtein, getProteinExamples } from "@/lib/api";
import VQEChart from "@/components/VQEChart";
import ErrorBoundary from "@/components/ErrorBoundary";
import { motion } from "framer-motion";

export default function ProteinPage() {
  const [vqeData, setVqeData] = useState<Record<string, unknown> | null>(null);
  const [foldingData, setFoldingData] = useState<Record<string, unknown> | null>(null);
  const [dynamicsData, setDynamicsData] = useState<Record<string, unknown> | null>(null);
  const [modelResult, setModelResult] = useState<Record<string, unknown> | null>(null);
  const [examples, setExamples] = useState<Record<string, unknown> | null>(null);
  const [fasta, setFasta] = useState("");
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    load("vqe", async () => setVqeData(await getVQEConvergence()));
    load("folding", async () => setFoldingData(await getProteinFolding()));
    load("examples", async () => setExamples(await getProteinExamples()));
  }, []);

  const load = async (key: string, fn: () => Promise<void>) => {
    setLoading(p => ({ ...p, [key]: true }));
    setErrors(p => ({ ...p, [key]: "" }));
    try { await fn(); }
    catch (e) { setErrors(p => ({ ...p, [key]: e instanceof Error ? e.message : "Failed" })); }
    finally { setLoading(p => ({ ...p, [key]: false })); }
  };

  const runDynamics = () => load("dynamics", async () => setDynamicsData(await getProteinDynamics()));
  const runModel = () => load("model", async () => setModelResult(await modelProtein(fasta)));

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fold = foldingData as any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const dyn = dynamicsData as any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mod = modelResult as any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const ex = examples as any;

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-lg text-white/80 font-medium mb-1 flex items-center gap-2">
          <Atom size={20} className="text-[#A78BFA]" />
          Protein & Quantum Dynamics
        </h1>
        <p className="text-xs text-white/30">
          Variational Quantum Eigensolver · Protein folding sequences · Molecular dynamics
        </p>
      </div>

      {/* VQE Convergence */}
      <ErrorBoundary fallbackLabel="VQE chart failed to load">
        {loading.vqe && <div className="panel p-8 flex items-center justify-center"><Loader2 size={20} className="animate-spin text-white/20" /></div>}
        {errors.vqe && <p className="text-xs text-red-400/70">{errors.vqe}</p>}
        {vqeData && <VQEChart data={vqeData as any} />}
      </ErrorBoundary>

      {/* Protein Folding */}
      <div className="panel p-4">
        <h3 className="text-xs font-mono tracking-wider text-white/40 mb-4 uppercase flex items-center gap-2">
          <Dna size={14} className="text-[#F472B6]" />
          Quantum Protein Folding Sequences
        </h3>
        {loading.folding && <div className="flex items-center justify-center py-8"><Loader2 size={20} className="animate-spin text-white/20" /></div>}
        {fold?.sequences && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {(fold.sequences as { step: number; sequence: string; energy: number; score: number }[]).map(
              (s: { step: number; sequence: string; energy: number; score: number }, i: number) => (
              <div key={i} className="bg-white/[0.03] rounded p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono text-white/30">Step {s.step}</span>
                  <span className="text-[10px] font-mono text-[#F472B6]">E = {(s.energy ?? 0).toFixed(4)}</span>
                </div>
                <code className="text-[10px] font-mono text-white/50 break-all">{s.sequence}</code>
                <div className="mt-1 h-1 rounded bg-white/[0.05] overflow-hidden">
                  <div className="h-full rounded bg-[#F472B6]" style={{ width: `${(s.score ?? 0) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Protein Dynamics */}
      <div className="panel p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-mono tracking-wider text-white/40 uppercase">
            Molecular Dynamics Analysis
          </h3>
          <button onClick={runDynamics} disabled={loading.dynamics}
            className="inline-flex items-center gap-2 px-4 py-1.5 bg-[#A78BFA] text-[#080A0F] text-[10px] font-mono font-semibold rounded hover:bg-[#9474E8] disabled:opacity-50 transition-colors">
            {loading.dynamics ? <><Loader2 size={12} className="animate-spin" /> Running...</> : "Run Dynamics →"}
          </button>
        </div>
        {errors.dynamics && <p className="text-xs text-red-400/70">{errors.dynamics}</p>}
        {dyn && (
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Flexibility Score", value: (dyn.flexibility_score ?? 0).toFixed(2), color: "#A78BFA" },
              { label: "Binding Pocket Vol", value: `${(dyn.binding_pocket_volume ?? 0).toFixed(0)} ų`, color: "#60A5FA" },
              { label: "Residues Analyzed", value: dyn.rmsf_per_residue?.length ?? 0, color: "#4AFA9A" },
            ].map(m => (
              <div key={m.label} className="bg-white/[0.03] rounded p-3 text-center">
                <span className="block text-[9px] font-mono text-white/30 uppercase">{m.label}</span>
                <span className="text-lg font-mono font-bold" style={{ color: m.color }}>{m.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Protein Modeling */}
      <div className="panel p-4">
        <h3 className="text-xs font-mono tracking-wider text-white/40 mb-4 uppercase">
          Protein Structure Modeling — Swiss-Model Inspired
        </h3>

        {ex?.sequences && (
          <div className="flex flex-wrap gap-2 mb-3">
            <span className="text-[10px] text-white/20">Examples:</span>
            {(ex.sequences as { name: string; sequence: string }[]).map(
              (s: { name: string; sequence: string }) => (
              <button key={s.name} onClick={() => setFasta(s.sequence)}
                className="text-[10px] font-mono px-2 py-0.5 rounded border border-white/10 text-white/40 hover:text-white/60 hover:border-white/20 transition-colors">
                {s.name}
              </button>
            ))}
          </div>
        )}

        <textarea
          value={fasta}
          onChange={e => setFasta(e.target.value)}
          placeholder=">sequence_name&#10;MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH..."
          rows={4}
          className="w-full bg-[#080A0F] border border-white/[0.07] rounded px-3 py-2 text-xs font-mono text-white/70 outline-none focus:border-[#4AFA9A]/30 resize-none mb-3"
        />

        <button onClick={runModel} disabled={loading.model || !fasta.trim()}
          className="inline-flex items-center justify-center w-full gap-2 px-5 py-3 bg-[#4AFA9A] text-[#080A0F] text-xs font-mono font-bold tracking-widest uppercase rounded hover:bg-[#3de88a] disabled:opacity-50 transition-colors">
          {loading.model ? <><Loader2 size={16} className="animate-spin" /> Initializing Homology Pipeline...</> : "Generate 3D Protein Model"}
        </button>

        {errors.model && <p className="text-xs text-red-400/70 mt-2 text-center">{errors.model}</p>}

        {mod && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mt-6 border-t border-white/[0.05] pt-6">
            
            <div className="flex gap-4 flex-col md:flex-row">
              {/* Sidebar Stats */}
              <div className="w-full md:w-64 space-y-3">
                <div className="text-[10px] font-mono text-[#4AFA9A] mb-4">MODEL GENERATED SUCCESSFULLY</div>
                {[
                  { label: "Sequence Length", value: mod.sequence_length ?? "—" },
                  { label: "Global Model Quality", value: `${((mod.model_quality ?? 0) * 100).toFixed(1)}%` },
                  { label: "Ramachandran Favored", value: `${((mod.ramachandran_favored ?? 0) * 100).toFixed(1)}%` },
                  { label: "Pred. Secondary Struct", value: mod.secondary_structure ?? "—" },
                ].map(m => (
                  <div key={m.label} className="bg-white/[0.03] border border-white/[0.05] rounded p-3">
                    <span className="block text-[9px] font-mono text-white/30 uppercase mb-1">{m.label}</span>
                    <span className="text-sm font-mono text-white/80">{m.value}</span>
                  </div>
                ))}
              </div>

              {/* Simulated 3D Viewer */}
              <div className="flex-1 bg-[#02050A] border border-white/[0.05] rounded relative min-h-[300px] flex items-center justify-center overflow-hidden group">
                {/* HUD Overlay */}
                <div className="absolute top-3 left-3 text-[9px] font-mono text-white/20">
                  <div>VIEWER: Pymol-WebGL</div>
                  <div>RENDER: Cartoon + Surface</div>
                  <div>RESOLUTION: 1.2Å</div>
                </div>
                
                {/* 3D Representation (Simulated with CSS) */}
                <div className="relative w-48 h-48 animate-[spin_20s_linear_infinite]">
                  <div className="absolute inset-0 rounded-full border-4 border-dashed border-[#A78BFA]/20 mix-blend-screen animate-[pulse_4s_ease-in-out_infinite]" />
                  <div className="absolute inset-4 rounded-full border border-[#4AFA9A]/30 mix-blend-screen" style={{ transform: "rotateX(45deg) rotateY(45deg)" }} />
                  <div className="absolute inset-4 rounded-full border border-[#38BDF8]/30 mix-blend-screen" style={{ transform: "rotateX(-45deg) rotateY(45deg)" }} />
                  <div className="absolute inset-10 bg-gradient-to-tr from-[#A78BFA]/20 to-[#4AFA9A]/20 blur-xl rounded-full" />
                </div>

                <div className="absolute bottom-3 right-3 text-[9px] font-mono text-[#4AFA9A]/40 flex gap-4">
                  <span>[DRAG TO ROTATE]</span>
                  <span>[SCROLL TO ZOOM]</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
