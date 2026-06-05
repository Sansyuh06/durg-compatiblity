"use client";
import { motion } from "framer-motion";
import { Shield, Brain, Droplets } from "lucide-react";

interface AdmetData {
  score: number;
  lipinski?: { mw: number; logp: number; hbd: number; hba: number; violations: number; pass: boolean };
  bbb?: { probability: number; permeable: boolean };
  psa: number;
  rotatable_bonds: number;
  solubility_mg_ml: number;
  confidence: string;
}

export default function AdmetPanel({ data, drugName }: { data: AdmetData; drugName: string }) {
  const lip = data.lipinski;
  const bbb = data.bbb;
  const scoreColor = (data.score ?? 0) >= 80 ? "#4AFA9A" : (data.score ?? 0) >= 50 ? "#FACC15" : "#EF4444";

  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-xs font-mono tracking-wider text-white/40 uppercase">ADMET — {drugName}</h4>
        <span className="text-xs font-mono px-2 py-0.5 rounded" style={{ color: scoreColor, background: `${scoreColor}15` }}>
          {(data.score ?? 0).toFixed(0)}/100
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {/* Lipinski */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.4 }}
          className="bg-black/30 border border-white/5 shadow-inner rounded-lg p-4 relative overflow-hidden group"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-[#60A5FA]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="flex items-center gap-2 mb-3 relative z-10">
            <Shield size={14} className="text-[#60A5FA]" />
            <span className="text-[10px] font-sans font-semibold text-white/50 uppercase tracking-widest">Lipinski</span>
          </div>
          {lip ? (
            <div className="space-y-1.5 relative z-10">
              {[
                { k: "MW", v: lip.mw?.toFixed(1), ok: (lip.mw ?? 0) <= 500 },
                { k: "LogP", v: lip.logp?.toFixed(2), ok: (lip.logp ?? 0) <= 5 },
                { k: "HBD", v: lip.hbd, ok: (lip.hbd ?? 0) <= 5 },
                { k: "HBA", v: lip.hba, ok: (lip.hba ?? 0) <= 10 },
              ].map(r => (
                <div key={r.k} className="flex justify-between items-center text-[11px] font-mono border-b border-white/[0.02] pb-1 mb-1">
                  <span className="text-white/40">{r.k}</span>
                  <span className={r.ok ? "text-[#4AFA9A] font-bold" : "text-[#EF4444] font-bold"}>{r.v ?? "—"}</span>
                </div>
              ))}
              <div className="text-[10px] font-mono text-center mt-3 pt-2 border-t border-white/[0.05]">
                <span className={`px-2 py-1 rounded ${lip.pass ? "bg-[#4AFA9A]/10 text-[#4AFA9A]" : "bg-[#FACC15]/10 text-[#FACC15]"}`}>
                  {lip.violations ?? 0} VIOLATION{(lip.violations ?? 0) !== 1 ? "S" : ""} — {lip.pass ? "PASS" : "FAIL"}
                </span>
              </div>
            </div>
          ) : <span className="text-[10px] text-white/20">N/A</span>}
        </motion.div>

        {/* BBB */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="bg-black/30 border border-white/5 shadow-inner rounded-lg p-4 relative overflow-hidden group"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-[#F472B6]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="flex items-center gap-2 mb-3 relative z-10">
            <Brain size={14} className="text-[#F472B6]" />
            <span className="text-[10px] font-sans font-semibold text-white/50 uppercase tracking-widest">Blood-Brain Barrier</span>
          </div>
          {bbb ? (
            <div className="text-center space-y-3 relative z-10 py-2">
              <div className="relative inline-block">
                <span className="text-4xl font-mono font-bold tracking-tighter" style={{ color: bbb.permeable ? "#4AFA9A" : "#FACC15" }}>
                  {((bbb.probability ?? 0) * 100).toFixed(0)}<span className="text-xl text-white/30 ml-1">%</span>
                </span>
              </div>
              <span className={`block text-[10px] font-mono font-bold tracking-widest uppercase ${bbb.permeable ? "text-[#4AFA9A]" : "text-[#FACC15]"}`}>
                {bbb.permeable ? "PERMEABLE" : "NON-PERMEABLE"}
              </span>
            </div>
          ) : <span className="text-[10px] text-white/20">N/A</span>}
        </motion.div>

        {/* Solubility & PSA */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.4 }}
          className="bg-black/30 border border-white/5 shadow-inner rounded-lg p-4 relative overflow-hidden group"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-[#38BDF8]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="flex items-center gap-2 mb-3 relative z-10">
            <Droplets size={14} className="text-[#38BDF8]" />
            <span className="text-[10px] font-sans font-semibold text-white/50 uppercase tracking-widest">Physicochemical</span>
          </div>
          <div className="space-y-2 relative z-10">
            {[
              { k: "Polar Surface Area", v: `${(data.psa ?? 0).toFixed(1)} Å²` },
              { k: "Rotatable Bonds", v: data.rotatable_bonds ?? "—" },
              { k: "Solubility", v: `${(data.solubility_mg_ml ?? 0).toFixed(2)} mg/mL` },
            ].map((r, i) => (
              <div key={r.k} className={`flex justify-between items-center text-[11px] font-mono ${i !== 2 ? "border-b border-white/[0.02] pb-2 mb-2" : ""}`}>
                <span className="text-white/40">{r.k}</span>
                <span className="text-white/80 font-bold">{r.v}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
