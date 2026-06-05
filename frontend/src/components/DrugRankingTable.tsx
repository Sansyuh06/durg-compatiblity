"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";
import type { DrugRanking } from "@/types";
import { scoreColor, recommendationColor, formatScore } from "@/lib/utils";
import ScoreBar from "./ScoreBar";

export default function DrugRankingTable({ rankings }: { rankings: DrugRanking[] }) {
  const [expanded, setExpanded] = useState<string | null>(rankings[0]?.drug_id || null);

  return (
    <div className="space-y-3">
      {rankings.map((drug, i) => {
        const isExpanded = expanded === drug.drug_id;
        
        return (
          <motion.div
            key={drug.drug_id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06, duration: 0.4 }}
            className={`group panel overflow-hidden transition-all duration-300 ${isExpanded ? "border-[#4AFA9A]/30 shadow-[0_4px_30px_-10px_rgba(74,250,154,0.15)]" : "hover:border-white/20"}`}
          >
            {/* Top Rank Indicator Line */}
            {i === 0 && (
              <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[#4AFA9A]/60 to-transparent" />
            )}

            <div 
              className="flex items-center gap-4 px-5 py-4 cursor-pointer select-none relative z-10"
              onClick={() => setExpanded(isExpanded ? null : drug.drug_id)}
            >
              {/* Subtle hover gradient */}
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/[0.02] to-white/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

              {/* Rank badge */}
              <div className="w-8 h-8 flex items-center justify-center rounded-lg text-xs font-mono font-bold shrink-0 shadow-inner"
                style={{ background: i === 0 ? "linear-gradient(135deg, rgba(74,250,154,0.2), rgba(74,250,154,0.05))" : "rgba(255,255,255,0.03)", 
                         color: i === 0 ? "#4AFA9A" : "rgba(255,255,255,0.5)",
                         border: `1px solid ${i === 0 ? "rgba(74,250,154,0.2)" : "transparent"}` }}>
                {drug.rank}
              </div>

              {/* Drug name */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-base font-semibold tracking-tight transition-colors ${isExpanded ? "text-white" : "text-white/80 group-hover:text-white"}`}>
                    {drug.drug_name}
                  </span>
                  {drug.breakdown.ddi.n_interactions && drug.breakdown.ddi.n_interactions > 0 ? (
                    <span className="tag tag-red text-[9px] px-1.5 py-0.5 animate-pulse-glow border-red-500/30">
                      {drug.breakdown.ddi.n_interactions} DDI ALERT
                    </span>
                  ) : null}
                </div>
                <span className="text-[10px] font-mono text-white/30 uppercase tracking-widest">{drug.drug_id}</span>
              </div>

              {/* Recommendation badge */}
              <div className="text-[10px] font-mono tracking-wider px-3 py-1 rounded-full font-bold uppercase"
                style={{ color: recommendationColor(drug.recommendation), background: `${recommendationColor(drug.recommendation)}15`, border: `1px solid ${recommendationColor(drug.recommendation)}30` }}>
                {drug.recommendation}
              </div>

              {/* Score */}
              <div className="text-2xl font-mono font-bold w-16 text-right tracking-tighter"
                style={{ color: scoreColor(drug.composite_score) }}>
                {formatScore(drug.composite_score)}
              </div>

              {/* Chevron */}
              <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} className="text-white/20 shrink-0 ml-2">
                <ChevronDown size={16} />
              </motion.div>
            </div>

            {/* Expanded details (Framer Motion AnimatePresence) */}
            <AnimatePresence initial={false}>
              {isExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                  className="overflow-hidden bg-black/20"
                >
                  <div className="px-5 pb-5 pt-3 border-t border-white/[0.05]">
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                      {(["efficacy", "safety", "genomic", "admet", "ddi"] as const).map((key, j) => (
                        <ScoreBar key={key} label={key} value={drug.breakdown[key].score} delay={j * 0.05} />
                      ))}
                    </div>
                    {drug.flags.length > 0 && (
                      <div className="mt-5 flex flex-wrap gap-2">
                        {drug.flags.map((f, j) => (
                          <span key={j} className="tag tag-amber text-[9px] px-2 py-1 bg-amber-500/5 border-amber-500/20 text-amber-400/80">
                            ⚠ {f}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        );
      })}
    </div>
  );
}
