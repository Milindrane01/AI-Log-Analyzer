# User Guide

## What it does

Paste or upload application/infrastructure logs and get, in seconds: grouped errors, AI root-cause
analysis, plain-language explanations, safe diagnostic commands, similar past incidents, a chat
interface over your log, a postmortem report, and a multi-agent investigation of complex incidents.

## Walkthrough

1. **Sign in.** Register with an email and a 10+ character password.
2. **Analyze.** On the home page, drop a `.log`/`.txt`/`.json` file (up to 50MB) or paste log lines.
   Format is detected automatically.
3. **Read the dashboard.** The left rail lists error groups by frequency and severity. Click one to
   see its root cause, a beginner-friendly explanation, likely reasons, a suggested fix, read-only
   diagnostic commands, and a confidence score.
4. **Chat with the log.** Click "Chat with this log" and ask questions like *"what happened between
   10:12 and 10:15?"* — answers cite the exact line ranges they're based on, and say "I don't see
   that in this log" rather than guessing.
5. **See the timeline** and click **Investigate** for a multi-agent causal analysis that identifies
   the first failure and whether later errors are a cascade.
6. **Generate an incident report** — a postmortem-ready markdown document you can download.
7. **Revisit history** any time from the History tab; similar incidents link across analyses.

## Notes

- **AI features need an OpenAI API key** configured by your administrator. Without one, parsing,
  grouping, timelines, investigations, and reports still work; AI insights and chat are disabled.
- Suggested commands are **read-only diagnostics only** — the tool never suggests destructive or
  state-changing commands, and never runs anything for you.
- Your logs and analyses are private to your account.
