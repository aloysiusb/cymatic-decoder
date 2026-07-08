"""A small library of public-domain classical melodies, transposable into
whatever key the decoded frequency's nearest note falls on. Notes are
stored as semitone offsets from the tonic (not a claim about the "true"
key of the original piece) so any motif can be sung in any derived key.
"""

# (semitone offset from tonic, duration in beats)
MOTIFS = {
    "ode_to_joy": {
        "label": "Beethoven — Ode to Joy (opening)",
        "bpm": 120,
        "notes": [
            (4, 1), (4, 1), (5, 1), (7, 1),
            (7, 1), (5, 1), (4, 1), (2, 1),
            (0, 1), (0, 1), (2, 1), (4, 1),
            (4, 1.5), (2, 0.5), (2, 2),
        ],
    },
    "canon_in_d_bass": {
        "label": "Pachelbel — Canon in D (bass line)",
        "bpm": 80,
        "notes": [
            (0, 1), (-5, 1), (-3, 1), (-7, 1),
            (-8, 1), (-12, 1), (-8, 1), (-7, 1),
        ],
    },
    "prelude_c_arpeggio": {
        "label": "Bach — Prelude in C, BWV 846 (arpeggio)",
        "bpm": 100,
        "notes": [
            (0, 0.5), (4, 0.5), (7, 0.5), (12, 0.5),
            (16, 0.5), (7, 0.5), (12, 0.5), (16, 0.5),
        ],
    },
}


def semitone_ratio(semitones: float) -> float:
    return 2 ** (semitones / 12)


def render_notes(piece_key: str, tonic_hz: float, tempo: float = 1.0,
                  humanize: float = 0.5, seed: int = 0) -> list[tuple[float, float, float, float]]:
    """Return [(frequency_hz, start_s, duration_s, velocity), ...] for a
    motif transposed to tonic_hz. `humanize` (0-1) adds small, seeded
    timing/velocity variation so repeated notes don't sound quantized."""
    import numpy as np
    piece = MOTIFS[piece_key]
    tempo = max(0.4, min(2.0, tempo))
    beat_s = 60.0 / piece["bpm"] / tempo
    rng = np.random.default_rng(seed)

    events = []
    t = 0.0
    for semitones, beats in piece["notes"]:
        dur = beats * beat_s
        jitter = rng.uniform(-0.02, 0.02) * humanize * beat_s
        velocity = 1.0 + rng.uniform(-0.12, 0.12) * humanize
        events.append((tonic_hz * semitone_ratio(semitones), max(0.0, t + jitter), dur, velocity))
        t += dur
    return events
