"use client";
import { motion } from "framer-motion";
import type { DrugRanking } from "@/types";
import { scoreColor, formatScore } from "@/lib/utils";
import ScoreBar from "./ScoreBar";

export default function DrugCompareCard({ drug, index }: { drug: DrugRanking; index: number }) {
  const isWinner = drug.rank === 1;
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.5 }}
      className="panel panel-accent min-w-[220px] max-w-[260px] p-4 flex-shrink-0"
      style={isWinner ? { borderColor: "#4AFA9A30" } : {}}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-white/80">{drug.drug_name}</span>
        {isWinner && <span className="tag tag-green text-[9px]">WINNER</span>}
        {drug.recommendation === "NOT_RECOMMENDED" && <span className="tag tag-red text-[9px]">AVOID</span>}
      </div>

      {/* Composite score */}
      <div className="text-center mb-4">
        <span className="text-3xl font-mono font-bold" style={{ color: scoreColor(drug.composite_score) }}>
          {formatScore(drug.composite_score)}
        </span>
        <span className="text-xs font-mono text-white/25 block mt-1">composite</span>
      </div>

      {/* Breakdown */}
      <div className="space-y-2">
        {(["efficacy", "safety", "genomic", "admet", "ddi"] as const).map((key, j) => (
          <ScoreBar key={key} label={key} value={drug.breakdown[key].score} delay={index * 0.1 + j * 0.04} height={4} />
        ))}
      </div>

      {/* Flags */}
      {drug.flags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {drug.flags.slice(0, 2).map((f, j) => <span key={j} className="tag tag-amber text-[8px]">{f}</span>)}
        </div>
      )}
    </motion.div>
  );
}
