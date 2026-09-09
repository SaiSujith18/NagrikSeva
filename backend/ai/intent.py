"""
NagrikSeva - Intent / Service Detection

Detects the most relevant government service using
multilingual semantic vector search.

The FastAPI /ask endpoint is defined in main.py.
"""

from ai.vector_db import (
    semantic_search,
    normalize_language,
)


def detect_service(
    query: str,
    language: str = "en",
):
    """
    Detect the most relevant government service.

    Supported languages:
        en - English
        te - Telugu
        hi - Hindi
        ur - Urdu

    Returns:
        service_id -> if a matching service is found
        None       -> if no service is found
    """

    # ========================================================
    # 1. Validate query
    # ========================================================

    if not query:
        print("[INTENT] Empty query.")
        return None

    query = str(query).strip()

    if not query:
        print("[INTENT] Empty query after stripping.")
        return None

    # ========================================================
    # 2. Normalize language
    # ========================================================

    try:
        language = normalize_language(language)
    except Exception:
        language = "en"

    print("")
    print("==========================================")
    print("           SERVICE DETECTION")
    print("==========================================")
    print("[INTENT] Query    :", query)
    print("[INTENT] Language :", language)
    print("==========================================")

    # ========================================================
    # 3. Semantic search
    #
    # IMPORTANT:
    # Do NOT use threshold=1.0 here.
    #
    # A threshold of 1.0 can reject almost every query
    # depending on how semantic_search() calculates
    # similarity/distance.
    #
    # We first retrieve the best matching service and
    # then inspect the result.
    # ========================================================

    try:

        results = semantic_search(
            query=query,
            language=language,
            top_k=3,
        )

    except TypeError:

        # Fallback in case semantic_search() requires
        # the threshold parameter.

        print(
            "[INTENT] semantic_search requires threshold."
        )

        try:

            results = semantic_search(
                query=query,
                language=language,
                top_k=3,
                threshold=0.0,
            )

        except Exception as e:

            print(
                "[INTENT] Semantic search error:",
                repr(e),
            )

            return None

    except Exception as e:

        print(
            "[INTENT] Semantic search error:",
            repr(e),
        )

        return None

    # ========================================================
    # 4. Check search result
    # ========================================================

    if not results:

        print("[INTENT] No search results.")
        return None

    print(
        "[INTENT] Search result type:",
        type(results).__name__,
    )

    # ========================================================
    # 5. Extract metadata
    # ========================================================

    metadatas = results.get(
        "metadatas",
        [],
    )

    if not metadatas:

        print("[INTENT] No metadata returned.")
        print("[INTENT] Raw results:", results)

        return None

    # Chroma-style result:
    #
    # metadatas = [
    #     [
    #         {...},
    #         {...}
    #     ]
    # ]
    #

    if isinstance(metadatas, list):

        if len(metadatas) == 0:
            print("[INTENT] Metadata list is empty.")
            return None

        first_metadata_group = metadatas[0]

    else:

        first_metadata_group = metadatas

    if not first_metadata_group:

        print("[INTENT] No metadata documents found.")
        return None

    # ========================================================
    # 6. Get best matching service
    # ========================================================

    service_metadata = first_metadata_group[0]

    if not isinstance(
        service_metadata,
        dict,
    ):

        print(
            "[INTENT] Invalid metadata:",
            service_metadata,
        )

        return None

    # ========================================================
    # 7. Extract service ID
    # ========================================================

    service_id = service_metadata.get(
        "service_id"
    )

    if not service_id:

        print(
            "[INTENT] service_id missing from metadata."
        )

        print(
            "[INTENT] Metadata:",
            service_metadata,
        )

        return None

    # ========================================================
    # 8. Distance / similarity information
    # ========================================================

    distances = results.get(
        "distances",
        [],
    )

    if distances:

        try:

            first_distance_group = distances[0]

            if first_distance_group:

                score = first_distance_group[0]

                print(
                    "[INTENT] Match score/distance:",
                    f"{float(score):.4f}",
                )

        except Exception:

            print(
                "[INTENT] Could not read match score."
            )

    # ========================================================
    # 9. Debug information
    # ========================================================

    print(
        "[INTENT] Service ID:",
        service_id,
    )

    print(
        "[INTENT] Metadata:",
        service_metadata,
    )

    print("==========================================")
    print(
        "[INTENT] MATCH FOUND:",
        service_id,
    )
    print("==========================================")
    print("")

    # ========================================================
    # 10. Return service ID
    # ========================================================

    return str(service_id)