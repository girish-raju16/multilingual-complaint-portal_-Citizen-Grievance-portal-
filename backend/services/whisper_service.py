import whisper
import tempfile
import os
from pathlib import Path

_model = None


def get_model(size: str = "base"):
    """Lazy-load Whisper model (base is fast; swap to 'medium' for better multilingual accuracy)."""
    global _model
    if _model is None:
        print(f"[Whisper] Loading '{size}' model…")
        _model = whisper.load_model(size)
        print("[Whisper] Model ready.")
    return _model


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> dict:
    """
    Transcribe audio bytes to text.
    Returns: { text, language, language_probability, segments }
    """
    model = get_model()

    suffix = Path(filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = model.transcribe(
            tmp_path,
            task="transcribe",        # keep original language
            fp16=False,               # CPU-safe
            verbose=False,
        )
        return {
            "text": result["text"].strip(),
            "language": result["language"],
            "language_probability": result.get("language_probs", {}).get(result["language"], 0.0),
            "segments": [
                {"start": s["start"], "end": s["end"], "text": s["text"]}
                for s in result.get("segments", [])
            ],
        }
    finally:
        os.unlink(tmp_path)


def detect_language(text: str) -> str:
    """
    Use langdetect as a lightweight fallback for plain text language detection.
    Returns ISO 639-1 code, e.g. 'hi', 'te', 'ta', 'en'.
    """
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return "unknown"
