"use client";
import { motion } from "framer-motion";
import { scoreColor } from "@/lib/utils";

interface Props {
  label: string;
  value: number;
  max?: number;
  delay?: number;
  showValue?: boolean;
  height?: number;
}

export default function ScoreBar({ label, value, max = 100, delay = 0, showValue = true, height = 6 }: Props) {
  const pct = Math.min(100, (value / max) * 100);
  const color = scoreColor(value);

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono tracking-wider text-white/40 uppercase">{label}</span>
        {showValue && <span className="text-[10px] font-mono" style={{ color }}>{(value ?? 0).toFixed(1)}</span>}
      </div>
      <div className="w-full rounded-full overflow-hidden" style={{ height, background: "rgba(255,255,255,0.05)" }}>
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, delay, ease: [0.23, 1, 0.32, 1] }}
        />
      </div>
    </div>
  );
}
