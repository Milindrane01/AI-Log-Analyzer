// Small shared UI pieces — one file on purpose (component sprawl is a smell at this size).

import type { Severity } from "../api/types";

const SEVERITY_STYLES: Record<Severity, string> = {
  critical: "bg-red-500/15 text-red-400 ring-red-500/30",
  high: "bg-orange-500/15 text-orange-400 ring-orange-500/30",
  medium: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
  low: "bg-slate-500/15 text-slate-300 ring-slate-500/30",
};

export function SeverityBadge({ severity }: { severity: Severity | string }) {
  const style = SEVERITY_STYLES[severity as Severity] ?? SEVERITY_STYLES.low;
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${style}`}>
      {severity}
    </span>
  );
}

export function StatusPill({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "text-emerald-400",
    running: "text-sky-400 animate-pulse",
    pending: "text-slate-400 animate-pulse",
    failed: "text-red-400",
  };
  return <span className={`text-sm font-medium ${styles[status] ?? ""}`}>{status}</span>;
}

export function ErrorNote({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-300">
      {message}
    </div>
  );
}

export function Confidence({ value }: { value: number }) {
  return (
    <span className="text-sm text-slate-400">
      Confidence <span className="font-semibold text-slate-100">{Math.round(value * 100)}%</span>
    </span>
  );
}
