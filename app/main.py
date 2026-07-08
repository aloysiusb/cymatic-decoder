from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from . import symmetry, frequency_mapping, cross_domain, audio, music_library

app = FastAPI(title="Cymatic Decoder")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC_DIR / "index.html").read_text()


def _sound_params(angular_folds: int, radial_rings: int) -> dict:
    # more angular folds + radial rings -> a more intricate mode -> richer harmonic stack
    num_partials = max(1, min(16, angular_folds + radial_rings - 3))
    # angular folds -> choir voice count (an M-fold pattern sung by M detuned unison voices)
    voices = max(2, min(8, angular_folds // 2))
    return {
        "num_partials": num_partials,
        "voices": voices,
        "harmonic_amplitudes": audio.harmonic_amplitudes(num_partials, radial_rings),
    }


@app.post("/analyze")
async def analyze(image: UploadFile = File(...)):
    image_bytes = await image.read()
    try:
        sym = symmetry.detect_symmetry(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    candidates = frequency_mapping.candidate_frequencies(
        sym["angular_folds"], sym["radial_rings"]
    )
    if not candidates:
        raise HTTPException(status_code=422, detail="No matching frequency found for this symmetry")

    sound = _sound_params(sym["angular_folds"], sym["radial_rings"])

    for c in candidates:
        c["profile"] = cross_domain.profile(c["frequency_hz"])
        c["audible_tone"] = cross_domain.octave_lift(c["frequency_hz"])
        c["audible_tone"].update(sound)

    return {
        "detected_symmetry": sym,
        "candidate_frequencies": candidates,
    }


@app.get("/modes")
def modes(frequency: float):
    """The reverse direction: given a frequency, what cymatic pattern would it drive?"""
    if not (0.1 <= frequency <= 20000):
        raise HTTPException(status_code=400, detail="frequency out of range")
    m, r = frequency_mapping.forward_modes(frequency)
    profile = cross_domain.profile(frequency)
    sound = _sound_params(m, r)
    return {
        "frequency_hz": round(frequency, 2),
        "angular_folds": m,
        "radial_rings": r,
        "profile": profile,
        "sound": sound,
    }


@app.get("/classical-pieces")
def classical_pieces():
    return [{"key": k, "label": v["label"]} for k, v in music_library.MOTIFS.items()]


@app.get("/audio/{frequency_hz}.wav")
def tone(frequency_hz: float, mode: str = "organ", partials: int = 5, rings: int = 4, voices: int = 4,
         brightness: float = None, reverb: float = 0.5, warmth: float = 0.5):
    if not (0.1 <= frequency_hz <= 20000):
        raise HTTPException(status_code=400, detail="frequency out of range")
    reverb = max(0.0, min(1.0, reverb))
    warmth = max(0.0, min(1.0, warmth))
    if mode == "chorus":
        wav_bytes = audio.synthesize_chorus(
            frequency_hz, num_partials=partials, radial_rings=rings, voices=voices,
            wet=0.15 + reverb * 0.55, brightness=brightness, warmth=warmth,
        )
    else:
        wav_bytes = audio.synthesize_organ(
            frequency_hz, num_partials=partials, radial_rings=rings,
            wet=0.1 + reverb * 0.55, brightness=brightness, warmth=warmth,
        )
    return Response(content=wav_bytes, media_type="audio/wav")


@app.get("/audio/classical/{piece_key}.wav")
def classical(piece_key: str, tonic_hz: float, partials: int = 5, rings: int = 4,
              brightness: float = None, reverb: float = 0.5, warmth: float = 0.5, tempo: float = 1.0):
    if piece_key not in music_library.MOTIFS:
        raise HTTPException(status_code=404, detail="unknown piece")
    if not (0.1 <= tonic_hz <= 20000):
        raise HTTPException(status_code=400, detail="frequency out of range")
    reverb = max(0.0, min(1.0, reverb))
    warmth = max(0.0, min(1.0, warmth))
    wav_bytes = audio.synthesize_classical(
        piece_key, tonic_hz, num_partials=partials, radial_rings=rings,
        wet=0.1 + reverb * 0.5, brightness=brightness, warmth=warmth, tempo=tempo,
    )
    return Response(content=wav_bytes, media_type="audio/wav")
