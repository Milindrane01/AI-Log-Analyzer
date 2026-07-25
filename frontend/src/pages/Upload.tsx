import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, ApiRequestError } from "../api/client";
import { ErrorNote } from "../components/ui";

export default function Upload() {
  const navigate = useNavigate();
  const [pasted, setPasted] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  async function run(action: () => Promise<{ analysis_id: string }>) {
    setError(null);
    setBusy(true);
    try {
      const accepted = await action();
      navigate(`/analyses/${accepted.analysis_id}`);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Upload failed");
      setBusy(false);
    }
  }

  function onFile(file: File | undefined) {
    if (file) void run(() => api.uploadLog(file));
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Analyze logs</h1>
        <p className="text-sm text-slate-400">
          Upload a file (up to 50MB) or paste log lines — format is detected automatically.
        </p>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          onFile(e.dataTransfer.files[0]);
        }}
        onClick={() => fileInput.current?.click()}
        className={`cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
          dragging ? "border-sky-500 bg-sky-500/10" : "border-slate-700 hover:border-slate-500"
        }`}
      >
        <p className="text-sm text-slate-300">
          Drop a log file here, or <span className="text-sky-400">browse</span>
        </p>
        <p className="mt-1 text-xs text-slate-500">.log .txt .json — 50MB max</p>
        <input
          ref={fileInput}
          type="file"
          hidden
          accept=".log,.txt,.json,.jsonl,.out"
          onChange={(e) => onFile(e.target.files?.[0])}
        />
      </div>

      <div className="flex items-center gap-3 text-xs text-slate-500">
        <div className="h-px flex-1 bg-slate-800" /> or paste
        <div className="h-px flex-1 bg-slate-800" />
      </div>

      <textarea
        value={pasted}
        onChange={(e) => setPasted(e.target.value)}
        rows={10}
        placeholder={`2026-07-15 10:12:14 ERROR Database connection timeout\nConnection refused to PostgreSQL`}
        className="w-full rounded-xl border border-slate-700 bg-slate-900 p-4 font-mono text-xs outline-none focus:border-sky-500"
      />
      <ErrorNote message={error} />
      <button
        disabled={busy || !pasted.trim()}
        onClick={() => void run(() => api.pasteLog(pasted))}
        className="rounded-lg bg-sky-600 px-5 py-2 text-sm font-medium hover:bg-sky-500 disabled:opacity-40"
      >
        {busy ? "Analyzing…" : "Analyze pasted logs"}
      </button>
    </div>
  );
}
