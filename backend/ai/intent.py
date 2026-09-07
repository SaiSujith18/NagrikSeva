"""
NagrikSeva - Intent / Service Detection

Intent detection is handled using semantic vector search.

The actual FastAPI /intent endpoint is defined in main.py.
"""

from ai.vector_db import (
    semantic_search,
    normalize_language,
)


# ============================================================
# DETECT SERVICE
# ============================================================

def detect_service(
    query: str,
    language: str = "en"
):
    """
    Detect the most relevant government service
    using multilingual semantic vector search.

    Supported languages:
        en - English
        te - Telugu
        hi - Hindi
        ur - Urdu
    """

    # --------------------------------------------------------
    # Validate query
    # --------------------------------------------------------

    if not query or not str(query).strip():
        return None

    query = str(query).strip()

    # --------------------------------------------------------
    # Normalize language
    # --------------------------------------------------------

    language = normalize_language(language)

    print("==========================================")
    print("[INTENT] Query    :", query)
    print("[INTENT] Language :", language)
    print("==========================================")

    # --------------------------------------------------------
    # Semantic search
    # --------------------------------------------------------

    results = semantic_search(
        query=query,
        language=language,
        top_k=1,
        threshold=1.0,
    )

    # --------------------------------------------------------
    # No matching service
    # --------------------------------------------------------

    if results is None:
        print("[INTENT] No service found.")
        return None

    # --------------------------------------------------------
    # Extract metadata
    # --------------------------------------------------------

    metadatas = results.get(
        "metadatas",
        [[]]
    )

    if not metadatas or not metadatas[0]:
        print("[INTENT] No metadata found.")
        return None

    service_metadata = metadatas[0][0]

    service_id = service_metadata.get(
        "service_id"
    )

    if not service_id:
        print("[INTENT] Service ID missing.")
        return None

    # --------------------------------------------------------
    # Distance
    # --------------------------------------------------------

    distances = results.get(
        "distances",
        [[]]
    )

    if distances and distances[0]:
        print(
            "[INTENT] Distance :",
            f"{distances[0][0]:.4f}"
        )

    print(
        "[INTENT] Service  :",
        service_id
    )

    return service_id