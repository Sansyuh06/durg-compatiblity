"use client";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from "recharts";

interface VQEData {
  iterations: number[];
  energies: number[];
  ground_state_energy: number;
  convergence_threshold: number;
  binding_affinity_score: number;
  qubit_count: number;
  ansatz: string;
  drug_id?: string;
  drug_name?: string;
}

export default function VQEChart({ data }: { data: VQEData }) {
  const points = (data.iterations ?? []).map((it: number, i: number) => ({
    iteration: it,
    energy: (data.energies ?? [])[i] ?? 0,
  }));
  const gse = data.ground_state_energy ?? 0;

  return (
    <div className="panel panel-accent p-4">
      <h3 className="text-xs font-mono tracking-wider text-white/40 mb-1 uppercase">
        Quantum Binding — VQE Convergence
      </h3>
      <p className="text-[10px] text-white/20 mb-4">
        {data.ansatz ?? "EfficientSU2"} ansatz · {data.qubit_count ?? 4} qubits · {data.drug_name ?? data.drug_id ?? "drug"}
      </p>

      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={points} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="iteration" tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }}
            label={{ value: "VQE Iteration", position: "insideBottom", offset: -2, style: { fontSize: 10, fill: "rgba(255,255,255,0.25)" } }} />
          <YAxis tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }}
            label={{ value: "Energy (Ha)", angle: -90, position: "insideLeft", style: { fontSize: 10, fill: "rgba(255,255,255,0.25)" } }} />
          <ReferenceLine y={gse} stroke="#4AFA9A" strokeDasharray="6 3" strokeWidth={1} label={{ value: `GSE: ${gse.toFixed(4)} Ha`, position: "right", style: { fontSize: 9, fill: "#4AFA9A" } }} />
          <Tooltip contentStyle={{ background: "#0D1117", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, fontSize: 11, color: "#e8f0fe" }} />
          <Line type="monotone" dataKey="energy" stroke="#A78BFA" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>

      <div className="grid grid-cols-3 gap-3 mt-4">
        {[
          { label: "Ground State", value: `${gse.toFixed(4)} Ha` },
          { label: "Binding Affinity", value: `${(data.binding_affinity_score ?? 0).toFixed(1)}%` },
          { label: "Convergence", value: `${(data.convergence_threshold ?? 0).toFixed(6)}` },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white/[0.03] rounded p-2 text-center">
            <span className="block text-[9px] font-mono text-white/30 uppercase">{label}</span>
            <span className="text-xs font-mono text-[#A78BFA]">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
