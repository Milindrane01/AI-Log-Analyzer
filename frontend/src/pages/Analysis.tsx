import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Analysis, ErrorGroup, Investigation, Report, SimilarIncident, TimelineEvent } from "../api/types";
import { Confidence, ErrorNote, SeverityBadge, StatusPill } from "../components/ui";

const POLL_MS = 1500;

export default function AnalysisPage() {
  const { id = "" } = useParams();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [groups, setGroups] = useState<ErrorGroup[]>([]);
  const [similar, setSimilar] = useState<SimilarIncident[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [reportBusy, setReportBusy] = useState(false);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [investigating, setInvestigating] = useState(false);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    let cancelled = false;

    async function poll() {
      try {
        const a = await api.analysis(id);
        if (cancelled) return;
        setAnalysis(a);
        if (a.status === "completed") {
          const page = await api.groups(id);
          if (cancelled) return;
          setGroups(page.items);
          setSelected((s) => s ?? page.items[0]?.id ?? null);
          api.similar(id).then((r) => !cancelled && setSimilar(r.items)).catch(() => {});
          api.timeline(id).then((r) => !cancelled && setTimeline(r.events)).catch(() => {});
        } else if (a.status !== "failed") {
          timer = setTimeout(poll, POLL_MS); // 202 pattern: poll until settled
        }
      } catch {
        if (!cancelled) setError("Could not load this analysis.");
      }
    }
    void poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [id]);

  if (error) return <ErrorNote message={error} />;
  if (!analysis) return <p className="text-slate-400">Loading…</p>;

  if (analysis.status === "pending" || analysis.status === "running") {
    return (
      <div className="mt-20 text-center">
        <StatusPill status={analysis.status} />
        <p className="mt-2 text-sm text-slate-400">
          Parsing, grouping and analyzing your logs…
        </p>
      </div>
    );
  }
  if (analysis.status === "failed") {
    return <ErrorNote message={analysis.error_message ?? "Analysis failed"} />;
  }

  const current = groups.find((g) => g.id === selected) ?? groups[0];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm text-slate-400">
        <Link
          to={`/logs/${analysis.log_file_id}/chat`}
          className="rounded-lg border border-sky-600/50 px-3 py-1 text-sky-400 hover:bg-sky-600/10"
        >
          Chat with this log
        </Link>
        <button
          onClick={async () => {
            setReportBusy(true);
            try {
              setReport(await api.generateReport(id));
            } finally {
              setReportBusy(false);
            }
          }}
          className="rounded-lg border border-slate-600 px-3 py-1 text-slate-200 hover:bg-slate-800"
        >
          {reportBusy ? "Generating…" : "Incident report"}
        </button>
        <button
          onClick={async () => {
            setInvestigating(true);
            try {
              setInvestigation(await api.investigate(id));
            } finally {
              setInvestigating(false);
            }
          }}
          className="rounded-lg border border-violet-600/50 px-3 py-1 text-violet-300 hover:bg-violet-600/10"
        >
          {investigating ? "Investigating…" : "Investigate"}
        </button>
        <span>
          <b className="text-slate-200">{analysis.total_lines.toLocaleString()}</b> lines
        </span>
        <span>
          <b className="text-slate-200">{analysis.error_lines.toLocaleString()}</b> errors
        </span>
        <span>
          <b className="text-slate-200">{analysis.group_count}</b> groups
        </span>
        <StatusPill status={analysis.status} />
      </div>

      <div className="grid gap-4 lg:grid-cols-[280px,1fr]">
        <aside className="space-y-2">
          {groups.map((g) => (
            <button
              key={g.id}
              onClick={() => setSelected(g.id)}
              className={`w-full rounded-lg border p-3 text-left transition-colors ${
                current?.id === g.id
                  ? "border-sky-500 bg-sky-500/5"
                  : "border-slate-800 hover:border-slate-600"
              }`}
            >
              <div className="mb-1 flex items-center justify-between">
                <SeverityBadge severity={g.severity} />
                <span className="text-xs text-slate-500">×{g.count}</span>
              </div>
              <p className="truncate text-sm">{g.insight?.payload.error_type ?? g.template}</p>
            </button>
          ))}
          {groups.length === 0 && (
            <p className="text-sm text-slate-500">No warnings or errors found. Clean log!</p>
          )}
        </aside>

        {current && (
          <section className="space-y-4 rounded-xl border border-slate-800 p-5">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-lg font-semibold">
                {current.insight?.payload.error_type ?? current.template}
              </h2>
              <SeverityBadge severity={current.severity} />
              {current.insight && (
                <span className="ml-auto flex items-center gap-3">
                  {current.insight.from_cache && (
                    <span className="text-xs text-slate-500">cached</span>
                  )}
                  <Confidence value={current.insight.payload.confidence} />
                </span>
              )}
            </div>

            {current.insight ? (
              <>
                <Block title="Root cause">{current.insight.payload.root_cause}</Block>
                <Block title="What this means">{current.insight.payload.explanation}</Block>
                <Block title="Possible reasons">
                  <ul className="list-inside list-disc space-y-1">
                    {current.insight.payload.possible_reasons.map((r) => (
                      <li key={r}>{r}</li>
                    ))}
                  </ul>
                </Block>
                <Block title="Suggested fix">{current.insight.payload.suggested_fix}</Block>
                {current.insight.payload.recommended_commands.length > 0 && (
                  <Block title="Recommended commands (read-only diagnostics)">
                    <pre className="overflow-x-auto rounded-lg bg-slate-900 p-3 text-xs leading-6">
                      {current.insight.payload.recommended_commands.join("\n")}
                    </pre>
                  </Block>
                )}
              </>
            ) : (
              <p className="text-sm text-slate-400">
                No AI insight for this group (AI disabled or unavailable). Sample lines below.
              </p>
            )}

            <Block title={`Sample lines (${current.count} total occurrences)`}>
              <pre className="overflow-x-auto rounded-lg bg-slate-900 p-3 text-xs leading-6 text-slate-300">
                {(current.sample_lines ?? []).join("\n")}
              </pre>
            </Block>

            {similar.length > 0 && (
              <Block title="Similar past incidents">
                <ul className="space-y-1 text-sm">
                  {similar.map((s) => (
                    <li key={s.group_id} className="flex items-center gap-2">
                      <SeverityBadge severity={s.severity} />
                      <Link
                        to={`/analyses/${s.analysis_id}`}
                        className="truncate text-sky-400 hover:underline"
                      >
                        {s.template}
                      </Link>
                      <span className="ml-auto text-xs text-slate-500">
                        {Math.round(s.score * 100)}% match
                      </span>
                    </li>
                  ))}
                </ul>
              </Block>
            )}
          </section>
        )}
      </div>

      {timeline.length > 0 && (
        <section className="rounded-xl border border-slate-800 p-5">
          <h2 className="mb-3 text-lg font-semibold">Incident timeline</h2>
          <ol className="relative space-y-3 border-l border-slate-700 pl-5">
            {timeline.map((e) => (
              <li key={e.group_id} className="relative">
                <span
                  className={`absolute -left-[26px] top-1 h-3 w-3 rounded-full ${
                    e.is_first_failure ? "bg-red-500 ring-4 ring-red-500/20" : "bg-slate-600"
                  }`}
                />
                <div className="flex items-center gap-2 text-sm">
                  <SeverityBadge severity={e.severity} />
                  <span>{e.label}</span>
                  <span className="text-xs text-slate-500">×{e.count}</span>
                  {e.is_first_failure && (
                    <span className="rounded bg-red-500/15 px-2 py-0.5 text-xs text-red-400">
                      first failure
                    </span>
                  )}
                  <span className="ml-auto text-xs text-slate-500">
                    {e.first_seen ? new Date(e.first_seen).toLocaleTimeString() : "—"}
                  </span>
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      {investigation && (
        <section className="rounded-xl border border-violet-800/50 p-5">
          <div className="mb-2 flex items-center gap-3">
            <h2 className="text-lg font-semibold">Multi-agent investigation</h2>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs ${
                investigation.verified
                  ? "bg-emerald-500/15 text-emerald-400"
                  : "bg-amber-500/15 text-amber-300"
              }`}
            >
              {investigation.verified ? "verified" : "unverified"} ·{" "}
              {Math.round(investigation.confidence * 100)}%
            </span>
          </div>
          <p className="mb-4 text-sm leading-6 text-slate-200">{investigation.conclusion}</p>
          <ol className="space-y-2">
            {investigation.steps.map((s) => (
              <li key={s.seq} className="rounded-lg bg-slate-900 p-3 text-xs">
                <span className="mr-2 rounded bg-violet-500/15 px-2 py-0.5 text-violet-300">
                  {s.agent}
                </span>
                <code className="text-slate-400">{JSON.stringify(s.content)}</code>
              </li>
            ))}
          </ol>
        </section>
      )}

      {report && (
        <section className="rounded-xl border border-slate-800 p-5">
          <div className="mb-2 flex items-center gap-3">
            <h2 className="text-lg font-semibold">{report.title}</h2>
            <a
              href={api.reportDownloadUrl(report.analysis_id)}
              className="ml-auto text-sm text-sky-400 hover:underline"
            >
              Download .md
            </a>
          </div>
          <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-900 p-4 text-xs leading-6 text-slate-200">
            {report.markdown}
          </pre>
        </section>
      )}
    </div>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">{title}</h3>
      <div className="text-sm leading-6 text-slate-200">{children}</div>
    </div>
  );
}
