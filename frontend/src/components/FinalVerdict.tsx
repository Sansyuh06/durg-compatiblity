"use client";
import { motion } from "framer-motion";
import { CheckCircle, AlertTriangle, XCircle, FileText } from "lucide-react";
import type { ExtendedDrugRanking } from "@/types";

export default function FinalVerdict({ rankings, disclaimer }: { rankings: ExtendedDrugRanking[]; disclaimer?: string }) {
  if (!rankings?.length) return null;

  const top = rankings[0];
  const avoid = rankings[rankings.length - 1];
  const icon = top.recommendation === "RECOMMENDED"
    ? <CheckCircle size={20} className="text-[#4AFA9A]" />
    : top.recommendation === "CONDITIONAL"
    ? <AlertTriangle size={20} className="text-[#FACC15]" />
    : <XCircle size={20} className="text-[#EF4444]" />;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="panel overflow-hidden"
    >
      <div className="flex items-center gap-2 p-5 border-b border-white/[0.05] bg-black/20">
        <FileText size={16} className="text-[#00D4FF]" />
        <h3 className="text-sm font-semibold tracking-wider text-white/80 uppercase">
          Final Recommendation — End-to-End Pipeline Verdict
        </h3>
      </div>

      <div className="p-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Top pick */}
          <div className="relative overflow-hidden rounded-xl bg-[#4AFA9A]/[0.02] border border-[#4AFA9A]/20 p-6 shadow-[0_0_30px_-5px_rgba(74,250,154,0.1)] group">
            <div className="absolute inset-0 bg-gradient-to-br from-[#4AFA9A]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="flex items-center gap-2 mb-3">
              {icon}
              <span className="text-xs font-mono tracking-wider text-white/50 uppercase">Top Recommendation</span>
            </div>
            
            <span className="text-4xl font-sans font-bold tracking-tight text-white mb-2 block">{top.drug_name}</span>
            
            <div className="mt-4 flex flex-col gap-2">
              <div className="flex items-center justify-between bg-black/40 rounded p-2 border border-white/5">
                <span className="text-[10px] font-mono text-white/40 uppercase">Composite Score</span>
                <span className="text-sm font-mono font-bold text-[#4AFA9A]">{(top.composite_score ?? 0).toFixed(1)} / 100</span>
              </div>
              <div className="flex items-center justify-between bg-black/40 rounded p-2 border border-white/5">
                <span className="text-[10px] font-mono text-white/40 uppercase">Action</span>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#4AFA9A]/10 text-[#4AFA9A] border border-[#4AFA9A]/20">{top.recommendation}</span>
              </div>
            </div>

            {top.pk_summary && (
              <div className="mt-4 text-[10px] font-mono text-white/30 border-t border-white/[0.05] pt-3">
                PK TARGET: {(top.pk_summary.css_avg ?? 0).toFixed(2)} µg/mL — <span className="text-[#4AFA9A]">{top.pk_summary.status}</span>
              </div>
            )}
          </div>

          {/* Avoid */}
          {avoid && avoid.drug_id !== top.drug_id && (
            <div className="relative overflow-hidden rounded-xl bg-[#EF4444]/[0.02] border border-[#EF4444]/20 p-6 shadow-[0_0_30px_-5px_rgba(239,68,68,0.1)] group">
              <div className="absolute inset-0 bg-gradient-to-br from-[#EF4444]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              
              <div className="flex items-center gap-2 mb-3">
                <XCircle size={16} className="text-[#EF4444]/80" />
                <span className="text-xs font-mono tracking-wider text-white/50 uppercase">Lowest Ranked</span>
              </div>
              
              <span className="text-3xl font-sans font-bold tracking-tight text-white/80 mb-2 block">{avoid.drug_name}</span>
              
              <div className="mt-4 flex flex-col gap-2">
                <div className="flex items-center justify-between bg-black/40 rounded p-2 border border-white/5">
                  <span className="text-[10px] font-mono text-white/40 uppercase">Composite Score</span>
                  <span className="text-sm font-mono font-bold text-[#EF4444]">{(avoid.composite_score ?? 0).toFixed(1)} / 100</span>
                </div>
                <div className="flex items-center justify-between bg-black/40 rounded p-2 border border-white/5">
                  <span className="text-[10px] font-mono text-white/40 uppercase">Action</span>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#EF4444]/10 text-[#EF4444] border border-[#EF4444]/20">{avoid.recommendation}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* All rankings summary */}
        <div className="flex items-center gap-2 flex-wrap mb-4 bg-black/20 p-3 rounded-lg border border-white/[0.02]">
          <span className="text-[9px] font-mono text-white/30 uppercase mr-2">Full Roster:</span>
          {rankings.map((r, i) => (
            <div key={r.drug_id} className="flex items-center gap-1.5 bg-white/[0.03] border border-white/[0.05] rounded px-2 py-1 shadow-sm">
              <span className="text-[10px] font-mono text-white/30">#{i + 1}</span>
              <span className="text-[10px] font-sans font-medium text-white/70">{r.drug_name}</span>
              <span className="text-[10px] font-mono font-bold" style={{
                color: (r.composite_score ?? 0) >= 90 ? "#4AFA9A" : (r.composite_score ?? 0) >= 80 ? "#FACC15" : "#EF4444"
              }}>{(r.composite_score ?? 0).toFixed(1)}</span>
            </div>
          ))}
        </div>

        {disclaimer && (
          <div className="text-[10px] text-[#00D4FF]/60 font-mono leading-relaxed border-t border-[#00D4FF]/10 pt-4 bg-[#00D4FF]/[0.02] -mx-5 px-5 -mb-5 pb-5">
            <span className="font-bold text-[#00D4FF]">SYSTEM DISCLAIMER:</span> {disclaimer}
          </div>
        )}
      </div>
    </motion.div>
  );
}
