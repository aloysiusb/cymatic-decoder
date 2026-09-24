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

## 2026-09-24 — Resonance Engine handoff checked against the repo
A Claude.ai-chat handoff note said `resonance-engine.html` (with an audio
`ReferenceError` fix: undefined `voice` → `which` in `startVoice`/
`stopVoice`) had been pushed here, that full context lived in
`claude-log/CLAUDE.md`, and asked whether Render service
`srv-d96pqgd8nd3s73bd7khg` deploys from this repo. Checked:
- **Neither file exists on GitHub.** `main` is still at 61c34bd
  (2026-07-11), the only branch; no file anywhere mentions
  `startVoice`/`stopVoice`. The push never landed — the file still has
  to be uploaded from wherever the chat session produced it.
- **Render does deploy from this repo.** https://cymatic-decoder.onrender.com/
  serves `app/static/index.html` byte-identical to `main` (modulo CRLF),
  `/modes?frequency=136` returns 200, origin is uvicorn. The service ID
  itself wasn't verifiable from here (no Render API access).
- The handoff's "next up: 3D via Three.js" conflicts with CLAUDE.md's
  standing instruction that 3D design is the owner's to lead. Not started;
  needs the owner's explicit go-ahead or their own design.

## 2026-09-24 — Resonance Engine added (from claude.ai chat)
The earlier push never landed; owner recovered the file. Added as
`app/static/resonance-engine.html`, served by the existing `/static`
mount — no Python change. Changes vs. the handoff prototype:
- Audio: `voice` → `which` ReferenceError fixed in startVoice/stopVoice.
- Layout: Voice/Volume/Space controls moved out of `.engine-grid` into
  `.engine-opts`.
- Glass harp card always uses the glass timbre, plays the octave-lifted
  pitch, and its Hz/note readout is now filled in; canvas animates for it.
- Tuning switched to A432 (`const A4 = 432`); A4 preset 432 Hz, C0 16.05 Hz.
- iPhone: `navigator.audioSession.type = 'playback'` so the silent switch
  doesn't mute it; octave-lift floor raised 110 → 220 Hz for phone speakers.
  Not yet confirmed audible on her phone.
- New **Decode a pattern** view (header nav, CSS-only `#decode:target`
  switch) that posts an image to the existing `POST /analyze` and loads a
  chosen candidate frequency into the engine. Backend `forward_modes()`
  and engine `cymModes()` share the same formula. Tested locally.

## 2026-09-24 — Water cymatics view on the Resonance Engine
Owner reopened the visual design: sent CymaScope water-cymatics reference
photos and chose "water", with color matching each tone's frequency.
Added to `app/static/resonance-engine.html` only (no Python change):
- **Water / Sand switch** above the pattern; Water is default, choice is
  remembered per browser. Sand = the original φ-spiral dots, unchanged.
  Falls back to Sand automatically if WebGL isn't available.
- **Water view**: one full-screen WebGL fragment shader, no libraries.
  Surface height = Bessel-style radial × cos(mθ) modes + m plane waves,
  driven by the same `cymModes()` folds/rings the engine and `/analyze`
  use. Light = thin glowing iso-lines around wave crests + a caustic fill,
  soft tone-map glow, bright rim — to read like light on moving water.
- **Color** = `colorOctave(freq)` (the tone raised by octaves into visible
  light), normalized to full strength — so every octave of a note shares
  a hue, matching the "Color octave" profile card.
- Animates while a tone plays; on a frequency change the old pattern
  cross-fades into the new one over ~0.9s.
Pre-existing, not touched: at 390px phone width the header (logo + nav
+ Settings) overflows horizontally by ~85px. Flagged to owner.

## 2026-09-24 — Water view: analogous color weave + accent
Owner asked to "interweave analogous colors with an accent for depth".
`tonePalette(freq)` (OKLCH, reuses the page's hexToOklch/oklchToHex):
the tone's own hue, warm neighbour (−30°), cool neighbour (+30°) and a
soft complementary accent (+180°, low chroma). In the shader: hue drifts
warm (centre) → tone → cool (rim); crest / mid / nodal line layers each
take a different neighbour so they interlace; the caustic fill leans cool
so it sits back; the accent appears only in the hottest cores and as a
small spark at the still centre.

## 2026-09-24 — Water view: motion (idle ripple, speed by frequency, volume energy)
Owner asked for the water to move like water. Honest framing given to
her: it's standing-wave math + caustic lighting, not a fluid simulation;
a real GPU wave-equation sim (ripples propagate, reflect off the rim,
tap-to-ripple) was offered as a bigger follow-up, not started.
- `waterTime` now always advances in Water view (rAF), paused via
  IntersectionObserver when the canvas is scrolled off-screen.
- `waterRate(freq)`: log-mapped, 8 Hz slow heave → 2 kHz fast shimmer;
  idle runs at 18% of that rate.
- `uEnergy` scales wave height (so weak drive naturally shows fewer crest
  lines) and brightness: idle 0.62, playing 0.8–1.25 by the Volume
  slider, eased so the surface swells up / settles down.

## 2026-09-24 — Phone header fix (gear icon)
Owner picked the gear-icon option. CSS + markup only, header of
`resonance-engine.html`:
- ≤640px: Settings button shows an inline SVG gear (label hidden, kept as
  aria-label/title); tighter header gap, logo and nav padding.
- ≤460px: "Decode a pattern" → "Decode" (" a pattern" in a `.long` span).
- ≤360px: slightly smaller logo/nav spacing for the smallest phones.
- Nav links `nowrap`; the "Prototype 01" tag now hides below 860px (was
  640px) so the nav doesn't wrap at tablet widths.
Verified no horizontal scroll at 320/360/375/390/430/500/641/700/861/1200px;
Settings drawer and Decode view still open from the header.

## 2026-09-24 — Real plucked harp voice (replaces the humming "glass harp")
Owner: "the harp does not sound like a harp at all — I want pleasing,
soothing sound." Cause: the "Glass harp" card was a continuous
PeriodicWave oscillator with a bright harmonic stack — a buzzy hum, never
plucked. Changes (`resonance-engine.html` only):
- Card renamed **Harp voice**; it now runs `startHarp()`: Karplus–Strong
  plucked strings rendered per pitch into cached AudioBuffers (soft
  twice-low-passed noise excitation = finger not pick; fractional-delay
  tuning; decay t60 1.8–5 s, longer for low strings).
- Plays a slow rolling pattern on just ratios of the root
  [1, 3/2, 2, 5/2, 3, 5/2, 2, 3/2], 0.46 s apart with a breath at the top,
  slight timing/velocity humanising, stereo spread, soft bass (root/2)
  each cycle; through a 3.4 kHz lowpass into the existing reverb.
  Root = octave-lifted pitch, halved if above 440 Hz to stay warm.
  Follows frequency changes live; Stop lets strings ring out.
- Voice-menu "Glass harp" sustained timbre softened to a near-pure rubbed
  rim [1, .10, .035, .012] and renamed "Glass — soft sustained".
Verified: pitches correct (fifth/octave/tenth/twelfth of 272 Hz for
136.1 Hz); offline NumPy render of the same algorithm is click-free.
(A real-time capture in headless Chromium showed click streaks — those
were capture underruns, not present in the offline render.)
