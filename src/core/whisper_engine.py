"""
Yerel Whisper Ses Tanıma Motoru (src/core/whisper_engine.py)
============================================================
%100 Çevrimdışı, CTranslate2 hızlandırılmış yerel Türkçe ses transkripsiyonu.
"""

import os
import tempfile
from typing import Optional

_whisper_model = None


def get_whisper_model():
    """Whisper base modelini lazy-load olarak belleğe yükler."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            # CPU int8 ile yüksek doğruluklu ve ultra hızlı (~200ms) yerel transkripsiyon
            _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        except Exception as e:
            print(f"⚠️ Whisper modeli yüklenirken hata: {e}")
            return None
    return _whisper_model


def transcribe_audio_bytes(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """Gelen ses baytlarını yerel Whisper modeli ile metne dönüştürür."""
    model = get_whisper_model()
    if not model:
        return ""

    suffix = os.path.splitext(filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, info = model.transcribe(
            tmp_path,
            language="tr",
            beam_size=3,
            initial_prompt="Türkçe doküman analizi, mali tablo, bütçe, teknik altyapı, mimari ve kurumsal soru cümleleri.",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400)
        )
        text_segments = [s.text.strip() for s in segments if s.text.strip()]
        return " ".join(text_segments)
    except Exception as e:
        print(f"⚠️ Ses transkripsiyon hatası: {e}")
        return ""
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
