
import json
import re
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer



BASE_DIR = Path(__file__).resolve().parent.parent.parent

SERVICES_FILE = BASE_DIR / "data" / "services.json"

CHROMA_DB_DIR = BASE_DIR / "data" / "chroma_db"


LANGUAGES = ["en", "te", "hi", "ur"]


model = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2"
)




chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DB_DIR)
)

collection = chroma_client.get_or_create_collection(
    name="government_services"
)




def normalize_language(language: str) -> str:

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

    return "en"




def load_services():

    if not SERVICES_FILE.exists():
        raise FileNotFoundError(
            f"services.json not found at: {SERVICES_FILE}"
        )

    with open(
        SERVICES_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "services.json must contain a JSON array."
        )

    return data




KEYWORDS = {

    "income_certificate": {

        "en": [
            "income",
            "earnings",
            "salary",
            "annual income",
            "family income",
            "income proof",
            "income certificate",
        ],

        "te": [
            "ఆదాయం",
            "ఆదాయ",
            "సంపాదన",
            "జీతం",
            "వార్షిక ఆదాయం",
            "కుటుంబ ఆదాయం",
            "ఆదాయ ధృవీకరణ",
            "ఆదాయ ధృవీకరణ పత్రం",
            "ఆదాయ సర్టిఫికేట్",
        ],

        "hi": [
            "आय",
            "आय प्रमाण",
            "आय प्रमाण पत्र",
            "आय प्रमाणपत्र",
            "कमाई",
            "वेतन",
            "वार्षिक आय",
            "परिवार की आय",
        ],

        "ur": [
            "آمدنی",
            "آمدن",
            "کمائی",
            "تنخواہ",
            "سالانہ آمدنی",
            "خاندان کی آمدنی",
            "آمدنی کا ثبوت",
            "آمدنی کا سرٹیفکیٹ",
        ],
    },


    "caste_certificate": {

        "en": [
            "caste",
            "community",
            "sc",
            "st",
            "bc",
            "oc",
            "caste certificate",
            "community certificate",
            "social category",
        ],

        "te": [
            "కులం",
            "కుల",
            "కుల ధృవీకరణ",
            "కుల ధృవీకరణ పత్రం",
            "కుల సర్టిఫికేట్",
            "కమ్యూనిటీ సర్టిఫికేట్",
            "సామాజిక వర్గం",
            "ఎస్సీ",
            "ఎస్టీ",
            "బీసీ",
            "ఓసీ",
        ],

        "hi": [
            "जाति",
            "जाति प्रमाण",
            "जाति प्रमाण पत्र",
            "जाति प्रमाणपत्र",
            "समुदाय",
            "समुदाय प्रमाण पत्र",
            "सामाजिक वर्ग",
            "एससी",
            "एसटी",
            "बीसी",
            "ओबीसी",
        ],

        "ur": [
            "ذات",
            "ذات کا سرٹیفکیٹ",
            "ذات کا ثبوت",
            "برادری",
            "برادری کا سرٹیفکیٹ",
            "سماجی زمرہ",
        ],
    },


    "residence_certificate": {

        "en": [
            "residence",
            "address",
            "domicile",
            "living place",
            "proof of residence",
            "address certificate",
            "residence certificate",
            "domicile certificate",
        ],

        "te": [
            "నివాసం",
            "నివాస",
            "చిరునామా",
            "డొమిసైల్",
            "నివాస రుజువు",
            "నివాస ధృవీకరణ",
            "నివాస ధృవీకరణ పత్రం",
            "నివాస సర్టిఫికేట్",
            "చిరునామా ధృవీకరణ",
        ],

        "hi": [
            "निवास",
            "निवासी",
            "पता",
            "अधिवास",
            "डोमिसाइल",
            "निवास प्रमाण",
            "निवास प्रमाण पत्र",
            "निवास प्रमाणपत्र",
            "पता प्रमाण",
        ],

        "ur": [
            "رہائش",
            "رہائشی",
            "پتہ",
            "ڈومیسائل",
            "رہائش کا ثبوت",
            "رہائشی سرٹیفکیٹ",
            "پتہ کا ثبوت",
        ],
    },


    "birth_certificate": {

        "en": [
            "birth",
            "newborn",
            "child",
            "date of birth",
            "birth registration",
            "birth certificate",
        ],

        "te": [
            "జననం",
            "జనన",
            "పుట్టిన",
            "బిడ్డ",
            "పుట్టిన తేదీ",
            "జనన నమోదు",
            "జనన ధృవీకరణ",
            "జనన ధృవీకరణ పత్రం",
        ],

        "hi": [
            "जन्म",
            "जन्म तिथि",
            "नवजात",
            "बच्चा",
            "जन्म पंजीकरण",
            "जन्म प्रमाण पत्र",
            "जन्म प्रमाणपत्र",
        ],

        "ur": [
            "پیدائش",
            "نوزائیدہ",
            "بچہ",
            "تاریخ پیدائش",
            "پیدائش کا اندراج",
            "پیدائش کا سرٹیفکیٹ",
        ],
    },


    "death_certificate": {

        "en": [
            "death",
            "deceased",
            "death registration",
            "death record",
            "death certificate",
        ],

        "te": [
            "మరణం",
            "మరణించిన",
            "మరణ నమోదు",
            "మరణ రికార్డు",
            "మరణ ధృవీకరణ",
            "మరణ ధృవీకరణ పత్రం",
        ],

        "hi": [
            "मृत्यु",
            "मृतक",
            "मृत्यु पंजीकरण",
            "मृत्यु रिकॉर्ड",
            "मृत्यु प्रमाण पत्र",
            "मृत्यु प्रमाणपत्र",
        ],

        "ur": [
            "وفات",
            "مرنے والا",
            "وفات کا اندراج",
            "وفات کا ریکارڈ",
            "وفات کا سرٹیفکیٹ",
        ],
    },


    "family_member_certificate": {

        "en": [
            "family member",
            "family members",
            "family relationship",
            "family certificate",
            "relatives",
            "legal family members",
            "family details",
        ],

        "te": [
            "కుటుంబ సభ్యుడు",
            "కుటుంబ సభ్యులు",
            "కుటుంబ సంబంధం",
            "కుటుంబ సభ్యుల ధృవీకరణ పత్రం",
            "కుటుంబ సర్టిఫికేట్",
            "బంధువులు",
            "కుటుంబ వివరాలు",
        ],

        "hi": [
            "परिवार सदस्य",
            "परिवार के सदस्य",
            "पारिवारिक संबंध",
            "परिवार सदस्य प्रमाण पत्र",
            "रिश्तेदार",
            "परिवार विवरण",
        ],

        "ur": [
            "خاندانی رکن",
            "خاندان کے افراد",
            "خاندانی تعلق",
            "خاندانی رکن کا سرٹیفکیٹ",
            "رشتہ دار",
            "خاندان کی تفصیلات",
        ],
    },


    "property_tax": {

        "en": [
            "property tax",
            "house tax",
            "building tax",
            "municipal tax",
            "property payment",
        ],

        "te": [
            "ఆస్తి పన్ను",
            "ఇంటి పన్ను",
            "భవనం పన్ను",
            "మున్సిపల్ పన్ను",
            "ఆస్తి చెల్లింపు",
        ],

        "hi": [
            "संपत्ति कर",
            "मकान कर",
            "भवन कर",
            "नगर पालिका कर",
            "संपत्ति भुगतान",
        ],

        "ur": [
            "جائیداد ٹیکس",
            "مکان ٹیکس",
            "عمارت ٹیکس",
            "میونسپل ٹیکس",
            "جائیداد کی ادائیگی",
        ],
    },


    "electricity_services": {

        "en": [
            "electricity",
            "power",
            "current",
            "electricity bill",
            "power bill",
            "bill payment",
            "electricity connection",
        ],

        "te": [
            "విద్యుత్",
            "కరెంట్",
            "కరెంట్ బిల్లు",
            "విద్యుత్ బిల్లు",
            "బిల్లు చెల్లింపు",
            "విద్యుత్ కనెక్షన్",
        ],

        "hi": [
            "बिजली",
            "विद्युत",
            "करंट",
            "बिजली बिल",
            "बिल भुगतान",
            "बिजली कनेक्शन",
        ],

        "ur": [
            "بجلی",
            "برقی",
            "کرنٹ",
            "بجلی کا بل",
            "بل کی ادائیگی",
            "بجلی کا کنکشن",
        ],
    },


    "water_services": {

        "en": [
            "water",
            "water connection",
            "water bill",
            "water supply",
            "drinking water",
            "water services",
        ],

        "te": [
            "నీరు",
            "నీటి కనెక్షన్",
            "నీటి బిల్లు",
            "నీటి సరఫరా",
            "తాగునీరు",
            "నీటి సేవలు",
        ],

        "hi": [
            "पानी",
            "जल कनेक्शन",
            "पानी का बिल",
            "जल आपूर्ति",
            "पेयजल",
            "जल सेवाएं",
        ],

        "ur": [
            "پانی",
            "پانی کا کنکشن",
            "پانی کا بل",
            "پانی کی فراہمی",
            "پینے کا پانی",
        ],
    },


    "rta_services": {

        "en": [
            "rta",
            "transport",
            "driving licence",
            "driving license",
            "vehicle registration",
            "rc",
            "road transport",
        ],

        "te": [
            "ఆర్టీఏ",
            "రవాణా",
            "డ్రైవింగ్ లైసెన్స్",
            "వాహనం",
            "వాహన రిజిస్ట్రేషన్",
            "ఆర్సీ",
            "రోడ్డు రవాణా",
        ],

        "hi": [
            "आरटीए",
            "परिवहन",
            "ड्राइविंग लाइसेंस",
            "वाहन पंजीकरण",
            "आरसी",
            "सड़क परिवहन",
        ],

        "ur": [
            "آر ٹی اے",
            "ٹرانسپورٹ",
            "ڈرائیونگ لائسنس",
            "گاڑی رجسٹریشن",
            "آر سی",
            "سڑک ٹرانسپورٹ",
        ],
    },


    "scholarships": {

        "en": [
            "scholarship",
            "student",
            "education",
            "financial assistance",
            "school",
            "college",
        ],

        "te": [
            "స్కాలర్‌షిప్",
            "విద్యార్థి",
            "విద్య",
            "ఆర్థిక సహాయం",
            "పాఠశాల",
            "కళాశాల",
            "ఉపకార వేతనం",
        ],

        "hi": [
            "छात्रवृत्ति",
            "छात्र",
            "शिक्षा",
            "आर्थिक सहायता",
            "स्कूल",
            "कॉलेज",
            "स्कॉलरशिप",
        ],

        "ur": [
            "اسکالرشپ",
            "طالب علم",
            "تعلیم",
            "مالی امداد",
            "اسکول",
            "کالج",
        ],
    },
}



def create_service_text(
    service,
    language
):

    language = normalize_language(language)

    service_id = service.get(
        "service_id",
        ""
    )

    service_name = service.get(
        "service_name",
        {}
    ).get(
        language,
        ""
    )

    description = service.get(
        "description",
        {}
    ).get(
        language,
        ""
    )

    keyword_text = " ".join(
        KEYWORDS
        .get(service_id, {})
        .get(language, [])
    )

    return (
        f"{service_name}. "
        f"{description}. "
        f"{keyword_text}"
    ).strip()




def build_vector_database():

    services = load_services()

    documents = []
    ids = []
    metadatas = []

    for service in services:

        service_id = service.get(
            "service_id",
            ""
        )

        if not service_id:
            continue

        for language in LANGUAGES:

            document_id = (
                f"{service_id}_{language}"
            )

            text = create_service_text(
                service,
                language
            )

            documents.append(text)

            ids.append(document_id)

            metadatas.append({

                "service_id":
                    service_id,

                "language":
                    language,

                "category":
                    service.get(
                        "category",
                        ""
                    ),

                "department":
                    service.get(
                        "department",
                        ""
                    ),

                "state":
                    service.get(
                        "state",
                        ""
                    ),
            })

    if not documents:

        raise RuntimeError(
            "No service documents found."
        )

    print(
        f"[VECTOR DB] Creating "
        f"{len(documents)} documents..."
    )

    embeddings = model.encode(
        documents,
        normalize_embeddings=True,
        show_progress_bar=True
    ).tolist()

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(
        "[VECTOR DB] Database built successfully."
    )

    return len(documents)




def normalize_search_text(text: str) -> str:

    text = str(text or "").lower().strip()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text



def keyword_score(
    query: str,
    service_id: str,
    language: str
) -> int:

    query = normalize_search_text(query)

    keywords = (
        KEYWORDS
        .get(service_id, {})
        .get(language, [])
    )

    score = 0

    for keyword in keywords:

        keyword = normalize_search_text(
            keyword
        )

        if not keyword:
            continue

        if keyword in query:

            # Longer phrases are stronger signals.
            if len(keyword) >= 10:
                score += 4

            elif len(keyword) >= 5:
                score += 3

            else:
                score += 2

    return score



def calculate_service_score(
    query: str,
    service_id: str,
    language: str,
    distance: float
) -> float:

    # Chroma distance:
    # lower = better
    #
    # Convert it into a similarity-like score.
    semantic_score = 1.0 / (
        1.0 + max(float(distance), 0.0)
    )

    # Keyword signal
    keyword_points = keyword_score(
        query,
        service_id,
        language
    )

    # Strong deterministic boost.
    #
    # This is intentionally larger than the
    # small differences between similar
    # certificate embeddings.
    keyword_boost = min(
        keyword_points * 0.08,
        0.40
    )

    return semantic_score + keyword_boost




def semantic_search(
    query,
    language="en",
    top_k=3,
    threshold=1.0
):

    if not query or not str(query).strip():
        return None

    language = normalize_language(language)

    query = str(query).strip()

  

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    ).tolist()

  

    candidate_count = max(
        top_k,
        5
    )

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=candidate_count,
        where={
            "language": language
        },
        include=[
            "metadatas",
            "documents",
            "distances",
        ],
    )

    # --------------------------------------------------------
    # No results
    # --------------------------------------------------------

    if (
        not results
        or not results.get("ids")
        or not results["ids"][0]
    ):
        return None

    ids = results["ids"][0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    documents = results.get(
        "documents",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]

    candidates = []

    for index in range(len(ids)):

        metadata = (
            metadatas[index]
            if index < len(metadatas)
            else {}
        )

        service_id = metadata.get(
            "service_id",
            ""
        )

        distance = (
            distances[index]
            if index < len(distances)
            else 1.0
        )

        score = calculate_service_score(
            query=query,
            service_id=service_id,
            language=language,
            distance=distance
        )

        candidates.append({

            "id":
                ids[index],

            "document":
                documents[index]
                if index < len(documents)
                else "",

            "metadata":
                metadata,

            "distance":
                distance,

            "score":
                score,
        })

    # --------------------------------------------------------
    # Sort by combined semantic + keyword score
    # --------------------------------------------------------

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    if not candidates:
        return None

    best = candidates[0]

    # --------------------------------------------------------
    # Weak semantic match protection
    #
    # Keep the original threshold behavior.
    # --------------------------------------------------------

    if float(best["distance"]) > threshold:

        # However, if the query has a strong exact
        # service keyword, allow it through.
        strong_keyword_match = (
            keyword_score(
                query,
                best["metadata"].get(
                    "service_id",
                    ""
                ),
                language
            ) >= 2
        )

        if not strong_keyword_match:
            return None

    # --------------------------------------------------------
    # Return Chroma-compatible structure.
    #
    # intent.py already expects:
    #
    # results["metadatas"][0][0]["service_id"]
    # --------------------------------------------------------

    selected = candidates[:top_k]

    return {

        "ids": [[
            item["id"]
            for item in selected
        ]],

        "documents": [[
            item["document"]
            for item in selected
        ]],

        "metadatas": [[
            item["metadata"]
            for item in selected
        ]],

        "distances": [[
            item["distance"]
            for item in selected
        ]],

        # Extra debugging information.
        "scores": [[
            item["score"]
            for item in selected
        ]],
    }


# ============================================================
# GET BEST SERVICE ID
# ============================================================

def get_best_service_id(
    query,
    language="en",
    threshold=1.0
):

    results = semantic_search(
        query=query,
        language=language,
        top_k=1,
        threshold=threshold
    )

    if not results:
        return None

    metadata = results.get(
        "metadatas",
        [[]]
    )[0]

    if not metadata:
        return None

    return metadata[0].get(
        "service_id"
    )