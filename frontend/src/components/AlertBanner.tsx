"use client";
import { severityColor } from "@/lib/utils";
import type { ClinicalAlert } from "@/types";

export default function AlertBanner({ alert }: { alert: ClinicalAlert }) {
  const color = severityColor(alert.type);
  return (
    <div className="flex items-start gap-3 px-4 py-3 rounded border-l-2" style={{ borderColor: color, background: `${color}08` }}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-xs font-semibold" style={{ color }}>{alert.title}</span>
        </div>
        <p className="text-xs text-white/50 leading-relaxed">{alert.message}</p>
      </div>
      <span className="text-[9px] font-mono text-white/25 whitespace-nowrap mt-0.5">{alert.source}</span>
    </div>
  );
}
