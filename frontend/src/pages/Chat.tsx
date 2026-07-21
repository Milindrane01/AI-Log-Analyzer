import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, chatStream } from "../api/client";
import type { ChatMessage } from "../api/types";

export default function Chat() {
  const { logFileId = "" } = useParams();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.chatHistory(logFileId).then((h) => setMessages(h.items)).catch(() => {});
  }, [logFileId]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  async function send() {
    const question = draft.trim();
    if (!question || streaming !== null) return;
    setDraft("");
    setError(null);
    setMessages((m) => [
      ...m,
      {
        id: `local-${Date.now()}`,
        role: "user",
        content: question,
        citations: null,
        created_at: new Date().toISOString(),
      },
    ]);
    setStreaming("");
    let answer = "";
    await chatStream(logFileId, question, (event) => {
      if (event.type === "token" && event.text) {
        answer += event.text;
        setStreaming(answer);
      } else if (event.type === "done") {
        setMessages((m) => [
          ...m,
          {
            id: event.message ?? `a-${Date.now()}`,
            role: "assistant",
            content: answer,
            citations: event.citations ?? null,
            created_at: new Date().toISOString(),
          },
        ]);
        setStreaming(null);
      } else if (event.type === "error") {
        setError(event.message ?? "Chat failed");
        setStreaming(null);
      }
    });
    // Refusal streams tokens but may not emit done — settle the UI either way.
    setStreaming((s) => {
      if (s !== null && s.length > 0) {
        setMessages((m) => [
          ...m,
          {
            id: `a-${Date.now()}`,
            role: "assistant",
            content: s,
            citations: null,
            created_at: new Date().toISOString(),
          },
        ]);
      }
      return null;
    });
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-3xl flex-col">
      <div className="mb-2 text-sm text-slate-400">
        Chat with this log · answers cite line ranges ·{" "}
        <Link to="/history" className="text-sky-400 hover:underline">
          back to history
        </Link>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto rounded-xl border border-slate-800 p-4">
        {messages.length === 0 && streaming === null && (
          <p className="text-sm text-slate-500">
            Ask things like “what happened between 10:12 and 10:15?” or “which error came first?”
          </p>
        )}
        {messages.map((m) => (
          <Bubble key={m.id} message={m} />
        ))}
        {streaming !== null && (
          <Bubble
            message={{
              id: "streaming",
              role: "assistant",
              content: streaming + "▍",
              citations: null,
              created_at: "",
            }}
          />
        )}
        {error && <p className="text-sm text-red-400">{error}</p>}
        <div ref={bottom} />
      </div>
      <div className="mt-3 flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && void send()}
          placeholder="Ask about this log…"
          className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-sky-500"
        />
        <button
          onClick={() => void send()}
          disabled={streaming !== null || !draft.trim()}
          className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium hover:bg-sky-500 disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </div>
  );
}

function Bubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] whitespace-pre-wrap rounded-xl px-4 py-2 text-sm leading-6 ${
          isUser ? "bg-sky-600/20 text-sky-100" : "bg-slate-800/80 text-slate-100"
        }`}
      >
        {message.content}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-1 text-xs text-slate-400">
            Evidence:{" "}
            {message.citations.map((c) => `lines ${c.start_line}-${c.end_line}`).join(" · ")}
          </div>
        )}
      </div>
    </div>
  );
}
