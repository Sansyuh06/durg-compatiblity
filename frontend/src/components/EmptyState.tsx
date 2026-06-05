"use client";
export default function EmptyState({ label, icon }: { label: string; icon?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      {icon && <span className="text-3xl mb-3 opacity-30">{icon}</span>}
      <span className="font-mono text-xs tracking-wider text-white/25">{label}</span>
    </div>
  );
}
