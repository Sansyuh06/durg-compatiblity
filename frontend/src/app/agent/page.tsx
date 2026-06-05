"use client";
import { useState, useEffect } from "react";
import { Loader2, Play, FileText } from "lucide-react";
import { runAgent } from "@/lib/api";
import { DEMO_AGENT_TRANSCRIPT } from "@/lib/presets";
import type { AgentResult, AgentStep as AgentStepType } from "@/types";
import AgentStepComponent from "@/components/AgentStep";
import ErrorBoundary from "@/components/ErrorBoundary";
import EmptyState from "@/components/EmptyState";

export default function AgentPage() {
  const [task, setTask] = useState("easy");
  const [model, setModel] = useState("claude-3-5-haiku-20241022");
  const [apiKey, setApiKey] = useState("");
  const [maxSteps, setMaxSteps] = useState(8);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Persist/restore API key from sessionStorage
  useEffect(() => {
    const saved = sessionStorage.getItem("quantamed_anthropic_key");
    if (saved) setApiKey(saved);
  }, []);

  useEffect(() => {
    if (apiKey) sessionStorage.setItem("quantamed_anthropic_key", apiKey);
  }, [apiKey]);

  const run = async () => {
    if (!apiKey.trim()) { setError("Enter your Anthropic API key"); return; }
    setLoading(true); setError(null);
    try {
      const data = await runAgent({ task_id: task, model, max_steps: maxSteps, anthropic_api_key: apiKey });
      setResult(data);
    } catch (e) { setError(e instanceof Error ? e.message : "Agent run failed"); }
    finally { setLoading(false); }
  };

  const loadDemo = () => {
    setResult({
      transcript: DEMO_AGENT_TRANSCRIPT as AgentStepType[],
      final_score: 0.92,
      final_message: "Correct assessment. Metformin's lactic acidosis risk is well-characterized and adequately managed by the existing Black Box Warning. Monitor recommendation is appropriate.",
      steps_taken: 5,
      task_id: "easy",
    });
    setError(null);
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <h1 className="text-lg text-white/80 font-medium mb-1">AI Agent Runner</h1>
      <p className="text-xs text-white/30 mb-6">Autonomous pharmacovigilance triage agent powered by Claude</p>

      <div className="panel p-4 space-y-3 mb-6">
        {/* Config row */}
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Task</label>
            <select value={task} onChange={e => setTask(e.target.value)}
              className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none">
              <option value="easy">Easy (Metformin)</option>
              <option value="medium">Medium (Rofecoxib)</option>
              <option value="hard">Hard (Isotretinoin)</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Model</label>
            <select value={model} onChange={e => setModel(e.target.value)}
              className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none">
              <option value="claude-3-5-haiku-20241022">Haiku 3.5</option>
              <option value="claude-sonnet-4-20250514">Sonnet 4</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Max Steps</label>
            <input type="number" value={maxSteps} onChange={e => setMaxSteps(Number(e.target.value))} min={3} max={15}
              className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none" />
          </div>
        </div>

        {/* API Key */}
        <div>
          <label className="text-[10px] font-mono text-white/30 uppercase block mb-1">Anthropic API Key</label>
          <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="sk-ant-..."
            className="w-full bg-white/[0.03] border border-white/[0.07] rounded px-3 py-1.5 text-xs text-white/70 outline-none focus:border-[#4AFA9A]/30 placeholder:text-white/15" />
          <span className="text-[9px] text-white/20 mt-1 block">Stored in sessionStorage only — never sent to our servers.</span>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3">
          <button onClick={run} disabled={loading}
            className="inline-flex items-center gap-2 px-5 py-2 bg-[#4AFA9A] text-[#080A0F] text-xs font-mono font-semibold rounded hover:bg-[#3de88a] disabled:opacity-50 transition-colors">
            {loading ? <><Loader2 size={14} className="animate-spin" /> Running Agent...</> : <><Play size={14} /> Run Agent</>}
          </button>
          <button onClick={loadDemo}
            className="inline-flex items-center gap-2 px-5 py-2 border border-white/10 text-white/50 text-xs font-mono rounded hover:border-white/20 hover:text-white/70 transition-colors">
            <FileText size={14} /> Demo Transcript
          </button>
        </div>
      </div>

      {error && <p className="text-xs text-red-400/70 mb-4">{error}</p>}

      <ErrorBoundary fallbackLabel="Agent transcript failed to load.">
        {!result && !loading && <EmptyState label="Run the agent or load a demo transcript" icon="🤖" />}

        {result && (
          <div className="space-y-2">
            {/* Final score */}
            <div className="panel panel-accent p-4 mb-4 text-center">
              <span className="text-3xl font-mono font-bold text-[#4AFA9A]">{result.final_score.toFixed(4)}</span>
              <span className="block text-[10px] font-mono text-white/30 mt-1">{result.steps_taken} steps · {result.task_id}</span>
              {result.final_message && <p className="text-xs text-white/40 mt-2 max-w-lg mx-auto">{result.final_message}</p>}
            </div>

            {/* Transcript */}
            <div className="space-y-2">
              {result.transcript.map((s, i) => <AgentStepComponent key={i} step={s} index={i} />)}
            </div>
          </div>
        )}
      </ErrorBoundary>
    </div>
  );
}
