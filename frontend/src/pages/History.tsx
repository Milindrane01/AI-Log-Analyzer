import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import type { AnalysisListItem } from "../api/types";
import { StatusPill } from "../components/ui";

export default function History() {
  const [items, setItems] = useState<AnalysisListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  useEffect(() => {
    api.history(limit, offset).then((page) => {
      setItems(page.items);
      setTotal(page.total);
    });
  }, [offset]);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Analysis history</h1>
      <div className="overflow-hidden rounded-xl border border-slate-800">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-2">File</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Errors</th>
              <th className="px-4 py-2">Groups</th>
              <th className="px-4 py-2">When</th>
            </tr>
          </thead>
          <tbody>
            {items.map((a) => (
              <tr key={a.id} className="border-t border-slate-800 hover:bg-slate-900/50">
                <td className="px-4 py-2">
                  <Link to={`/analyses/${a.id}`} className="text-sky-400 hover:underline">
                    {a.filename}
                  </Link>
                </td>
                <td className="px-4 py-2">
                  <StatusPill status={a.status} />
                </td>
                <td className="px-4 py-2">{a.error_lines.toLocaleString()}</td>
                <td className="px-4 py-2">{a.group_count}</td>
                <td className="px-4 py-2 text-slate-400">
                  {new Date(a.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                  Nothing yet — <Link to="/" className="text-sky-400">analyze your first log</Link>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {total > limit && (
        <div className="flex items-center gap-3 text-sm">
          <button
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - limit))}
            className="rounded border border-slate-700 px-3 py-1 disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-slate-500">
            {offset + 1}–{Math.min(offset + limit, total)} of {total}
          </span>
          <button
            disabled={offset + limit >= total}
            onClick={() => setOffset(offset + limit)}
            className="rounded border border-slate-700 px-3 py-1 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
