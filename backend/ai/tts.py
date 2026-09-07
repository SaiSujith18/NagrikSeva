# ============================================================
# NAGRIKSEVA - backend/ai/tts.py
# ============================================================

import os

from dotenv import load_dotenv
from sarvamai import SarvamAI


load_dotenv()

SARVAM_API_KEY = os.getenv(
    "SARVAM_API_KEY"
)

if not SARVAM_API_KEY:
    raise RuntimeError(
        "SARVAM_API_KEY is not configured."
    )


client = SarvamAI(
    api_subscription_key=SARVAM_API_KEY
)


LANGUAGE_CODES = {
    "en": "en-IN",
    "te": "te-IN",
    "hi": "hi-IN",
    "ur": "ur-IN",
}


def text_to_speech(
    text: str,
    language: str = "en"
):

    if not text or not text.strip():
        raise ValueError(
            "TTS text cannot be empty."
        )

    language = (
        language or "en"
    ).lower().strip()

    language_code = LANGUAGE_CODES.get(
        language,
        "en-IN"
    )

    text = text.strip()

    if len(text) > 2500:
        text = text[:2500]

    return client.text_to_speech.convert(
        text=text,
        model="bulbul:v3",
        language_code=language_code,
        speaker="shubh",
        pace=1.0,
    )