import { type FormEvent, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { ApiRequestError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ErrorNote } from "../components/ui";

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: { pathname: string } } };
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await (mode === "login" ? login(email, password) : register(email, password));
      navigate(location.state?.from?.pathname ?? "/", { replace: true });
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto mt-24 w-full max-w-sm">
      <h1 className="mb-1 text-center text-2xl font-semibold">AI Log Analyzer</h1>
      <p className="mb-8 text-center text-sm text-slate-400">
        Root cause in minutes, not hours
      </p>
      <div className="mb-6 grid grid-cols-2 rounded-lg bg-slate-900 p-1 text-sm">
        {(["login", "register"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`rounded-md py-1.5 capitalize ${
              mode === m ? "bg-slate-700 text-white" : "text-slate-400"
            }`}
          >
            {m === "login" ? "Sign in" : "Create account"}
          </button>
        ))}
      </div>
      <form onSubmit={submit} className="space-y-4">
        <input
          type="email"
          required
          placeholder="you@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-sky-500"
        />
        <input
          type="password"
          required
          minLength={10}
          placeholder={mode === "register" ? "Password (10+ characters)" : "Password"}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-sky-500"
        />
        <ErrorNote message={error} />
        <button
          disabled={busy}
          className="w-full rounded-lg bg-sky-600 py-2 text-sm font-medium hover:bg-sky-500 disabled:opacity-50"
        >
          {busy ? "Working…" : mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>
    </div>
  );
}
