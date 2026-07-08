"""Cross-domain meaning of a frequency, ported from the Resonance Engine
prototype's JS: nearest musical pitch, EEG brainwave band, Schumann-resonance
proximity, the visible-light octave it maps to, acoustic wavelength, and
how the human body responds to that range.
"""
import numpy as np

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
SPEED_SOUND = 343.0
SPEED_LIGHT = 299_792_458.0
SCHUMANN_MODES = [7.83, 14.3, 20.8, 27.3, 33.8, 39.0, 45.0]


def nearest_note(f: float) -> dict:
    midi = 69 + 12 * np.log2(f / 440)
    n = round(midi)
    cents = round((midi - n) * 100)
    return {"name": NOTE_NAMES[n % 12], "octave": n // 12 - 1, "cents": int(cents)}


def brain_band(f: float) -> dict:
    if f < 4:
        return {"band": "Delta", "desc": "deep sleep, unconscious repair"}
    if f < 8:
        return {"band": "Theta", "desc": "meditation, dream states, deep memory"}
    if f < 12:
        return {"band": "Alpha", "desc": "relaxed awareness, eyes-closed calm"}
    if f < 30:
        return {"band": "Beta", "desc": "alert focus, active waking thought"}
    if f < 100:
        return {"band": "Gamma", "desc": "high-level binding, peak cognition"}
    return {"band": "Above EEG", "desc": "outside measured brainwave bands"}


def schumann_proximity(f: float) -> dict:
    best = min(SCHUMANN_MODES, key=lambda s: abs(f - s))
    harmonic = SCHUMANN_MODES.index(best) + 1
    dev = (f - best) / best * 100
    return {"harmonic": harmonic, "mode_hz": best, "deviation_pct": round(dev, 1)}


def wavelength_to_hex(nm: float) -> str:
    r = g = b = 0.0
    if nm < 380:
        r, b = 0.5, 1.0
    elif nm < 440:
        r, b = -(nm - 440) / 60, 1.0
    elif nm < 490:
        g, b = (nm - 440) / 50, 1.0
    elif nm < 510:
        g, b = 1.0, -(nm - 510) / 20
    elif nm < 580:
        r, g = (nm - 510) / 70, 1.0
    elif nm < 645:
        r, g = 1.0, -(nm - 645) / 65
    else:
        r = 1.0

    factor = 1.0
    if nm > 700:
        factor = 0.3 + 0.7 * (780 - nm) / 80
    if nm < 420:
        factor = 0.3 + 0.7 * (nm - 380) / 40

    def clamp_channel(v: float) -> str:
        v = max(0.0, min(1.0, v * factor))
        return format(round(v ** 0.8 * 255), "02x")

    return "#" + clamp_channel(r) + clamp_channel(g) + clamp_channel(b)


def color_octave(f: float) -> dict:
    x, k = f, 0
    while x < 4.0e14:
        x *= 2
        k += 1
    thz = x / 1e12
    nm = (SPEED_LIGHT / x) * 1e9
    return {
        "octaves_up": k,
        "terahertz": round(thz, 1),
        "wavelength_nm": round(nm, 1),
        "visible": thz <= 790,
        "hex": wavelength_to_hex(nm),
    }


def physical_scale(f: float) -> dict:
    wavelength_m = SPEED_SOUND / f
    return {
        "wavelength_m": round(wavelength_m, 2),
        "half_wave_cavity_m": round(wavelength_m / 2, 2),
    }


def body_response(f: float) -> dict:
    if f < 0.5:
        return {"response": "Below perception", "desc": "slower than physiological rhythms"}
    if f < 8:
        return {"response": "Whole-body / organ range", "desc": "chest, abdomen and organs resonate roughly 4-8 Hz"}
    if f < 16:
        return {"response": "Felt vibration", "desc": "below the hearing threshold; perceived as pressure and movement"}
    if f < 22:
        return {"response": "Eye resonance zone", "desc": "the eyeball resonates near 18 Hz (Tandy's experiments)"}
    if f < 100:
        return {"response": "Deep bass / chest", "desc": "audible low end; strong SPL is felt in the chest cavity"}
    if f < 4000:
        return {"response": "Core hearing range", "desc": "where human hearing is most sensitive"}
    return {"response": "Upper hearing", "desc": "high-frequency air conduction"}


def octave_lift(f: float) -> dict:
    """Double/halve into the 110-880 Hz comfortable hearing range, preserving pitch class."""
    x, k = f, 0
    while x < 110:
        x *= 2
        k += 1
    while x > 880:
        x /= 2
        k -= 1
    return {"frequency_hz": round(x, 2), "octaves_shifted": k}


def profile(f: float) -> dict:
    return {
        "frequency_hz": round(f, 2),
        "musical_note": nearest_note(f),
        "brainwave_band": brain_band(f),
        "schumann": schumann_proximity(f),
        "color_octave": color_octave(f),
        "physical_scale": physical_scale(f),
        "body_response": body_response(f),
    }
