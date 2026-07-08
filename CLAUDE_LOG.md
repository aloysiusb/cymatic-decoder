# CLAUDE_LOG.md

Running, dated, append-only log of what any Claude session (any model) did
in this project and why. **Read this before doing anything else** — see
the instruction at the top of CLAUDE.md. Add a new dated entry after
making non-trivial changes, don't edit past entries except to fix a
factual error.

This log started 2026-07-07 when the project had no git history yet (see
the first entry below). Git was initialized later that same day — see
the "git init + Render deploy" entries for when that changed.

## 2026-07-07 — CLAUDE.md + CLAUDE_LOG.md created
Added as part of a portfolio-wide convention (see The-Lemmon-Dociere's
CLAUDE_LOG.md for the incident that prompted it — two Claude sessions
worked that repo in parallel with no shared record and diverged on
GitHub). CLAUDE.md's content was reconstructed from prior-session memory
notes (the 3D-visualization handoff status, architecture, known gotchas),
not from reading this session's own work — verify against the actual code
if anything here seems stale, especially the "current state" section.

## 2026-07-07 — git init + Render deploy prep
Owner asked to deploy this to Render. Added `.gitignore` (already existed
from earlier the same day, just added `.claude/` to it) and `render.yaml`
(Python runtime, `pip install -r requirements.txt`, `uvicorn
app.main:app --host 0.0.0.0 --port $PORT` — matches the pattern in
evergreen-driver-app's render.yaml, adapted from Node to Python).
Confirmed no code hardcodes port 8420 (that's only in the local
`.claude/launch.json` dev config, which is gitignored). Initializing git,
creating a GitHub repo under aloysiusb, and pushing next — actual Render
web service creation (connecting the repo, setting build/start commands)
has to happen in the Render dashboard, not something doable from here.

## 2026-07-07 — deployed
Pushed to https://github.com/aloysiusb/cymatic-decoder (public). Owner
created the Render web service herself and it's live at
https://cymatic-decoder.onrender.com/ — verified working: `/`,
`/classical-pieces`, and `/modes?frequency=136` all return correct
200 responses in production. Render free-tier services spin down after
inactivity, so the first request after a while will be slow (cold
start) — not a bug if that happens.
