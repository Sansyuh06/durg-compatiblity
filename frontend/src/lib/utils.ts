// ── Utility Functions ──────────────────────────────────────────────────

export function scoreColor(score: number): string {
  if (score >= 80) return "#4AFA9A";
  if (score >= 60) return "#FACC15";
  if (score >= 40) return "#FB923C";
  return "#EF4444";
}

export function severityColor(severity: string): string {
  switch (severity) {
    case "CRITICAL": case "MAJOR": return "#EF4444";
    case "WARNING": case "MODERATE": return "#FB923C";
    case "INFO": case "MINOR": return "#4AFA9A";
    default: return "#6B7280";
  }
}

export function recommendationColor(rec: string): string {
  switch (rec) {
    case "RECOMMENDED": return "#4AFA9A";
    case "CONDITIONAL": return "#FACC15";
    case "NOT_RECOMMENDED": return "#EF4444";
    default: return "#6B7280";
  }
}

export function formatScore(score: number): string {
  return (score ?? 0).toFixed(1);
}

export function actionColor(action: string): string {
  switch (action) {
    case "search_faers": return "#60A5FA";
    case "fetch_label": return "#9CA3AF";
    case "analyze_signal": return "#A78BFA";
    case "lookup_mechanism": return "#F472B6";
    case "check_literature": return "#FBBF24";
    case "submit": return "#4AFA9A";
    default: return "#6B7280";
  }
}

export function cn(...classes: (string | false | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
