# ============================================================
# NAGRIKSEVA - backend/ai/llm.py
# ============================================================

import os

from dotenv import load_dotenv
from sarvamai import SarvamAI


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
# SARVAM CLIENT
# ============================================================

client = SarvamAI(
    api_subscription_key=SARVAM_API_KEY
)


# ============================================================
# LANGUAGE NAMES
# ============================================================

LANGUAGE_NAMES = {
    "en": "English",
    "te": "Telugu",
    "hi": "Hindi",
    "ur": "Urdu",
}


# ============================================================
# NORMALIZE LANGUAGE
# ============================================================

def normalize_language(language: str) -> str:

    language = str(language or "en").lower().strip()

    if language.startswith("te"):
        return "te"

    if language.startswith("hi"):
        return "hi"

    if language.startswith("ur"):
        return "ur"

    return "en"


# ============================================================
# NORMALIZE LIST
# ============================================================

def list_to_text(value):

    if isinstance(value, list):

        return "\n".join(
            f"- {str(item)}"
            for item in value
        )

    if value is None:
        return ""

    return str(value)


# ============================================================
# GENERATE RAG RESPONSE
# ============================================================

def generate_rag_response(
    query: str,
    context: dict,
    language: str = "en",
) -> str:

    language = normalize_language(language)

    target_language = LANGUAGE_NAMES.get(
        language,
        "English"
    )

    # --------------------------------------------------------
    # Context
    # --------------------------------------------------------

    service_name = context.get(
        "service_name",
        ""
    )

    description = context.get(
        "description",
        ""
    )

    eligibility = list_to_text(
        context.get(
            "eligibility",
            []
        )
    )

    required_documents = list_to_text(
        context.get(
            "required_documents",
            []
        )
    )

    application_procedure = list_to_text(
        context.get(
            "application_procedure",
            []
        )
    )

    fees = context.get(
        "fees",
        ""
    )

    processing_time = context.get(
        "processing_time",
        ""
    )

    contact_information = context.get(
        "contact_information",
        ""
    )

    application_url = context.get(
        "application_url",
        ""
    )

    source_url = context.get(
        "source_url",
        ""
    )

    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = f"""
You are NagrikSeva, a multilingual Indian government
service assistant.

The user's language is {target_language}.

IMPORTANT LANGUAGE RULE:

You MUST answer entirely in {target_language}.

If language = English:
Answer entirely in English.

If language = Telugu:
Answer entirely in Telugu script.

If language = Hindi:
Answer entirely in Hindi Devanagari script.

If language = Urdu:
Answer entirely in Urdu script.

Do NOT answer in English when the user asks in Hindi,
Telugu or Urdu.

Translate all headings and explanations into the target
language.

Use ONLY the government service information supplied below.

Do NOT invent:
- eligibility
- fees
- documents
- procedures
- dates
- government websites
- contact information

Keep official URLs exactly unchanged.

Give the citizen a clear and useful answer.

The answer should include the relevant information from
the supplied government service data.

Target language: {target_language}
"""

    # ========================================================
    # USER PROMPT
    # ========================================================

    user_prompt = f"""
USER QUESTION:
{query}

VERIFIED GOVERNMENT SERVICE INFORMATION:

Service Name:
{service_name}

Description:
{description}

Eligibility:
{eligibility}

Required Documents:
{required_documents}

Application Procedure:
{application_procedure}

Fees:
{fees}

Processing Time:
{processing_time}

Contact Information:
{contact_information}

Application URL:
{application_url}

Source URL:
{source_url}

Now answer the user's question.

IMPORTANT:

Return the answer entirely in {target_language}.

Do not mix English sentences into the response.

If the user asks in Hindi, answer in Hindi.
If the user asks in Telugu, answer in Telugu.
If the user asks in Urdu, answer in Urdu.
If the user asks in English, answer in English.
"""

    # ========================================================
    # SARVAM CHAT COMPLETION
    # ========================================================

    try:

        response = client.chat.completions(
            model="sarvam-105b-conversations",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.2,
            max_tokens=1500,
            reasoning_effort=None,
        )

    except TypeError:

        # Compatibility fallback for SDK versions
        # that don't expose reasoning_effort.

        response = client.chat.completions(
            model="sarvam-105b-conversations",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.2,
            max_tokens=1500,
        )

    # ========================================================
    # EXTRACT ANSWER
    # ========================================================

    try:

        answer = response.choices[0].message.content

    except Exception as e:

        raise RuntimeError(
            f"Invalid Sarvam LLM response: {e}"
        )

    if not answer:

        raise RuntimeError(
            "Sarvam returned an empty answer."
        )

    return str(answer).strip()