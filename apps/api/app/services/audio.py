from __future__ import annotations

import base64
import hashlib
import logging

import requests

from app.services.analysis_service import build_voice_script
from app.core.config import settings

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None

logger = logging.getLogger(__name__)

LANGUAGE_CODES = {
    "hindi": "hi-IN",
    "tamil": "ta-IN",
    "telugu": "te-IN",
    "kannada": "kn-IN",
    "malayalam": "ml-IN",
    "bengali": "bn-IN",
    "marathi": "mr-IN",
    "gujarati": "gu-IN",
    "punjabi": "pa-IN",
    "english": "en-IN",
}


class AudioService:
    def __init__(self) -> None:
        self.redis = None
        if redis is not None:
            try:
                self.redis = redis.from_url(settings.redis_url)
                self.redis.ping()
            except Exception:
                self.redis = None

    def cache_key(self, analysis_id: str, language: str) -> str:
        digest = hashlib.sha256(f"{analysis_id}:{language}".encode("utf-8")).hexdigest()
        return f"audio:{digest}"

    def summarize(self, analysis: dict, language: str) -> str:
        detailed_report = analysis.get("detailed_report")
        if detailed_report:
            return build_voice_script(detailed_report, language)
        conditions = [item["condition"] for item in analysis.get("conditions", [])]
        summary = analysis.get("summary", "")
        prefix = f"Language {language}. " if language != "english" else ""
        if conditions:
            return f"{prefix}{summary} This may indicate {', '.join(conditions)}. Please consult a healthcare provider."
        return f"{prefix}{summary} Please consult a healthcare provider for interpretation."

    def generate(self, analysis_id: str, language: str, analysis: dict) -> tuple[bytes | None, str]:
        cache_key = self.cache_key(analysis_id, language)
        if self.redis is not None:
            cached = self.redis.get(cache_key)
            if cached:
                return base64.b64decode(cached), self.summarize(analysis, language)

        fallback_text = self.summarize(analysis, language)
        if not settings.sarvam_api_key:
            return None, fallback_text

        translated_text = self._translate(fallback_text, language)
        audio = self._tts(translated_text, language)
        if audio and self.redis is not None:
            self.redis.setex(cache_key, 7 * 24 * 3600, base64.b64encode(audio))
        return audio, translated_text

    def _translate(self, text: str, language: str) -> str:
        if language == "english":
            return text
        try:
            response = requests.post(
                "https://api.sarvam.ai/translate",
                headers={"api-subscription-key": settings.sarvam_api_key or "", "Content-Type": "application/json"},
                json={
                    "input": text[:1000],
                    "source_language_code": "en-IN",
                    "target_language_code": LANGUAGE_CODES.get(language, "en-IN"),
                    "speaker_gender": "Female",
                    "mode": "formal"
                },
                timeout=15,
            )
            response.raise_for_status()
            return response.json().get("translated_text", text)
        except Exception:
            logger.exception("Sarvam translation failed")
            return text

    def _tts(self, text: str, language: str) -> bytes | None:
        try:
            response = requests.post(
                "https://api.sarvam.ai/text-to-speech",
                headers={"api-subscription-key": settings.sarvam_api_key or "", "Content-Type": "application/json"},
                json={
                    "text": text[:2000],
                    "target_language_code": LANGUAGE_CODES.get(language, "en-IN"),
                    "speaker": "priya",
                    "pace": 1.0,
                    "sample_rate": 22050,
                    "model": "bulbul:v3"
                },
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            audio_b64 = (payload.get("audios") or [""])[0]
            return base64.b64decode(audio_b64) if audio_b64 else None
        except Exception:
            logger.exception("Sarvam TTS failed")
            return None


audio_service = AudioService()
