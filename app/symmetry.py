"""Detect radial/angular symmetry in an image via a polar-coordinate FFT.

The core idea: resample the image into polar coordinates around its center
(angle on one axis, radius on the other). A pattern with M-fold rotational
symmetry becomes, in polar coordinates, a signal that repeats M times per
360 degrees along the angle axis -- so summing energy along radius and
taking an FFT along angle reveals M as the dominant angular frequency.
Radial ring count is found the same way, along the radius axis.
"""
import io
import numpy as np
from PIL import Image


def load_grayscale(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("L")
    return np.asarray(img, dtype=np.float64)


def to_polar(img: np.ndarray, angle_bins: int = 512, radius_bins: int = 512) -> np.ndarray:
    """Bilinear-sample img at (angle, radius) grid points around its center."""
    h, w = img.shape
    cy, cx = h / 2, w / 2
    max_radius = min(cy, cx) * 0.95

    angles = np.linspace(0, 2 * np.pi, angle_bins, endpoint=False)
    radii = np.linspace(0, max_radius, radius_bins)
    theta, r = np.meshgrid(angles, radii, indexing="ij")

    xs = cx + r * np.cos(theta)
    ys = cy + r * np.sin(theta)

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
    band = spectrum[min_k:max_k + 1]
    if band.size == 0 or band.max() == 0:
        return min_k, 0.0
    k = min_k + int(np.argmax(band))
    strength = float(band.max() / (spectrum.sum() + 1e-9))
    return k, strength


def detect_symmetry(image_bytes: bytes) -> dict:
    img = load_grayscale(image_bytes)
    polar = to_polar(img)

    # Angular profile: average brightness at each angle, across all radii.
    angular_profile = polar.mean(axis=1)
    m, m_strength = dominant_frequency(angular_profile, min_k=2, max_k=24)

    # Radial profile: average brightness at each radius, across all angles.
    radial_profile = polar.mean(axis=0)
    r, r_strength = dominant_frequency(radial_profile, min_k=1, max_k=12)

    return {
        "angular_folds": m,
        "angular_confidence": round(m_strength, 3),
        "radial_rings": r,
        "radial_confidence": round(r_strength, 3),
    }
