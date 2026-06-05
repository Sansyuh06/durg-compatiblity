"use client";
import { motion } from "framer-motion";

interface FaersData {
  drug_name: string;
  total_reports: number;
  events: { event: string; count: number; pct: number }[];
}

export default function FaersPanel({ data }: { data: FaersData }) {
  const events = (data.events ?? []).slice(0, 8);
  const maxPct = Math.max(...events.map(e => e.pct ?? 0), 1);

  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-mono tracking-wider text-white/40 uppercase">
          FDA FAERS — {data.drug_name}
        </h4>
        <span className="text-[10px] font-mono text-white/20">
          {(data.total_reports ?? 0).toLocaleString()} total reports
        </span>
      </div>

      <div className="space-y-1.5">
        {events.map((ev, i) => (
          <motion.div
            key={ev.event}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-center gap-3"
          >
            <span className="text-[10px] font-mono text-white/40 w-28 truncate flex-shrink-0">{ev.event}</span>
            <div className="flex-1 h-[6px] rounded-full overflow-hidden bg-white/[0.05]">
              <motion.div
                className="h-full rounded-full"
                style={{ background: (ev.pct ?? 0) > 10 ? "#EF4444" : (ev.pct ?? 0) > 5 ? "#FB923C" : "#4AFA9A" }}
                initial={{ width: 0 }}
                animate={{ width: `${((ev.pct ?? 0) / maxPct) * 100}%` }}
                transition={{ duration: 0.5, delay: i * 0.05 }}
              />
            </div>
            <span className="text-[10px] font-mono text-white/30 w-12 text-right">{(ev.pct ?? 0).toFixed(1)}%</span>
            <span className="text-[10px] font-mono text-white/20 w-14 text-right">{(ev.count ?? 0).toLocaleString()}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
