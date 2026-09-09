"""
NagrikSeva - Intent / Service Detection

Service detection uses:
1. Direct keyword matching for known government services.
2. Multilingual semantic vector search as fallback.

This makes service detection more reliable in production.
"""

from ai.vector_db import (
    semantic_search,
    normalize_language,
)


# ============================================================
# DIRECT SERVICE KEYWORDS
# ============================================================

SERVICE_KEYWORDS = {

    "income_certificate": [
        "income certificate",
        "income cert",
        "income proof",
        "proof of income",
        "family income certificate",
        "income certificate apply",
        "need income certificate",
        "i need an income certificate",
        "want income certificate",
        "apply income certificate",
    ],

    "caste_certificate": [
        "caste certificate",
        "caste cert",
        "community certificate",
        "sc certificate",
        "st certificate",
        "bc certificate",
        "obc certificate",
        "caste proof",
    ],

    "residence_certificate": [
        "residence certificate",
        "residential certificate",
        "residence proof",
        "residential proof",
        "domicile certificate",
        "nativity certificate",
    ],

    "birth_certificate": [
        "birth certificate",
        "birth cert",
        "certificate of birth",
        "birth registration",
        "register birth",
    ],

    "death_certificate": [
        "death certificate",
        "death cert",
        "certificate of death",
        "death registration",
    ],

    "marriage_certificate": [
        "marriage certificate",
        "marriage cert",
        "marriage registration",
        "register marriage",
    ],

    "aadhaar": [
        "aadhaar",
        "aadhar",
        "aadhaar card",
        "aadhar card",
        "uidai",
        "aadhaar update",
        "aadhaar enrollment",
    ],

    "ration_card": [
        "ration card",
        "rationcard",
        "food security card",
        "food card",
        "ration",
    ],

    "driving_license": [
        "driving license",
        "driving licence",
        "driver license",
        "driver licence",
        "dl",
        "learning license",
        "learner license",
        "learner licence",
    ],

    "vehicle_registration": [
        "vehicle registration",
        "vehicle register",
        "car registration",
        "bike registration",
        "vehicle rc",
        "registration certificate",
        "rc book",
    ],

    "pension": [
        "pension",
        "old age pension",
        "senior citizen pension",
        "widow pension",
        "disability pension",
    ],
}


# ============================================================
# NORMALIZE QUERY
# ============================================================

def normalize_query(query: str) -> str:
    """
    Normalize user query for reliable keyword matching.
    """

    query = str(query).lower().strip()

    # Remove common punctuation
    punctuation = [
        ",",
        ".",
        "?",
        "!",
        ":",
        ";",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        "/",
        "\\",
        "-",
        "_",
    ]

    for char in punctuation:
        query = query.replace(char, " ")

    # Remove duplicate spaces
    query = " ".join(query.split())

    return query


# ============================================================
# DIRECT KEYWORD DETECTION
# ============================================================

def detect_service_by_keywords(query: str):
    """
    Detect service using direct keyword matching.

    Returns:
        service_id or None
    """

    normalized_query = normalize_query(query)

    if not normalized_query:
        return None

    # Check longer/more specific phrases first
    matches = []

    for service_id, keywords in SERVICE_KEYWORDS.items():

        for keyword in keywords:

            normalized_keyword = normalize_query(keyword)

            if normalized_keyword in normalized_query:

                matches.append(
                    (
                        len(normalized_keyword),
                        service_id,
                    )
                )

    if not matches:
        return None

    # Prefer the longest matching phrase
    matches.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    service_id = matches[0][1]

    print(
        "[INTENT] Direct keyword match:",
        service_id,
    )

    return service_id


# ============================================================
# SEMANTIC SERVICE DETECTION
# ============================================================

def detect_service_by_semantic(
    query: str,
    language: str,
):
    """
    Detect service using multilingual semantic search.

    Semantic search is used only when direct keyword
    matching cannot identify the service.
    """

    try:

        results = semantic_search(
            query=query,
            language=language,
            top_k=1,
            threshold=1.0,
        )

    except Exception as e:

        print(
            "[INTENT] Semantic search error:",
            repr(e),
        )

        return None

    if results is None:

        print(
            "[INTENT] Semantic search returned no results."
        )

        return None

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadatas = results.get(
        "metadatas",
        [[]],
    )

    if (
        not metadatas
        or not metadatas[0]
    ):

        print(
            "[INTENT] No semantic metadata found."
        )

        return None

    service_metadata = metadatas[0][0]

    if not isinstance(
        service_metadata,
        dict,
    ):

        print(
            "[INTENT] Invalid service metadata."
        )

        return None

    service_id = service_metadata.get(
        "service_id"
    )

    if not service_id:

        print(
            "[INTENT] Service ID missing from metadata."
        )

        return None

    # --------------------------------------------------------
    # Distance
    # --------------------------------------------------------

    distances = results.get(
        "distances",
        [[]],
    )

    if (
        distances
        and distances[0]
    ):

        try:

            distance = float(
                distances[0][0]
            )

            print(
                "[INTENT] Semantic distance:",
                f"{distance:.4f}",
            )

        except Exception:

            pass

    print(
        "[INTENT] Semantic service:",
        service_id,
    )

    return service_id


# ============================================================
# MAIN SERVICE DETECTION
# ============================================================

def detect_service(
    query: str,
    language: str = "en",
):
    """
    Detect the most relevant government service.

    Detection order:

        1. Direct keyword matching
        2. Semantic vector search

    Supported languages:

        en - English
        te - Telugu
        hi - Hindi
        ur - Urdu
    """

    # --------------------------------------------------------
    # Validate query
    # --------------------------------------------------------

    if not query:

        return None

    query = str(query).strip()

    if not query:

        return None

    # --------------------------------------------------------
    # Normalize language
    # --------------------------------------------------------

    try:

        language = normalize_language(
            language
        )

    except Exception:

        language = "en"

    print("")
    print("==========================================")
    print(
        "[INTENT] Query    :",
        query,
    )
    print(
        "[INTENT] Language :",
        language,
    )
    print("==========================================")

    # ========================================================
    # STEP 1 - DIRECT KEYWORD MATCH
    # ========================================================

    service_id = detect_service_by_keywords(
        query
    )

    if service_id:

        print(
            "[INTENT] Detection method: KEYWORD"
        )

        print(
            "[INTENT] Final service:",
            service_id,
        )

        return service_id

    # ========================================================
    # STEP 2 - SEMANTIC SEARCH
    # ========================================================

    print(
        "[INTENT] No direct keyword match."
    )

    print(
        "[INTENT] Trying semantic search..."
    )

    service_id = detect_service_by_semantic(
        query=query,
        language=language,
    )

    if service_id:

        print(
            "[INTENT] Detection method: SEMANTIC"
        )

        print(
            "[INTENT] Final service:",
            service_id,
        )

        return service_id

    # ========================================================
    # NO SERVICE FOUND
    # ========================================================

    print(
        "[INTENT] No matching service found."
    )

    return None