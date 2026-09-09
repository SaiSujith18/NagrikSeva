
import os

from dotenv import load_dotenv
from sarvamai import SarvamAI


load_dotenv()

SARVAM_API_KEY = os.getenv(
    "SARVAM_API_KEY"
)

if not SARVAM_API_KEY:
    raise RuntimeError(
        "SARVAM_API_KEY is not configured. "
        "Add SARVAM_API_KEY to backend/.env"
    )


client = SarvamAI(
    api_subscription_key=SARVAM_API_KEY
)


LANGUAGE_MAP = {
    "en": "en-IN",
    "en-in": "en-IN",
    "te": "te-IN",
    "te-in": "te-IN",
    "hi": "hi-IN",
    "hi-in": "hi-IN",
    "ur": "ur-IN",
    "ur-in": "ur-IN",
}


def normalize_language(
    language: str
) -> str:

    language = (
        str(language or "en")
        .lower()
        .strip()
    )

    return LANGUAGE_MAP.get(
        language,
        "en-IN"
    )


def short_language(
    language_code: str
) -> str:

    code = str(
        language_code or "en"
    ).lower().strip()

    if code.startswith("te"):
        return "te"

    if code.startswith("hi"):
        return "hi"

    if code.startswith("ur"):
        return "ur"

    return "en"


def speech_to_text(
    audio_file,
    language="en"
):

    if audio_file is None:
        raise ValueError(
            "Audio file is required."
        )

    audio_bytes = audio_file.read()

    if not audio_bytes:
        raise ValueError(
            "Uploaded audio file is empty."
        )

    language_code = normalize_language(
        language
    )

    sarvam_file = (
        "nagrikseva.webm",
        audio_bytes,
        "audio/webm"
    )

    try:

        response = (
            client
            .speech_to_text
            .transcribe(
                file=sarvam_file,
                model="saaras:v4",
                mode="transcribe",
                language_code=language_code,
            )
        )

    except Exception as e:

        raise ValueError(
            f"Sarvam STT failed: {e}"
        )

    transcript = (
        getattr(
            response,
            "transcript",
            ""
        )
        or ""
    ).strip()

    if not transcript:

        raise ValueError(
            "Sarvam returned an empty transcript."
        )

    detected_code = getattr(
        response,
        "language_code",
        None
    )

    detected_language = short_language(
        detected_code or language_code
    )

    return {

        "success": True,

        "transcript": transcript,

        "text": transcript,

        "language": detected_language,

        "detected_language":
            detected_language,

        "language_code":
            detected_code or language_code,
    }