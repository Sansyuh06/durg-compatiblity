"use client";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceArea, ResponsiveContainer } from "recharts";
import type { PKCurve } from "@/types";

export default function PKChart({ data }: { data: PKCurve }) {
  const points = data.series.t_h.map((t, i) => ({ t, c: data.series.c_ug_ml[i] }));
  const d = data.derived;

  const cmax = d?.cmax_ug_ml ?? 0;
  const cavg = d?.cavg_ug_ml ?? 0;
  const cmin = d?.cmin_ug_ml ?? 0;
  const tHalf = d?.t_half_adjusted_h ?? d?.t_half_h ?? 0;
  const thMin = d?.therapeutic_min ?? 0;
  const thMax = d?.therapeutic_max ?? 0;
  const status = d?.status ?? "—";

  return (
    <div className="panel panel-accent p-4">
      <h3 className="text-xs font-mono tracking-wider text-white/40 mb-4 uppercase">PK Curve — {data.drug_name ?? data.drug_id ?? "Drug"}</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={points} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="t" tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }} label={{ value: "Time (h)", position: "insideBottom", offset: -2, style: { fontSize: 10, fill: "rgba(255,255,255,0.25)" } }} />
          <YAxis tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }} label={{ value: "Conc (µg/mL)", angle: -90, position: "insideLeft", style: { fontSize: 10, fill: "rgba(255,255,255,0.25)" } }} />
          {thMin > 0 && thMax > 0 && (
            <ReferenceArea y1={thMin} y2={thMax} fill="#4AFA9A" fillOpacity={0.06} strokeDasharray="3 3" stroke="#4AFA9A20" />
          )}
          <Tooltip contentStyle={{ background: "#0D1117", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6, fontSize: 11, color: "#e8f0fe" }} />
          <Line type="monotone" dataKey="c" stroke="#4AFA9A" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>

      {/* Metric tiles */}
      <div className="grid grid-cols-5 gap-3 mt-4">
        {[
          { label: "Cmax", value: `${cmax.toFixed(2)} µg/mL` },
          { label: "Cavg", value: `${cavg.toFixed(2)} µg/mL` },
          { label: "Cmin", value: `${cmin.toFixed(2)} µg/mL` },
          { label: "t½", value: `${tHalf.toFixed(1)} h` },
          { label: "Status", value: status },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white/[0.03] rounded p-2 text-center">
            <span className="block text-[9px] font-mono text-white/30 uppercase">{label}</span>
            <span className="text-xs font-mono text-white/70">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
