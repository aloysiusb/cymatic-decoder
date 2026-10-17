# CLAUDE.md — project handoff notes

**Before doing anything else in this repo, read `CLAUDE_LOG.md`.** It's a
running log every Claude session (any model) appends to — check it first
for prior context, and add a new dated entry after making changes. Don't
rely on conversation memory alone; it doesn't carry across sessions or
models, but this file does.

## Current state — READ THIS, then update it before you end the session

*Last updated 2026-10-17. VERIFIED means a session checked it; Owner TOLD means
she said so. UNVERIFIED is a claim, not a fact.*

| Area | State | Basis |
|---|---|---|
| Git | **This is a git repo.** Remote `github.com/aloysiusb/cymatic-decoder` (public). An earlier version of this file said it was not a git repo; that was true once and has been wrong for a while | VERIFIED |
| Hosting | Render web service `cymatic-decoder`, Python, auto-deploys from `main`. Service record last updated 2026-10-13. Not suspended | VERIFIED 2026-10-17 |
| Live links | `vpayson.com` no longer links here. Since 2026-10-13 it serves its own static, server-free copy at `vpayson.com/resonance/` (vpayson PR #10). This app still runs and returned 200 on 2026-10-17. It still does two things the static copy cannot: the decoder page and the WAV audio. **Stopping this Render service is the owner's call, and would lose both** | VERIFIED 2026-10-17 |
| Water view | Built and merged (PR #2). Owner's direction, not ours: iterate on it from her feedback only | VERIFIED |
| 3D view | Still hers to design. Do not start 3D visual work unless she asks again | Owner TOLD |

The rest of this file's rules (the audio is solid; do not reintroduce opencv;
Python 3.9 needs `from __future__ import annotations`) still stand.

### Session rule — no information may be lost between sessions

**Cross-project, cross-account handoff:** first read the Google Doc **"CLAUDE HANDOFF — READ FIRST"** (Google Drive, shared with the work account) — `https://docs.google.com/document/d/17i7T_GmTaWdkZUPy7PgATpdfms3mWDw3Lj8DTB4sejU/edit`. Before your final reply, add a dated entry to its *Session log*. No secrets in it. If this session has no Google Drive connector, say so to the owner instead of skipping silently.

1. Read this block and `CLAUDE_LOG.md` first.
2. When the owner says something changed outside a session, write it here
   **immediately**, marked "Owner TOLD".
3. Before ending, update the date and every line you touched, and say how you
   know it. Never call something fine because one check passed without saying
   what that check could not have shown.
4. Sessions here are told to work on a `claude/<task>` branch and open a draft
   PR. The owner works from an iPad and dictation mangles technical words, so
   give one step at a time and keep answers short.

## What this is
Cymatic Decoder — a Python/FastAPI tool for reverse-engineering cymatic
patterns: upload an image of a Chladni-plate pattern and get back the
frequency/mode that would produce it, or go the other direction (pick a
frequency, hear/see the resulting pattern). Spun out of a "Resonance
Engine" conversation about cymatics/sacred geometry. Not part of the
`evergreen-driver-app` repo — that repo's `.claude/launch.json` just hosts
the dev-server launch config since Claude Code sessions run with that as
the working directory.

## Architecture
- `app/main.py` — FastAPI endpoints: `/analyze` (image upload →
  frequency/mode), `/modes` (reverse frequency → pattern lookup),
  `/audio/*` (WAV synthesis)
- `app/symmetry.py` — polar-FFT symmetry detection on the uploaded image.
  Finds the plate's actual centre and corrects for tilt rather than
  assuming the pattern is centred in frame; `tests/test_symmetry.py`
  covers it
- `app/frequency_mapping.py` — Chladni mode ↔ frequency mapping
- `app/cross_domain.py` — frequency → musical note / brainwave band /
  Schumann resonance / color / physical-scale correspondences
- `app/audio.py` — organ/chorus/classical synthesis, with editable
  brightness/reverb/warmth/tempo
- `app/music_library.py` — public-domain melody motifs
- `/resonance` → `app/static/resonance-engine.html` (Resonance Engine page; also at `/static/resonance-engine.html`), linked from the home page
- `app/static/index.html` — frontend, including a Three.js 3D view

## Running it
`venv/bin/uvicorn app.main:app --reload --port 8420 --app-dir /Users/virginiapayson/Documents/cymatic-decoder`

## Gotchas
- No opencv dependency. Originally because Python 3.9 here had no prebuilt
  wheel and source-builds forever. **Reconsidered 2026-10-04 and still
  rejected** — centre detection and tilt correction, the two things opencv
  was wanted for, are now done in NumPy (`find_centre`, `find_tilt`), so
  the dependency would buy a faster `warpPolar` and nothing else. It would
  also cost: opencv-python needs `libGL` on a headless box, so Render would
  need `opencv-python-headless`, and the wheel is tens of MB. If you ever
  do add it, that headless detail is the trap.
- Python: the owner is upgrading this Mac off 3.9. Until that lands, 3.9
  can't parse `X | None` type hints, so keep `from __future__ import
  annotations` at the top of any file using them — it's good practice
  regardless and costs nothing.

## Update 2026-09-24 — owner reopened visuals: water cymatics
Owner shared CymaScope water-cymatics photos (cadboy_hk, magicaqua.de
"planet tones") and chose a **water** look, with each tone tinted by its
own color octave. Built as a WebGL "Water" view on
`app/static/resonance-engine.html` (Sand/dots view kept as a toggle).
Iterate on *that* direction from her feedback; the notes below about
not proposing new aesthetics still apply to anything beyond it.

## Current state (as of 2026-07-06)
**3D visualization design was explicitly handed off to the owner — do NOT
initiate further 3D visual design work on this project unless she asks
again.** She said: "forget the flower of life build... I need to figure
the 3D render out myself."

Current 3D view code (left in place, functional, not being iterated on):
opens with a Flower-of-Life circle-packing construction (thin colored
THREE.Line strokes, compass-style sweep, paced to ~14s total regardless
of circle count), then settles into an ongoing spirograph/epicycloid
trace using the decoded angular-folds:radial-rings ratio (reduced to
lowest terms) as a fading comet trail.

Audio (organ/chorus/classical playback with brightness/reverb/warmth/
tempo sliders) is considered solid and separate from the 3D-visual
handoff — fine to keep working on that.

**If she comes back with her own 3D design** (built via Spline/Cables.gl/
hand-coded reference, or a screenshot/link), implement *that* rather than
proposing new aesthetic directions. If asked to touch
`app/static/index.html`'s `buildModeViewer` for non-visual reasons (bug
fix, data wiring), don't take it as an invitation to redesign it.

**Prior iterations she explicitly rejected — don't reintroduce:**
- A rigid ring+spoke grid ("looks like a colander")
- A hex-tiling math bug (since fixed to true triangular circle-packing)
- Monochrome green-on-black ("1985 WarGames terminal aesthetic")
