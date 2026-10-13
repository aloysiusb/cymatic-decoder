"""Symmetry-detection tests.

Runs standalone (`venv/bin/python tests/test_symmetry.py`) or under pytest,
so it needs no dev dependency beyond what the app already installs.

The patterns are synthetic and carry one clean angular frequency, so the
expected fold count isn't a judgement call -- which is what makes the
off-centre cases meaningful: the detector either still recovers M once the
plate is shifted and tilted, or it doesn't.
"""
from __future__ import annotations

import io
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import symmetry  # noqa: E402

SIZE = 480
RNG = np.random.default_rng(7)


def render(M: int, N: int = 3, off_frac: float = 0.0, off_angle: float = 0.7,
           ratio: float = 1.0, tilt: float = 0.0, noise: float = 0.03) -> bytes:
    """A disc with M-fold angular structure and N radial rings, as a PNG."""
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(float)
    cy = SIZE / 2 + off_frac * SIZE * math.sin(off_angle)
    cx = SIZE / 2 + off_frac * SIZE * math.cos(off_angle)

    dx, dy = xx - cx, yy - cy
    if ratio != 1.0:  # squash, mimicking an off-axis shot
        ca, sa = math.cos(tilt), math.sin(tilt)
        u = dx * ca + dy * sa
        v = (-dx * sa + dy * ca) / ratio
        dx, dy = u * ca - v * sa, u * sa + v * ca

    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    R = SIZE * 0.42
    rho = np.clip(r / R, 0, 1)

    img = (0.5 + 0.25 * np.cos(M * th) * np.cos(np.pi * rho / 2)
               + 0.20 * np.cos(N * np.pi * rho))
    img[r > R] = 0.5
    img = np.clip(img + RNG.normal(0, noise, img.shape), 0, 1)

    buf = io.BytesIO()
    Image.fromarray((img * 255).astype(np.uint8), "L").save(buf, format="PNG")
    return buf.getvalue()


def test_recovers_folds_when_centred():
    for M in (4, 6, 8, 10):
        got = symmetry.detect_symmetry(render(M))["angular_folds"]
        assert got == M, f"centred M={M}: got {got}"


def test_recovers_folds_when_off_centre():
    """The case the old centred-assumption code got wrong."""
    for M in (4, 6, 8, 10):
        for off in (0.04, 0.08, 0.12):
            got = symmetry.detect_symmetry(render(M, off_frac=off))["angular_folds"]
            assert got == M, f"M={M} at {off:.0%} offset: got {got}"


def test_recovers_folds_when_tilted():
    for M in (6, 8):
        for ratio in (0.88, 0.80):
            got = symmetry.detect_symmetry(
                render(M, off_frac=0.03, off_angle=1.2, ratio=ratio, tilt=0.6)
            )["angular_folds"]
            assert got == M, f"M={M} at tilt ratio {ratio}: got {got}"


def test_reports_the_offset_it_found():
    sym = symmetry.detect_symmetry(render(6, off_frac=0.10))
    assert sym["centre_offset_pct"] > 5.0, sym


def test_confidence_survives_being_off_centre():
    centred = symmetry.detect_symmetry(render(6))["angular_confidence"]
    shifted = symmetry.detect_symmetry(render(6, off_frac=0.10))["angular_confidence"]
    assert shifted > centred * 0.6, f"centred {centred}, shifted {shifted}"


def test_keeps_the_keys_the_frontends_render():
    sym = symmetry.detect_symmetry(render(6))
    for key in ("angular_folds", "angular_confidence", "radial_rings", "radial_confidence"):
        assert key in sym, f"missing {key}"


def test_unreadable_upload_raises_valueerror():
    """main.py maps ValueError to a 400; anything else escapes as a 500."""
    for bad in (b"not an image", b"", b"\x89PNG\r\n\x1a\n truncated"):
        try:
            symmetry.detect_symmetry(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad!r}")


def test_degenerate_images_do_not_crash():
    def png(arr):
        buf = io.BytesIO()
        Image.fromarray(arr, "L").save(buf, format="PNG")
        return buf.getvalue()

    for arr in (np.zeros((200, 200), np.uint8),
                np.full((200, 200), 255, np.uint8),
                (RNG.random((200, 200)) * 255).astype(np.uint8)):
        symmetry.detect_symmetry(png(arr))


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
    print("\nall passed" if not failures else f"\n{failures} failed")
    sys.exit(1 if failures else 0)
