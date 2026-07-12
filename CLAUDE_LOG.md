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

## 2026-07-11 — Bumped off the free plan
Owner confirmed she's on Render's Pro tier, so the cold-start/spin-down
behavior noted above no longer needs to be tolerated. Added
`plan: starter` to `render.yaml` — no other change needed (no persistent
disk here, this app has no database). Same caveat as the equivalent
evergreen-driver-app change: this only takes effect automatically if the
Render service was created via Blueprint sync; since the owner created
this service manually in the dashboard (per the "deployed" entry above),
she likely needs to change the plan directly in the Render dashboard
(Settings → Instance Type) rather than relying on this file alone —
flagged to her, not something to assume worked without checking.

**Left `render.yaml` as the only file touched this session.** The
working tree had other uncommitted, unlogged changes when this session
started (`app/audio.py`, `app/main.py`, `app/static/index.html` modified,
new `app/settings_store.py`) — matches the exact parallel-session
collision pattern from this repo's history (see git log / prior
sessions). Did not stage, commit, inspect closely, or otherwise touch
any of them.
