# ============================================================
# NAGRIKSEVA - backend/main.py
# ============================================================

import base64
import io
import os

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Form,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from ai.language import detect_language
from ai.rag import (
    load_services,
    retrieve_service,
    build_context,
)
from ai.intent import detect_service
from ai.llm import generate_rag_response
from ai.stt import speech_to_text
from ai.tts import text_to_speech


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

if not SARVAM_API_KEY:
    raise RuntimeError(
        "SARVAM_API_KEY is not configured. "
        "Add SARVAM_API_KEY to backend/.env"
    )


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="NagrikSeva API",
    description="Multilingual AI Government Service Assistant",
    version="2.1.0",
)


# ============================================================
# CORS
# ============================================================

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

SUPPORTED_LANGUAGES = {
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
        hi
        hi-IN
        ur
        ur-IN

    into:

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

    return "en"


# ============================================================
# LANGUAGE MESSAGES
# ============================================================

MESSAGES = {
    "en": {
        "empty":
            "Please enter a question.",

        "not_found":
            "Sorry, I could not find information about that government service.",

        "error":
            "Unable to process your request.",

        "audio_required":
            "Audio file is required.",

        "audio_empty":
            "Uploaded audio is empty.",
    },

    "te": {
        "empty":
            "దయచేసి మీ ప్రశ్నను నమోదు చేయండి.",

        "not_found":
            "క్షమించండి, ఆ ప్రభుత్వ సేవకు సంబంధించిన సమాచారం కనుగొనలేకపోయాను.",

        "error":
            "మీ అభ్యర్థనను ప్రాసెస్ చేయలేకపోయాము.",

        "audio_required":
            "ఆడియో ఫైల్ అవసరం.",

        "audio_empty":
            "అప్‌లోడ్ చేసిన ఆడియో ఖాళీగా ఉంది.",
    },

    "hi": {
        "empty":
            "कृपया अपना प्रश्न दर्ज करें।",

        "not_found":
            "क्षमा करें, मुझे उस सरकारी सेवा की जानकारी नहीं मिली।",

        "error":
            "आपके अनुरोध को संसाधित नहीं किया जा सका।",

        "audio_required":
            "ऑडियो फ़ाइल आवश्यक है।",

        "audio_empty":
            "अपलोड की गई ऑडियो फ़ाइल खाली है।",
    },

    "ur": {
        "empty":
            "براہ کرم اپنا سوال درج کریں۔",

        "not_found":
            "معذرت، مجھے اس سرکاری سروس کی معلومات نہیں مل سکیں۔",

        "error":
            "آپ کی درخواست پر کارروائی نہیں ہو سکی۔",

        "audio_required":
            "آڈیو فائل ضروری ہے۔",

        "audio_empty":
            "اپ لوڈ کی گئی آڈیو خالی ہے۔",
    },
}


# ============================================================
# GET LANGUAGE MESSAGE
# ============================================================

def get_message(
    language: str,
    key: str,
) -> str:

    language = normalize_language(language)

    return (
        MESSAGES
        .get(language, MESSAGES["en"])
        .get(
            key,
            MESSAGES["en"].get(key, "")
        )
    )


# ============================================================
# SERVICES CACHE
# ============================================================

SERVICES_CACHE = []


# ============================================================
# STARTUP
#
# services.json is loaded ONCE when backend starts.
# ============================================================

@app.on_event("startup")
def startup_event():

    global SERVICES_CACHE

    print("")
    print("==========================================")
    print("          NAGRIKSEVA BACKEND")
    print("==========================================")

    try:

        SERVICES_CACHE = load_services()

        print(
            f"Services loaded : {len(SERVICES_CACHE)}"
        )

    except Exception as e:

        print(
            "[STARTUP ERROR] Unable to load services.json"
        )

        print(
            repr(e)
        )

        raise

    print("Status           : RUNNING")

    print(
        "Languages        : English / Telugu / Hindi / Urdu"
    )

    print("Service data     : Loaded once")

    print(
        "Frontend URL     :",
        FRONTEND_URL
    )

    print("==========================================")


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "success": True,
        "message": "NagrikSeva backend is running",
        "version": "2.1.0",
        "languages": list(
            SUPPORTED_LANGUAGES.keys()
        ),
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "success": True,
        "status": "healthy",
        "services_loaded": len(SERVICES_CACHE),
    }


# ============================================================
# LANGUAGE DETECTION
# ============================================================

@app.get("/detect-language")
def detect_language_api(
    q: str,
):

    query = (
        q or ""
    ).strip()

    if not query:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": get_message(
                    "en",
                    "empty",
                ),
            },
        )

    language = detect_language(query)

    return {
        "success": True,
        "query": query,
        "language": language,
        "detected_language": language,
    }


# ============================================================
# ASK GOVERNMENT SERVICE
# ============================================================

@app.get("/ask")
def ask(
    q: str,
    language: str = "auto",
):

    query = (
        q or ""
    ).strip()

    if not query:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": get_message(
                    "en",
                    "empty",
                ),
            },
        )

    # --------------------------------------------------------
    # Determine language
    # --------------------------------------------------------

    requested_language = (
        str(language or "auto")
        .lower()
        .strip()
    )

    if requested_language == "auto":

        detected_language = detect_language(
            query
        )

        final_language = detected_language

    else:

        final_language = normalize_language(
            requested_language
        )

        detected_language = detect_language(
            query
        )

    print("")
    print("==========================================")
    print(
        "[ASK] Query              :",
        query
    )
    print(
        "[ASK] Requested language:",
        requested_language
    )
    print(
        "[ASK] Detected language :",
        detected_language
    )
    print(
        "[ASK] Final language    :",
        final_language
    )
    print("==========================================")


    # --------------------------------------------------------
    # SERVICE DETECTION
    # --------------------------------------------------------

    try:

        service_id = detect_service(
            query=query,
            language=final_language,
        )

    except Exception as e:

        print(
            "[SERVICE DETECTION ERROR]",
            repr(e)
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "query": query,
                "language": final_language,
                "detected_language": detected_language,
                "message": get_message(
                    final_language,
                    "error",
                ),
                "error": str(e),
            },
        )


    # --------------------------------------------------------
    # SERVICE NOT FOUND
    # --------------------------------------------------------

    if not service_id:

        print(
            "[ASK] No matching service found."
        )

        return {
            "success": False,
            "query": query,
            "language": final_language,
            "detected_language": detected_language,
            "message": get_message(
                final_language,
                "not_found",
            ),
        }


    print(
        "[ASK] Service ID:",
        service_id
    )


    # --------------------------------------------------------
    # RETRIEVE SERVICE
    # --------------------------------------------------------

    try:

        service = retrieve_service(
            service_id
        )

    except Exception as e:

        print(
            "[SERVICE RETRIEVAL ERROR]",
            repr(e)
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "query": query,
                "language": final_language,
                "detected_language": detected_language,
                "service_id": service_id,
                "message": get_message(
                    final_language,
                    "error",
                ),
                "error": str(e),
            },
        )


    if not service:

        print(
            "[ASK] Service ID was detected but "
            "service data was not found:",
            service_id
        )

        return {
            "success": False,
            "query": query,
            "language": final_language,
            "detected_language": detected_language,
            "service_id": service_id,
            "message": get_message(
                final_language,
                "not_found",
            ),
        }


    # --------------------------------------------------------
    # BUILD LOCALIZED CONTEXT
    # --------------------------------------------------------

    context = build_context(
        service,
        final_language,
    )

    print(
        "[ASK] Localized service:",
        context.get(
            "service_name",
            "",
        )
    )


    # --------------------------------------------------------
    # GENERATE MULTILINGUAL RESPONSE
    # --------------------------------------------------------

    try:

        answer = generate_rag_response(
            query,
            context,
            final_language,
        )

    except Exception as e:

        print(
            "[LLM ERROR]",
            repr(e)
        )

        return {
            "success": False,
            "query": query,
            "language": final_language,
            "detected_language": detected_language,
            "service_id": service_id,
            "message": get_message(
                final_language,
                "error",
            ),
            "error": str(e),
        }


    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "success": True,

        "query": query,

        "language": final_language,

        "detected_language":
            detected_language,

        "intent":
            "service_guidance",

        "service_id":
            service_id,

        "service_name":
            context.get(
                "service_name",
                "",
            ),

        "description":
            context.get(
                "description",
                "",
            ),

        "eligibility":
            context.get(
                "eligibility",
                [],
            ),

        "required_documents":
            context.get(
                "required_documents",
                [],
            ),

        "application_procedure":
            context.get(
                "application_procedure",
                [],
            ),

        "fees":
            context.get(
                "fees",
                "",
            ),

        "processing_time":
            context.get(
                "processing_time",
                "",
            ),

        "contact_information":
            context.get(
                "contact_information",
                "",
            ),

        "application_url":
            context.get(
                "application_url",
                "",
            ),

        "source_url":
            context.get(
                "source_url",
                "",
            ),

        "last_verified_date":
            context.get(
                "last_verified_date",
                "",
            ),

        "answer":
            answer,
    }


# ============================================================
# STT REQUEST
# ============================================================

@app.post("/stt")
async def generate_stt(
    audio: UploadFile | None = File(None),
    file: UploadFile | None = File(None),
    language: str = Form("auto"),
):

    # --------------------------------------------------------
    # Support both:
    #
    # file
    # audio
    #
    # so the frontend can use either field name.
    # --------------------------------------------------------

    uploaded_file = (
        audio
        if audio is not None
        else file
    )

    if uploaded_file is None:

        raise HTTPException(
            status_code=400,
            detail=get_message(
                "en",
                "audio_required",
            ),
        )


    # --------------------------------------------------------
    # Read audio
    # --------------------------------------------------------

    audio_bytes = await uploaded_file.read()

    if not audio_bytes:

        raise HTTPException(
            status_code=400,
            detail=get_message(
                "en",
                "audio_empty",
            ),
        )


    # --------------------------------------------------------
    # Determine STT language
    # --------------------------------------------------------

    requested_language = (
        str(language or "auto")
        .lower()
        .strip()
    )

    if requested_language == "auto":

        # STT helper requires a language.
        #
        # English is used as the initial fallback.
        #
        # If transcript is returned in another script,
        # detect_language() will correct the final language.

        stt_language = "en"

    else:

        stt_language = normalize_language(
            requested_language
        )


    print("")
    print("==========================================")
    print(
        "[STT] Requested language:",
        requested_language,
    )
    print(
        "[STT] STT language:",
        stt_language,
    )
    print("==========================================")


    # --------------------------------------------------------
    # Convert bytes into file-like object
    # --------------------------------------------------------

    audio_stream = io.BytesIO(
        audio_bytes
    )

    audio_stream.name = (
        uploaded_file.filename
        or "nagrikseva.webm"
    )


    # --------------------------------------------------------
    # Speech recognition
    # --------------------------------------------------------

    try:

        result = speech_to_text(
            audio_stream,
            stt_language,
        )

    except ValueError as e:

        print(
            "[STT ERROR]",
            repr(e)
        )

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        print(
            "[STT ERROR]",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Speech recognition failed: {e}"
            ),
        )


    # --------------------------------------------------------
    # Extract transcript
    # --------------------------------------------------------

    transcript = (
        result.get(
            "transcript",
            "",
        )
        or result.get(
            "text",
            "",
        )
        or ""
    ).strip()


    if not transcript:

        raise HTTPException(
            status_code=400,
            detail="No speech was recognized.",
        )


    # --------------------------------------------------------
    # Detect transcript language
    # --------------------------------------------------------

    transcript_language = detect_language(
        transcript
    )


    if requested_language == "auto":

        final_language = (
            transcript_language
        )

    else:

        final_language = stt_language


    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    result["success"] = True

    result["transcript"] = transcript

    result["text"] = transcript

    result["language"] = final_language

    result["detected_language"] = (
        final_language
    )

    result["requested_language"] = (
        requested_language
    )

    result["language_code"] = (
        SUPPORTED_LANGUAGES.get(
            final_language,
            "en-IN",
        )
    )


    print("")
    print("==========================================")
    print(
        "[STT] Transcript:",
        transcript,
    )
    print(
        "[STT] Detected language:",
        transcript_language,
    )
    print(
        "[STT] Final language:",
        final_language,
    )
    print("==========================================")


    return result


# ============================================================
# TTS REQUEST MODEL
# ============================================================

class TTSRequest(BaseModel):

    text: str

    language: str = "en"


# ============================================================
# TTS
# ============================================================

@app.post("/tts")
async def generate_tts(
    request: TTSRequest,
):

    text = (
        request.text or ""
    ).strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="TTS text cannot be empty.",
        )


    language = normalize_language(
        request.language
    )


    print("")
    print("==========================================")
    print(
        "[TTS] Language:",
        language,
    )
    print("==========================================")


    # --------------------------------------------------------
    # Generate speech
    # --------------------------------------------------------

    try:

        response = text_to_speech(
            text,
            language,
        )

    except Exception as e:

        print(
            "[TTS ERROR]",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to generate speech: {e}"
            ),
        )


    # --------------------------------------------------------
    # Extract audio
    # --------------------------------------------------------

    audios = getattr(
        response,
        "audios",
        None,
    )

    if not audios:

        raise HTTPException(
            status_code=500,
            detail="TTS returned no audio.",
        )


    if isinstance(
        audios,
        list,
    ):

        audio_base64 = audios[0]

    else:

        audio_base64 = audios


    # --------------------------------------------------------
    # Decode Base64
    # --------------------------------------------------------

    try:

        audio_bytes = base64.b64decode(
            audio_base64
        )

    except Exception as e:

        print(
            "[TTS DECODE ERROR]",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to decode generated audio.",
        )


    if not audio_bytes:

        raise HTTPException(
            status_code=500,
            detail="Generated audio is empty.",
        )


    # --------------------------------------------------------
    # Return WAV audio
    # --------------------------------------------------------

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition":
                "inline; filename=nagrikseva.wav",

            "X-TTS-Language":
                language,
        },
    )