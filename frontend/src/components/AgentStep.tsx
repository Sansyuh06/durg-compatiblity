"use client";
import { motion } from "framer-motion";
import type { AgentStep as AgentStepType } from "@/types";
import { actionColor } from "@/lib/utils";

export default function AgentStep({ step, index }: { step: AgentStepType; index: number }) {
  const color = actionColor(step.action_type);
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.3 }}
      className="panel p-3 flex gap-3 items-start"
    >
      {/* Step number */}
      <span className="w-6 h-6 flex items-center justify-center rounded text-[10px] font-mono text-white/30 bg-white/[0.04] flex-shrink-0 mt-0.5">
        {step.step}
      </span>

      <div className="flex-1 min-w-0">
        {/* Action pill */}
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono px-2 py-0.5 rounded" style={{ color, background: `${color}15` }}>
            {step.action_type}
          </span>
          <span className="text-[10px] font-mono" style={{ color: step.reward >= 0.5 ? "#4AFA9A" : step.reward > 0.01 ? "#FACC15" : "#6B7280" }}>
            +{(step.reward ?? 0).toFixed(4)}
          </span>
          {step.done && <span className="tag tag-green text-[8px]">DONE</span>}
        </div>

        {/* Reasoning */}
        <p className="text-xs text-white/40 leading-relaxed">{step.reasoning}</p>

        {/* Parameters (for submit) */}
        {step.action_type === "submit" && Object.keys(step.parameters).length > 0 && (
          <div className="mt-1.5 font-mono text-[10px] text-white/20 bg-white/[0.02] rounded p-2">
            {Object.entries(step.parameters).map(([k, v]) => (
              <div key={k}><span className="text-white/30">{k}:</span> {String(v)}</div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
