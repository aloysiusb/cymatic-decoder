"""Synthesize the sound of a derived frequency as a WAV file: a warm organ
pipe voice, spread across a real stereo field, ringing out in a cathedral-
style convolution reverb.

Three editable knobs (0-1) shape the character without touching code:
  - brightness: how much overtone presence the pipe has (soft flute-like
    at 0, a more present principal-pipe voicing at 1).
  - reverb:     wet/dry mix of the cathedral tail.
  - warmth:     depth of the built-in celeste detune + sub-octave layer,
    and the amount of gentle tape-style saturation on the final mix.

A few deliberate choices to avoid a thin, buzzy "80s synth" character:
  - harmonic amplitudes decay exponentially (like a real flue/principal
    pipe), not as a slow 1/n power law -- a slow 1/n falloff with
    phase-aligned harmonics is *literally* a sawtooth wave.
  - each harmonic gets a small random phase offset, avoiding the spiky
    transient of perfectly phase-aligned harmonics.
  - the organ/chorus voices are genuinely panned across left/right before
    reverb, not just summed to mono and reverbed -- real stereo width,
    not a decorrelation trick alone.
  - a gentle tanh soft-clip adds a touch of analog-style warmth instead
    of leaving the mix bit-perfect and clinical.
  - classical playback humanizes note timing/velocity slightly so
    repeated notes don't sound quantized.

Three playback modes:
  - organ:     a single warm sustained organ-pipe tone at the derived
               frequency.
  - chorus:    a harmony chord built from the cymatic pattern -- radial
               ring count picks how many chord tones (a justly-tuned major
               stack), angular fold count picks how many detuned unison
               voices sing each chord tone (the "choir" effect), panned
               across the stereo field.
  - classical: a short public-domain melody (see music_library.py)
               transposed into the derived frequency's key, played as a
               sequence of organ notes with humanized timing.
"""
from __future__ import annotations

import io
import struct
import numpy as np

from . import music_library

SAMPLE_RATE = 44100

_REVERB_IR: dict[int, np.ndarray] = {}

# simple just-intonation major stack, degrees 1 (unison) up through a 9th
CHORD_RATIOS = [1.0, 9 / 8, 5 / 4, 4 / 3, 3 / 2, 5 / 3, 15 / 8, 2.0, 9 / 4]


def harmonic_amplitudes(num_partials: int, radial_rings: int, brightness: float | None = None) -> list[float]:
    """Exponential falloff -- warm and rounded, not the slow 1/n
    (sawtooth-like) power law. `brightness` (0-1) overrides the ring-
    derived default when provided."""
    if brightness is None:
        brightness = max(0.0, min(1.0, (radial_rings - 2) / 6))
    ratio = 0.32 + brightness * (0.6 - 0.32)
    return [ratio ** (n - 1) for n in range(1, num_partials + 1)]


def chord_ratios(radial_rings: int) -> list[float]:
    return CHORD_RATIOS[: max(1, min(radial_rings, len(CHORD_RATIOS)))]


def _choir_detunes_cents(voices: int, spread_cents: float = 6.0) -> list[float]:
    if voices <= 1:
        return [0.0]
    step = (spread_cents * 2) / (voices - 1)
    return [(i - (voices - 1) / 2) * step for i in range(voices)]


def _cents_to_ratio(cents: float) -> float:
    return 2 ** (cents / 1200)


def _pan_gains(pan: float) -> tuple[float, float]:
    """Equal-power pan law. pan in [-1 (hard left), 1 (hard right)]."""
    angle = (pan + 1) * (np.pi / 4)
    return float(np.cos(angle)), float(np.sin(angle))


def _fft_convolve(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    n = len(a) + len(b) - 1
    fa = np.fft.rfft(a, n)
    fb = np.fft.rfft(b, n)
    return np.fft.irfft(fa * fb, n)


def _lowpass_kernel(alpha: float = 0.09, length: int = 2400) -> np.ndarray:
    k = np.arange(length)
    kernel = alpha * (1 - alpha) ** k
    return kernel / kernel.sum()


def _get_impulse_response(seed: int) -> np.ndarray:
    if seed not in _REVERB_IR:
        n = int(SAMPLE_RATE * 3.4)
        rng = np.random.default_rng(seed)
        noise = rng.standard_normal(n)
        env = (1 - np.arange(n) / n) ** 2.6
        raw = noise * env
        smoothed = _fft_convolve(raw, _lowpass_kernel())[:n]
        smoothed /= np.max(np.abs(smoothed)) + 1e-9
        _REVERB_IR[seed] = smoothed
    return _REVERB_IR[seed]


def _organ_pipe(frequency_hz: float, amplitudes: list[float], t: np.ndarray, seed: int = 0) -> np.ndarray:
    """A single organ-pipe voice: additive harmonics with randomized phase
    (avoids the phase-aligned "buzz" of a naive harmonic stack) plus a
    touch of vibrato."""
    rng = np.random.default_rng(seed % (2 ** 31))
    vibrato = 1 + 0.0025 * np.sin(2 * np.pi * 5.3 * t + rng.uniform(0, 2 * np.pi))
    wave = np.zeros_like(t)
    for n, amp in enumerate(amplitudes, start=1):
        phase = rng.uniform(0, 2 * np.pi)
        wave += amp * np.sin(2 * np.pi * frequency_hz * n * vibrato * t + phase)
    return wave


def _warm_organ_stereo(frequency_hz: float, amplitudes: list[float], t: np.ndarray,
                        seed: int, warmth: float) -> tuple[np.ndarray, np.ndarray]:
    """The default single 'organ' voice, genuinely spread in stereo: a
    subtle built-in celeste (two barely-detuned unison pipes, panned
    apart) plus a centered sub-octave layer for weight."""
    detune_cents = 1.0 + 3.0 * warmth
    sub_gain = 0.08 + 0.18 * warmth
    pan_spread = 0.35 + 0.3 * warmth

    voice_lo = _organ_pipe(frequency_hz * _cents_to_ratio(-detune_cents / 2), amplitudes, t, seed)
    voice_hi = _organ_pipe(frequency_hz * _cents_to_ratio(detune_cents / 2), amplitudes, t, seed + 1)
    gl_lo, gr_lo = _pan_gains(-pan_spread)
    gl_hi, gr_hi = _pan_gains(pan_spread)

    left = voice_lo * gl_lo + voice_hi * gl_hi
    right = voice_lo * gr_lo + voice_hi * gr_hi

    sub_amplitudes = amplitudes[: max(1, len(amplitudes) // 2)]
    sub = _organ_pipe(frequency_hz / 2, sub_amplitudes, t, seed + 2) * sub_gain
    return left + sub, right + sub


def _note_envelope(n: int, attack_s: float, release_s: float) -> np.ndarray:
    attack = max(1, int(attack_s * SAMPLE_RATE))
    release = max(1, int(release_s * SAMPLE_RATE))
    env = np.ones(n)
    env[: min(attack, n)] = np.linspace(0, 1, min(attack, n)) ** 1.5
    env[-min(release, n):] *= np.linspace(1, 0, min(release, n)) ** 1.5
    return env


def _saturate(x: np.ndarray, warmth: float) -> np.ndarray:
    """Gentle tanh soft-clip -- a touch of analog-style warmth so the
    mix doesn't sit perfectly bit-clean and clinical."""
    drive = 1.0 + 1.4 * warmth
    return np.tanh(x * drive) / np.tanh(drive)


def _apply_reverb_stereo(left_dry: np.ndarray, right_dry: np.ndarray, wet: float,
                          warmth: float) -> tuple[np.ndarray, np.ndarray]:
    ir_l, ir_r = _get_impulse_response(7), _get_impulse_response(13)
    wet_l = _fft_convolve(left_dry, ir_l)
    wet_r = _fft_convolve(right_dry, ir_r)
    wet_l /= np.max(np.abs(wet_l)) + 1e-9
    wet_r /= np.max(np.abs(wet_r)) + 1e-9

    total_len = len(wet_l)
    left_padded = np.zeros(total_len)
    right_padded = np.zeros(total_len)
    left_padded[: len(left_dry)] = left_dry
    right_padded[: len(right_dry)] = right_dry
    left = (1 - wet) * left_padded + wet * wet_l
    right = (1 - wet) * right_padded + wet * wet_r

    combined = np.maximum(np.abs(left), np.abs(right))
    peak = np.max(combined)
    audible = np.where(combined > peak * 0.01)[0]
    end = min(total_len, (audible[-1] if len(audible) else total_len) + SAMPLE_RATE // 8)
    left, right = left[:end], right[:end]

    left, right = _saturate(left, warmth), _saturate(right, warmth)
    norm = max(np.max(np.abs(left)), np.max(np.abs(right))) + 1e-9
    return left / norm, right / norm


def synthesize_organ(frequency_hz: float, num_partials: int = 5, radial_rings: int = 4,
                      note_duration_s: float = 2.6, wet: float = 0.36,
                      brightness: float | None = None, warmth: float = 0.5) -> bytes:
    """The simple default sound: a single warm organ-pipe voice."""
    num_partials = max(1, min(num_partials, 16))
    amplitudes = harmonic_amplitudes(num_partials, radial_rings, brightness)
    t = np.linspace(0, note_duration_s, int(SAMPLE_RATE * note_duration_s), endpoint=False)
    left, right = _warm_organ_stereo(frequency_hz, amplitudes, t, seed=int(frequency_hz * 1000), warmth=warmth)

    peak = max(np.max(np.abs(left)), np.max(np.abs(right))) + 1e-9
    left, right = left / peak, right / peak
    env = _note_envelope(len(left), 0.3, 0.7)
    left, right = left * env, right * env

    left, right = _apply_reverb_stereo(left, right, wet, warmth)
    return _wav_bytes_stereo(left * 0.68, right * 0.68)


def synthesize_chorus(frequency_hz: float, num_partials: int = 5, radial_rings: int = 4,
                       voices: int = 4, note_duration_s: float = 2.9, wet: float = 0.4,
                       brightness: float | None = None, warmth: float = 0.5) -> bytes:
    """A harmony chord (radial rings -> chord tones) sung by a choir
    (angular folds -> detuned unison voices per tone), spread across the
    stereo field by voice."""
    num_partials = max(1, min(num_partials, 16))
    voices = max(1, min(voices, 8))
    amplitudes = harmonic_amplitudes(num_partials, radial_rings, brightness)
    t = np.linspace(0, note_duration_s, int(SAMPLE_RATE * note_duration_s), endpoint=False)

    left = np.zeros_like(t)
    right = np.zeros_like(t)
    ratios = chord_ratios(radial_rings)
    detunes = _choir_detunes_cents(voices)
    for ratio in ratios:
        tone_freq = frequency_hz * ratio
        for voice_idx, cents in enumerate(detunes):
            voice_freq = tone_freq * _cents_to_ratio(cents)
            seed = int(tone_freq * 1000) + voice_idx
            voice_wave = _organ_pipe(voice_freq, amplitudes, t, seed=seed) / (len(ratios) * voices)
            pan = 0.0 if voices <= 1 else (voice_idx / (voices - 1) - 0.5) * 1.4
            gl, gr = _pan_gains(pan)
            left += voice_wave * gl
            right += voice_wave * gr

    peak = max(np.max(np.abs(left)), np.max(np.abs(right))) + 1e-9
    left, right = left / peak, right / peak
    env = _note_envelope(len(left), 0.35, 0.85)
    left, right = left * env, right * env

    left, right = _apply_reverb_stereo(left, right, wet, warmth)
    return _wav_bytes_stereo(left * 0.68, right * 0.68)


def synthesize_classical(piece_key: str, tonic_hz: float, num_partials: int = 5,
                          radial_rings: int = 4, wet: float = 0.34,
                          brightness: float | None = None, warmth: float = 0.5,
                          tempo: float = 1.0) -> bytes:
    """A short classical motif, transposed into the derived key, played as
    organ notes with humanized timing/velocity so it doesn't sound
    quantized."""
    num_partials = max(1, min(num_partials, 16))
    amplitudes = harmonic_amplitudes(num_partials, radial_rings, brightness)
    events = music_library.render_notes(piece_key, tonic_hz, tempo=tempo, humanize=0.6,
                                         seed=int(tonic_hz * 1000))
    total_duration = max(start + dur for _, start, dur, _ in events) + 1.2
    n_total = int(SAMPLE_RATE * total_duration)
    dry = np.zeros(n_total)

    rng = np.random.default_rng(int(tonic_hz * 1000))
    for i, (freq, start_s, dur_s, velocity) in enumerate(events):
        n = int(SAMPLE_RATE * dur_s * 1.15)  # slight overlap for legato
        t = np.linspace(0, dur_s * 1.15, n, endpoint=False)
        note = _organ_pipe(freq, amplitudes, t, seed=int(freq * 1000) + i) * velocity
        note *= _note_envelope(n, 0.02, dur_s * 0.6)
        start_i = int(SAMPLE_RATE * start_s)
        end_i = min(n_total, start_i + n)
        dry[start_i:end_i] += note[: end_i - start_i]

    dry /= np.max(np.abs(dry)) + 1e-9
    # gentle, slowly wandering stereo placement -- not hard-panned, just alive
    pan_lfo = 0.15 * np.sin(2 * np.pi * 0.07 * np.linspace(0, total_duration, n_total) + rng.uniform(0, 2 * np.pi))
    gl, gr = _pan_gains(0.0)
    left = dry * gl * (1 - pan_lfo * 0.5)
    right = dry * gr * (1 + pan_lfo * 0.5)

    left, right = _apply_reverb_stereo(left, right, wet, warmth)
    return _wav_bytes_stereo(left * 0.66, right * 0.66)


def _wav_bytes_stereo(left: np.ndarray, right: np.ndarray) -> bytes:
    n = len(left)
    interleaved = np.empty(2 * n, dtype=np.int16)
    interleaved[0::2] = (np.clip(left, -1, 1) * 32767).astype(np.int16)
    interleaved[1::2] = (np.clip(right, -1, 1) * 32767).astype(np.int16)
    return _wav_bytes(interleaved, channels=2)


def _wav_bytes(pcm: np.ndarray, channels: int = 1) -> bytes:
    buf = io.BytesIO()
    data = pcm.tobytes()
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + len(data)))
    buf.write(b"WAVEfmt ")
    buf.write(struct.pack(
        "<IHHIIHH", 16, 1, channels, SAMPLE_RATE,
        SAMPLE_RATE * channels * 2, channels * 2, 16,
    ))
    buf.write(b"data")
    buf.write(struct.pack("<I", len(data)))
    buf.write(data)
    return buf.getvalue()
