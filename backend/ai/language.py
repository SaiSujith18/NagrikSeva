# ============================================================
# NAGRIKSEVA - backend/ai/language.py
# ============================================================

import re


# ============================================================
# LANGUAGE INFORMATION
# ============================================================

LANGUAGE_NAMES = {
    "en": "English",
    "te": "Telugu",
    "hi": "Hindi",
    "ur": "Urdu",
}


LANGUAGE_CODES = {
    "en": "en-IN",
    "te": "te-IN",
    "hi": "hi-IN",
    "ur": "ur-IN",
}


# ============================================================
# NORMALIZE LANGUAGE
# ============================================================

def normalize_language(language: str | None) -> str:
    """
    Convert language values such as:

        en
        en-IN
        te
        te-IN
        hi-IN
        ur-IN

    into:

        en
        te
        hi
        ur
    """

    if not language:
        return "en"

    language = str(language).lower().strip()

    if language.startswith("te"):
        return "te"

    if language.startswith("hi"):
        return "hi"

    if language.startswith("ur"):
        return "ur"

    if language.startswith("en"):
        return "en"

    return "en"


# ============================================================
# DETECT LANGUAGE FROM TEXT
# ============================================================

def detect_language(text: str) -> str:
    """
    Detect the language from the script used in the text.

    Supported:
        English
        Telugu
        Hindi
        Urdu
    """

    if not text:
        return "en"

    text = str(text).strip()

    if not text:
        return "en"

    # --------------------------------------------------------
    # Telugu
    # --------------------------------------------------------

    if re.search(r"[\u0C00-\u0C7F]", text):
        return "te"

    # --------------------------------------------------------
    # Hindi / Devanagari
    # --------------------------------------------------------

    if re.search(r"[\u0900-\u097F]", text):
        return "hi"

    # --------------------------------------------------------
    # Urdu / Arabic script
    # --------------------------------------------------------

    if re.search(
        r"[\u0600-\u06FF"
        r"\u0750-\u077F"
        r"\uFB50-\uFDFF"
        r"\uFE70-\uFEFF]",
        text,
    ):
        return "ur"

    # --------------------------------------------------------
    # English
    # --------------------------------------------------------

    if re.search(r"[A-Za-z]", text):
        return "en"

    return "en"


# ============================================================
# LANGUAGE NAME
# ============================================================

def language_name(language: str) -> str:
    """
    Return human-readable language name.
    """

    language = normalize_language(language)

    return LANGUAGE_NAMES.get(
        language,
        "English",
    )


# ============================================================
# LANGUAGE CODE
# ============================================================

def language_code(language: str) -> str:
    """
    Convert internal language code to Sarvam language code.

    Example:
        te -> te-IN
    """

    language = normalize_language(language)

    return LANGUAGE_CODES.get(
        language,
        "en-IN",
    )