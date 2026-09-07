from vector_db import semantic_search


tests = [
    ("I need proof of how much money my family earns", "en"),
    ("నా కుల ధృవీకరణ పత్రం కావాలి", "te"),
    ("मुझे जन्म प्रमाण पत्र चाहिए", "hi"),
    ("مجھے بجلی کا بل ادا کرنا ہے", "ur"),
    ("I want to apply for a driving licence", "en")
]


for query, language in tests:

    print("\nQUERY:", query)
    print("LANGUAGE:", language)

    results = semantic_search(
        query,
        language=language,
        top_k=3
    )

    for i, service_id in enumerate(results["ids"][0]):

        service_id = service_id.rsplit("_", 1)[0]
        distance = results["distances"][0][i]

        print(
            f"{i + 1}. {service_id} "
            f"(distance: {distance:.4f})"
        )