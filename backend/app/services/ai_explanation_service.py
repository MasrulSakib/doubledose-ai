from groq import AsyncGroq

from app.core.config import settings
from app.schemas.ai_explanation import (
    AIExplanationRequest,
    AIExplanationResponse,
)


DISCLAIMER = (
    "This tool checks ingredient overlap in available records. "
    "It does not determine whether a medicine combination is safe. "
    "Consult a qualified healthcare professional about medication concerns."
)


SYSTEM_PROMPT = """
You are the ingredient-overlap explanation assistant for DoubleDose AI.

Your job is to explain supplied medicine ingredient-overlap results
in clear, concise, plain English.

Strict rules:
1. Use only the supplied data. Never invent ingredients, interactions,
   symptoms, dosages, medical history, or clinical evidence.
2. An ingredient overlap means the supplied records list the same
   active ingredient for multiple selected medicines. Explain this
   finding without claiming that harm will occur.
3. Never say that a medicine combination is safe, unsafe, or approved.
4. Never tell users to start, stop, skip, or change a medicine or dose.
5. If ingredient data is incomplete, clearly state that the available
   records are insufficient for a complete comparison.
6. If no overlap is found, say only that no overlap was found among
   the available records. Do not interpret this as proof of safety.
7. Do not treat missing ingredient data as evidence that an ingredient
   is absent.
8. Keep the explanation brief and easy for a non-medical user to
   understand.
9. Return a JSON object with exactly these fields:
   explanation (string), limitations (array of strings),
   disclaimer (string).
"""


async def generate_overlap_explanation(
    payload: AIExplanationRequest,
) -> AIExplanationResponse:
    api_key = settings.GROQ_API_KEY.strip()

    if not api_key:
        raise RuntimeError("Groq API key is not configured.")

    client = AsyncGroq(api_key=api_key)

    input_data = payload.model_dump_json(indent=2)

    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            temperature=0.2,
            max_completion_tokens=500,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        "Explain this supplied overlap result. "
                        "Return valid JSON only.\n\n"
                        f"{input_data}"
                    ),
                },
            ],
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("Groq returned an empty response.")

        result = AIExplanationResponse.model_validate_json(content)

        # Keep the disclaimer controlled by the backend.
        result.disclaimer = DISCLAIMER

        return result

    finally:
        await client.close()