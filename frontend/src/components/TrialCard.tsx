"use client";
import { motion } from "framer-motion";
import type { TrialMatch } from "@/types";
import { MapPin, Mail } from "lucide-react";

export default function TrialCard({ trial, index }: { trial: TrialMatch; index: number }) {
  const pct = trial.match_pct;
  const color = pct >= 50 ? "#4AFA9A" : pct >= 30 ? "#FACC15" : "#FB923C";
  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4 }}
      className="panel panel-accent p-4"
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm text-white/80 font-medium leading-snug">{trial.title}</h4>
          <div className="flex items-center gap-2 mt-1">
            <span className="tag tag-cyan text-[9px]">{trial.phase}</span>
            <span className="tag text-[9px]" style={{ borderColor: trial.status === "RECRUITING" ? "#4AFA9A40" : "#FACC1540", color: trial.status === "RECRUITING" ? "#4AFA9A" : "#FACC15" }}>
              {trial.status}
            </span>
            <span className="text-[10px] font-mono text-white/25">{trial.nct_id}</span>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <span className="text-2xl font-mono font-bold" style={{ color }}>{pct}%</span>
          <span className="block text-[9px] font-mono text-white/25">match</span>
        </div>
      </div>

      <p className="text-xs text-white/35 mb-2">Drug: {trial.drug} · Sponsor: {trial.sponsor}</p>

      {/* Match reasons */}
      <div className="flex flex-wrap gap-1 mb-2">
        {trial.match_reasons.map((r, i) => (
          <span key={i} className={`tag text-[8px] ${r.startsWith("EXCLUDED") ? "tag-red" : "tag-green"}`}>{r}</span>
        ))}
      </div>

      {/* Locations */}
      <div className="flex items-center gap-4 text-[10px] text-white/30">
        <span className="inline-flex items-center gap-1"><MapPin size={10} />{trial.locations[0]}</span>
        <span className="inline-flex items-center gap-1"><Mail size={10} />{trial.contact_email}</span>
      </div>
    </motion.div>
  );
}
