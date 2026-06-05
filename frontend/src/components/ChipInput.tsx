"use client";
import { useState, KeyboardEvent } from "react";
import { X } from "lucide-react";

interface Chip { name: string; dose?: string }
interface Props {
  chips: Chip[];
  onChange: (chips: Chip[]) => void;
  placeholder?: string;
}

export default function ChipInput({ chips, onChange, placeholder = "Add medication..." }: Props) {
  const [input, setInput] = useState("");

  const add = () => {
    const v = input.trim();
    if (!v) return;
    // Parse "Drug 500mg" format
    const match = v.match(/^(.+?)\s+(\d+\s*mg)$/i);
    const chip: Chip = match ? { name: match[1], dose: match[2] } : { name: v };
    onChange([...chips, chip]);
    setInput("");
  };

  const handleKey = (e: KeyboardEvent) => {
    if (e.key === "Enter") { e.preventDefault(); add(); }
  };

  return (
    <div className="border border-white/[0.07] rounded-md bg-white/[0.02] p-2 flex flex-wrap gap-1.5 min-h-[40px]">
      {chips.map((c, i) => (
        <span key={i} className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono bg-white/[0.06] border border-white/[0.1] rounded text-white/70">
          {c.name}{c.dose && <span className="text-[#4AFA9A]/60">{c.dose}</span>}
          <button onClick={() => onChange(chips.filter((_, j) => j !== i))} className="text-white/30 hover:text-white/60">
            <X size={12} />
          </button>
        </span>
      ))}
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKey}
        onBlur={add}
        placeholder={chips.length === 0 ? placeholder : ""}
        className="flex-1 min-w-[100px] bg-transparent text-xs text-white/70 outline-none placeholder:text-white/20"
      />
    </div>
  );
}
