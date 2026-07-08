# CLAUDE.md — project handoff notes

**Before doing anything else in this repo, read `CLAUDE_LOG.md`.** It's a
running log every Claude session (any model) appends to — check it first
for prior context, and add a new dated entry after making changes. Don't
rely on conversation memory alone; it doesn't carry across sessions or
models, but this file does.

Note: this project is **not currently a git repo** (no `.git`, no
remote), so there's no `origin/main` to diff against and no way for two
sessions to diverge on GitHub the way it happened on a sibling project —
but the same risk exists locally if this is ever worked from two machines
or two parallel sessions. If you initialize git here, keep this file's
instruction intact.

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
- `app/symmetry.py` — polar-FFT symmetry detection on the uploaded image
- `app/frequency_mapping.py` — Chladni mode ↔ frequency mapping
- `app/cross_domain.py` — frequency → musical note / brainwave band /
  Schumann resonance / color / physical-scale correspondences
- `app/audio.py` — organ/chorus/classical synthesis, with editable
  brightness/reverb/warmth/tempo
- `app/music_library.py` — public-domain melody motifs
- `app/static/index.html` — frontend, including a Three.js 3D view

## Running it
`venv/bin/uvicorn app.main:app --reload --port 8420 --app-dir /Users/virginiapayson/Documents/cymatic-decoder`

## Gotchas
- No opencv dependency — Python 3.9 on this machine has no prebuilt wheel
  for it and source-builds forever. Symmetry detection uses NumPy/Pillow
  polar remap instead. Don't reintroduce opencv without checking this is
  still true.
- Python 3.9 here doesn't support `X | None` type-hint syntax — needs
  `from __future__ import annotations` at the top of any file using it.

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
