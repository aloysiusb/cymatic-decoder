"""Map a detected (angular folds, radial rings) symmetry back to candidate
driving frequencies, using the same forward Chladni-mode model as the
Resonance Engine prototype (12-tone log steps for angular folds, octave
steps for radial rings). Because that forward mapping repeats every ~10
semitone-steps and every octave, a given (m, r) pair matches a whole family
of frequencies an octave apart -- we return one representative per family
across the audible/infrasound range, plus how each compares to the
Giza King's Chamber's measured ~16-30 Hz resonance band.
"""
import numpy as np

GIZA_KINGS_CHAMBER_HZ = (16.0, 30.0)


def forward_modes(f: float) -> tuple[int, int]:
    m = 2 + (round(12 * np.log2(max(f, 1) / 16)) % 10 + 10) % 10
    r = max(2, min(6, int(np.floor(np.log2(max(f, 2) / 2)))))
    return m, r


def giza_relation(f: float) -> dict:
    lo, hi = GIZA_KINGS_CHAMBER_HZ
    if lo <= f <= hi:
        return {"within_kings_chamber_range": True, "deviation_pct": 0.0}
    nearest = lo if abs(f - lo) < abs(f - hi) else hi
    return {
        "within_kings_chamber_range": False,
        "deviation_pct": round((f - nearest) / nearest * 100, 1),
    }


def candidate_frequencies(target_m: int, target_r: int, f_min: float = 0.5, f_max: float = 20000.0) -> list[dict]:
    target_m_norm = 2 + ((target_m - 2) % 10)
    target_r_clamped = max(2, min(6, target_r))

    freqs = np.logspace(np.log10(f_min), np.log10(f_max), 20000)
    modes = np.array([forward_modes(f) for f in freqs])
    matches = (modes[:, 0] == target_m_norm) & (modes[:, 1] == target_r_clamped)

    families = []
    in_run = False
    run_start = 0
    for i, hit in enumerate(matches):
        if hit and not in_run:
            in_run = True
            run_start = i
        elif not hit and in_run:
            in_run = False
            mid = freqs[(run_start + i - 1) // 2]
            families.append(mid)
    if in_run:
        mid = freqs[(run_start + len(matches) - 1) // 2]
        families.append(mid)

    results = []
    for f in families:
        results.append({
            "frequency_hz": round(float(f), 2),
            "giza_kings_chamber": giza_relation(float(f)),
        })
    return results
