# ============================================================
# NAGRIKSEVA - backend/ai/rag.py
# ============================================================

import json
from pathlib import Path
from typing import Any


# ============================================================
# PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

SERVICES_FILE = BASE_DIR / "data" / "services.json"


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

SUPPORTED_LANGUAGES = {
    "en",
    "te",
    "hi",
    "ur",
}


# ============================================================
# SERVICES CACHE
# ============================================================

_SERVICES: list[dict] | None = None
_SERVICE_INDEX: dict[str, dict] = {}


# ============================================================
# NORMALIZE LANGUAGE
# ============================================================

def normalize_language(language: str | None) -> str:
    """
    Normalize language values such as:

        en
        en-IN
        te
        te-IN
        hi-IN
        ur-IN

    to:

        en
        te
        hi
        ur
    """

    if not language:
        return "en"

    language = (
        str(language)
        .lower()
        .strip()
        .replace("_", "-")
    )

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
# LOAD SERVICES ONCE
# ============================================================

def load_services() -> list[dict]:
    """
    Load services.json once and cache the result.
    """

    global _SERVICES

    if _SERVICES is not None:
        return _SERVICES

    if not SERVICES_FILE.exists():
        raise FileNotFoundError(
            f"services.json not found at: {SERVICES_FILE}"
        )

    try:
        with open(
            SERVICES_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in services.json: {exc}"
        ) from exc

    if not isinstance(data, list):
        raise ValueError(
            "services.json must contain a JSON array."
        )

    _SERVICES = data

    print(
        f"[RAG] Loaded {len(_SERVICES)} "
        f"services from services.json"
    )

    return _SERVICES


# ============================================================
# INITIALIZE SERVICE INDEX
# ============================================================

def initialize_services() -> dict[str, dict]:
    """
    Build an in-memory index using service_id.

    This is called during FastAPI startup.
    """

    global _SERVICE_INDEX

    services = load_services()

    _SERVICE_INDEX = {}

    for service in services:

        if not isinstance(service, dict):
            continue

        service_id = str(
            service.get(
                "service_id",
                "",
            )
        ).strip().lower()

        if service_id:
            _SERVICE_INDEX[service_id] = service

    print(
        f"[RAG] Service index ready: "
        f"{len(_SERVICE_INDEX)} services"
    )

    return _SERVICE_INDEX


# ============================================================
# GET ALL SERVICES
# ============================================================

def get_services() -> list[dict]:
    """
    Return all government services.
    """

    return load_services()


# ============================================================
# RETRIEVE SERVICE
# ============================================================

def retrieve_service(
    service_id: str | None,
) -> dict | None:
    """
    Retrieve a service using its service_id.
    """

    if not service_id:
        return None

    # Make sure index exists.
    if not _SERVICE_INDEX:
        initialize_services()

    requested_id = (
        str(service_id)
        .strip()
        .lower()
    )

    return _SERVICE_INDEX.get(
        requested_id
    )


# ============================================================
# LANGUAGE VALUE HELPER
# ============================================================

def get_language_value(
    value: Any,
    language: str,
    default: Any = None,
) -> Any:
    """
    Extract a value from a multilingual dictionary.

    Priority:

    1. Requested language
    2. English
    3. First available non-empty value
    4. Default
    """

    if value is None:
        return default

    language = normalize_language(
        language
    )

    # --------------------------------------------------------
    # Multilingual dictionary
    # --------------------------------------------------------

    if isinstance(value, dict):

        # Requested language
        if language in value:

            result = value.get(
                language
            )

            if result not in (
                None,
                "",
                [],
                {},
            ):
                return result

        # English fallback
        if "en" in value:

            result = value.get(
                "en"
            )

            if result not in (
                None,
                "",
                [],
                {},
            ):
                return result

        # Last available value
        for result in value.values():

            if result not in (
                None,
                "",
                [],
                {},
            ):
                return result

        return default

    # --------------------------------------------------------
    # Normal non-dictionary value
    # --------------------------------------------------------

    return value


# ============================================================
# BUILD LOCALIZED CONTEXT
# ============================================================

def build_context(
    service: dict,
    language: str = "en",
) -> dict:
    """
    Build a localized RAG context from a service.
    """

    language = normalize_language(
        language
    )

    return {

        # ----------------------------------------------------
        # Basic information
        # ----------------------------------------------------

        "service_id":
            service.get(
                "service_id",
                "",
            ),

        "service_name":
            get_language_value(
                service.get(
                    "service_name"
                ),
                language,
                "",
            ),

        "category":
            service.get(
                "category",
                "",
            ),

        "department":
            service.get(
                "department",
                "",
            ),

        "government_level":
            service.get(
                "government_level",
                "",
            ),

        "state":
            service.get(
                "state",
                "",
            ),

        # ----------------------------------------------------
        # Localized information
        # ----------------------------------------------------

        "description":
            get_language_value(
                service.get(
                    "description"
                ),
                language,
                "",
            ),

        "eligibility":
            get_language_value(
                service.get(
                    "eligibility"
                ),
                language,
                [],
            ),

        "required_documents":
            get_language_value(
                service.get(
                    "required_documents"
                ),
                language,
                [],
            ),

        "application_procedure":
            get_language_value(
                service.get(
                    "application_procedure"
                ),
                language,
                [],
            ),

        "fees":
            get_language_value(
                service.get(
                    "fees"
                ),
                language,
                "",
            ),

        "processing_time":
            get_language_value(
                service.get(
                    "processing_time"
                ),
                language,
                "",
            ),

        "contact_information":
            get_language_value(
                service.get(
                    "contact_information"
                ),
                language,
                "",
            ),

        # ----------------------------------------------------
        # URLs / verification
        #
        # URLs are NOT translated.
        # ----------------------------------------------------

        "application_url":
            service.get(
                "application_url",
                "",
            ),

        "source_url":
            service.get(
                "source_url",
                "",
            ),

        "last_verified_date":
            service.get(
                "last_verified_date",
                "",
            ),
    }