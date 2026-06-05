"use client";
import { motion } from "framer-motion";
import { Target } from "lucide-react";

interface OffTargetData {
  score: number;
  targets: { protein: string; activity: string; pchembl: number; source: string }[];
  confidence: string;
}

export default function OffTargetPanel({ data, drugName }: { data: OffTargetData; drugName: string }) {
  const targets = data.targets ?? [];
  const scoreColor = (data.score ?? 0) >= 80 ? "#4AFA9A" : (data.score ?? 0) >= 50 ? "#FACC15" : "#EF4444";

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="panel p-4"
    >
      <div className="flex items-center justify-between mb-4 border-b border-white/[0.05] pb-3">
        <div className="flex items-center gap-2">
          <Target size={14} className="text-[#FFAB40]" />
          <h4 className="text-[11px] font-sans font-semibold tracking-wider text-white/50 uppercase">
            Off-Target Panel — {drugName}
          </h4>
        </div>
        <div className="flex items-center gap-2">
          <span className="tag tag-amber text-[8px]">{data.confidence ?? "—"}</span>
          <span className="text-xs font-mono px-2 py-0.5 rounded" style={{ color: scoreColor, background: `${scoreColor}15` }}>
            {(data.score ?? 0).toFixed(1)}/100
          </span>
        </div>
      </div>

      {targets.length > 0 ? (
        <div className="flex flex-col gap-2">
          <div className="grid grid-cols-4 px-3 text-[9px] font-mono tracking-widest text-white/30 uppercase mb-1">
            <div className="col-span-1">Protein Target</div>
            <div className="col-span-1">Activity</div>
            <div className="col-span-1 text-right">pChEMBL</div>
            <div className="col-span-1 text-right">Source</div>
          </div>
          
          <div className="space-y-1">
            {targets.map((t, i) => {
              const isHighRisk = (t.pchembl ?? 0) >= 6;
              const isMedRisk = (t.pchembl ?? 0) >= 5 && !isHighRisk;
              const rowColor = isHighRisk ? "#EF4444" : isMedRisk ? "#FACC15" : "#4AFA9A";
              
              return (
                <motion.div 
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 + 0.2, duration: 0.3 }}
                  className="grid grid-cols-4 items-center px-3 py-2.5 bg-black/30 border border-white/5 rounded hover:bg-white/[0.02] transition-colors relative overflow-hidden group"
                >
                  {/* Subtle warning glow for high risk */}
                  {isHighRisk && (
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[#EF4444]/5 to-transparent animate-[shimmer_3s_infinite] pointer-events-none" />
                  )}

                  <div className="col-span-1 text-[11px] font-sans font-semibold text-white/70 truncate relative z-10">{t.protein}</div>
                  <div className="col-span-1 text-[10px] font-mono text-white/40 truncate relative z-10">{t.activity}</div>
                  <div className="col-span-1 text-right relative z-10">
                    <span 
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${isHighRisk ? "bg-[#EF4444]/10 border border-[#EF4444]/20" : ""}`}
                      style={{ color: rowColor }}
                    >
                      {(t.pchembl ?? 0).toFixed(2)}
                    </span>
                  </div>
                  <div className="col-span-1 text-[9px] font-mono text-white/20 text-right truncate relative z-10">{t.source}</div>
                </motion.div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-6 text-center bg-black/20 rounded border border-white/[0.02] border-dashed">
          <Target size={20} className="text-white/10 mb-2" />
          <p className="text-[10px] font-mono text-white/30 tracking-widest uppercase">No off-target interactions detected</p>
        </div>
      )}
    </motion.div>
  );
}
