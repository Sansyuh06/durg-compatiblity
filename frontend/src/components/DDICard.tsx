"use client";
import { motion } from "framer-motion";
import type { DDIInteraction } from "@/types";
import { severityColor } from "@/lib/utils";

export default function DDICard({ interaction, index }: { interaction: DDIInteraction; index: number }) {
  const color = severityColor(interaction.severity);
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.35 }}
      className="panel p-4 border-l-2"
      style={{ borderLeftColor: color }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-mono font-semibold" style={{ color }}>
          {interaction.severity}
        </span>
        <span className="text-xs text-white/60">
          {interaction.drug_a} ↔ {interaction.drug_b}
        </span>
        <span className="ml-auto text-[10px] font-mono text-white/25">−{interaction.penalty} pts</span>
      </div>
      <p className="text-xs text-white/50 mb-1">{interaction.mechanism}</p>
      <p className="text-xs text-white/35">{interaction.effect}</p>
      <span className="text-[9px] font-mono text-white/20 mt-2 block">{interaction.source}</span>
    </motion.div>
  );
}
