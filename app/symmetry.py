"""Detect radial/angular symmetry in an image via a polar-coordinate FFT.

The core idea: resample the image into polar coordinates around its center
(angle on one axis, radius on the other). A pattern with M-fold rotational
symmetry becomes, in polar coordinates, a signal that repeats M times per
360 degrees along the angle axis -- so summing energy along radius and
taking an FFT along angle reveals M as the dominant angular frequency.
Radial ring count is found the same way, along the radius axis.

Two things that used to be assumed are now measured, because a plate
photographed by hand is rarely centred in frame and rarely shot dead-on:

* **Centre.** Sampling polar coordinates about the wrong origin smears the
  angular FFT -- equal angles no longer cover equal parts of the pattern,
  so the repeats stop lining up and the peak flattens. We search for the
  centre that maximises angular symmetry.
* **Tilt.** A circular plate shot off-axis lands on the sensor as an
  ellipse. We search a small ellipse (axis ratio + orientation) and sample
  along it, which undoes most of that foreshortening.

Both searches score candidates with the very metric the function reports,
so the optimisation is self-validating: a candidate only wins by making the
symmetry genuinely cleaner. Everything here is NumPy + Pillow on purpose --
see the dependency note in CLAUDE.md.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageFilter, UnidentifiedImageError

# How far from the frame centre the plate centre is allowed to be, as a
# fraction of the shorter image side. 0.12 covers sloppy framing without
# letting the search wander off into a corner.
CENTRE_SEARCH_FRAC = 0.12

# Ellipse axis ratios tried when correcting for an off-axis shot. 1.0 is
# "shot dead-on"; 0.80 is roughly a 37-degree tilt.
TILT_RATIOS = (1.0, 0.94, 0.88, 0.80)

MIN_SIDE = 32

# Phone cameras hand us 12MP files; the polar grid samples at most a few
# hundred bins a side, so anything past this is cost without information.
MAX_SIDE = 1024


def load_grayscale(image_bytes: bytes) -> np.ndarray:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("L")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        # main.py turns ValueError into a 400; without this an unreadable
        # upload would surface as a 500.
        raise ValueError(f"Could not read that image: {exc}") from exc

    if min(img.size) < MIN_SIDE:
        raise ValueError(f"Image is too small to analyse (needs at least {MIN_SIDE}px a side)")

    if min(img.size) > MAX_SIDE:
        scale = MAX_SIDE / min(img.size)
        img = img.resize((max(1, round(img.width * scale)),
                          max(1, round(img.height * scale))), Image.LANCZOS)

    # A light blur costs no detail at the scale we sample but stops sensor
    # noise and JPEG blocking from showing up as spurious high-k energy.
    img = img.filter(ImageFilter.GaussianBlur(radius=1.0))
    return np.asarray(img, dtype=np.float64)


def normalise(img: np.ndarray) -> np.ndarray:
    """Stretch the middle of the histogram to full range.

    Percentiles rather than min/max so one blown highlight or dust speck
    can't flatten everything else. Uneven lighting across the plate
    otherwise contributes a strong low-k component that competes with the
    pattern itself.
    """
    lo, hi = np.percentile(img, (2.0, 98.0))
    if hi - lo < 1e-6:
        return np.zeros_like(img)
    return np.clip((img - lo) / (hi - lo), 0.0, 1.0)


def sample_polar(
    img: np.ndarray,
    cy: float,
    cx: float,
    max_radius: float,
    angle_bins: int = 512,
    radius_bins: int = 512,
    ratio: float = 1.0,
    tilt: float = 0.0,
) -> np.ndarray:
    """Bilinear-sample img on a polar grid about (cy, cx).

    `ratio` < 1 samples along an ellipse whose minor axis is `ratio` times
    the major one, with the major axis at `tilt` radians -- the inverse of
    the foreshortening a tilted circular plate undergoes. `ratio=1` is the
    plain circular remap.
    """
    h, w = img.shape

    angles = np.linspace(0, 2 * np.pi, angle_bins, endpoint=False)
    radii = np.linspace(0, max_radius, radius_bins)
    theta, r = np.meshgrid(angles, radii, indexing="ij")

    ct, st = np.cos(theta), np.sin(theta)
    if ratio == 1.0:
        dx, dy = ct, st
    else:
        ca, sa = np.cos(tilt), np.sin(tilt)
        # into the ellipse frame, squash the minor axis, back out again
        u = ct * ca + st * sa
        v = (-ct * sa + st * ca) * ratio
        dx = u * ca - v * sa
        dy = u * sa + v * ca

    xs = cx + r * dx
    ys = cy + r * dy

    x0 = np.clip(np.floor(xs).astype(int), 0, w - 2)
    y0 = np.clip(np.floor(ys).astype(int), 0, h - 2)
    fx, fy = xs - x0, ys - y0

    top = img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx
    bot = img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx
    return top * (1 - fy) + bot * fy  # shape: (angle_bins, radius_bins)


def dominant_frequency(signal: np.ndarray, min_k: int, max_k: int) -> tuple[int, float]:
    """Return (k, strength) of the strongest FFT bin in [min_k, max_k]."""
    signal = signal - signal.mean()
    spectrum = np.abs(np.fft.rfft(signal))
    max_k = min(max_k, spectrum.size - 1)
    if max_k < min_k:
        return min_k, 0.0
    band = spectrum[min_k:max_k + 1]
    if band.size == 0 or band.max() == 0:
        return min_k, 0.0
    k = min_k + int(np.argmax(band))
    strength = float(band.max() / (spectrum.sum() + 1e-9))
    return k, strength


def _angular_score(
    img: np.ndarray, cy: float, cx: float, max_radius: float,
    ratio: float = 1.0, tilt: float = 0.0,
) -> float:
    """How cleanly does the image repeat around (cy, cx)? Higher is better.

    Deliberately coarse -- this runs ~100 times during the search, and the
    peak location is stable well below full resolution.
    """
    polar = sample_polar(img, cy, cx, max_radius, angle_bins=180, radius_bins=128,
                         ratio=ratio, tilt=tilt)
    _, strength = dominant_frequency(polar.mean(axis=1), min_k=2, max_k=24)
    return strength


def find_centre(img: np.ndarray) -> tuple[float, float, float]:
    """Coarse-to-fine hunt for the centre of symmetry.

    Every candidate is scored at the same sampling radius, so the scores
    stay comparable -- a centre must win on symmetry, not by quietly
    sampling a smaller, tamer disc.
    """
    h, w = img.shape
    short = min(h, w)
    span = CENTRE_SEARCH_FRAC * short
    radius = (short / 2 - span) * 0.95

    best_y, best_x = h / 2, w / 2
    best = _angular_score(img, best_y, best_x, radius)

    step = span / 2
    for _ in range(3):
        improved_y, improved_x, improved = best_y, best_x, best
        for dy in (-step, 0.0, step):
            for dx in (-step, 0.0, step):
                if dy == 0.0 and dx == 0.0:
                    continue
                cy, cx = best_y + dy, best_x + dx
                if abs(cy - h / 2) > span or abs(cx - w / 2) > span:
                    continue
                score = _angular_score(img, cy, cx, radius)
                if score > improved:
                    improved_y, improved_x, improved = cy, cx, score
        best_y, best_x, best = improved_y, improved_x, improved
        step /= 2.5

    return best_y, best_x, best


def find_tilt(img: np.ndarray, cy: float, cx: float, max_radius: float) -> tuple[float, float]:
    """Search a small ellipse to undo an off-axis shot. Returns (ratio, tilt).

    Only accepted when it beats the dead-on reading by a clear margin --
    an ellipse has enough freedom to flatter a circular pattern slightly,
    and a spurious correction is worse than none.
    """
    best_ratio, best_tilt = 1.0, 0.0
    baseline = _angular_score(img, cy, cx, max_radius)
    best = baseline

    for ratio in TILT_RATIOS[1:]:
        for tilt in np.linspace(0, np.pi, 6, endpoint=False):
            score = _angular_score(img, cy, cx, max_radius, ratio=ratio, tilt=float(tilt))
            if score > best:
                best_ratio, best_tilt, best = ratio, float(tilt), score

    if best < baseline * 1.05:
        return 1.0, 0.0
    return best_ratio, best_tilt


def detect_symmetry(image_bytes: bytes) -> dict:
    img = normalise(load_grayscale(image_bytes))
    h, w = img.shape

    cy, cx, _ = find_centre(img)

    # With the centre known, use every pixel actually available from it
    # rather than the conservative radius the search needed.
    max_radius = min(cy, cx, h - cy, w - cx) * 0.95
    ratio, tilt = find_tilt(img, cy, cx, max_radius)

    polar = sample_polar(img, cy, cx, max_radius, ratio=ratio, tilt=tilt)

    # Angular profile: average brightness at each angle, across all radii.
    angular_profile = polar.mean(axis=1)
    m, m_strength = dominant_frequency(angular_profile, min_k=2, max_k=24)

    # Radial profile: average brightness at each radius, across all angles.
    radial_profile = polar.mean(axis=0)
    r, r_strength = dominant_frequency(radial_profile, min_k=1, max_k=12)

    short = min(h, w)
    offset = float(np.hypot(cy - h / 2, cx - w / 2) / short)

    return {
        "angular_folds": m,
        "angular_confidence": round(m_strength, 3),
        "radial_rings": r,
        "radial_confidence": round(r_strength, 3),
        # Additive: existing callers ignore these, but they make it obvious
        # when a photo was badly framed or steeply tilted.
        "centre_offset_pct": round(offset * 100, 1),
        "tilt_corrected": ratio != 1.0,
    }
