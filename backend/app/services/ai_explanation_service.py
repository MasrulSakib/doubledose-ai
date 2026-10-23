import asyncio
import logging

from groq import AsyncGroq, GroqError
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.ai_explanation import (
    AIExplanationRequest,
    AIExplanationResponse,
)

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "DoubleDose AI compares medicine information supplied to this report. "
    "It does not determine whether a medicine combination is safe or unsafe. "
    "Published prescribing information may contain additional details that "
    "were not retrieved for this report. Consult a qualified doctor or "
    "pharmacist about medication concerns."
)

SYSTEM_PROMPT = """
You are DoubleDose AI's medicine comparison and ingredient-overlap assistant.
Create a detailed Markdown report in the JSON field "explanation". A single
paragraph is not an acceptable complete report.

Use only facts explicitly supplied in the input. Never invent ingredients,
strengths, dosage forms, side effects, dosage instructions, interactions,
symptoms, clinical findings, or medical history.

Required report structure:

### 1. Summary
Write 2-4 sentences describing the result_status and every supplied shared
active ingredient. Do not claim that harm or a clinical interaction is confirmed.

### 2. Medicine comparison
Produce a Markdown table with exactly these columns:
| Medicine | Recorded ingredients | Strength / dosage form | Manufacturer | Shared ingredients | Side effects in supplied data | Daily dose supplied |
Include one row for EVERY selected medicine. Use generic_name for recorded
ingredients. Use source_details only as supplied; do not interpret a database
identifier or slug as medicine instructions. Include dosage_form and
manufacturer when supplied. Use shared-ingredient data to list overlaps.

For side effects, use only the supplied side_effects list. If empty, write:
"Not retrieved for this report; this does not mean no side effects are known."
For daily dose, use only daily_dose if explicitly supplied. If absent, write:
"Patient-specific prescribed dose was not supplied. Published dosing guidance
may exist but was not retrieved and verified for this report."
Never infer the patient's daily dose from a product's strength.

### 3. What the result means
Write at least 2-3 informative sentences. Explain what overlap means and why
checking active ingredients matters. Distinguish ingredient overlap from a
clinically confirmed drug-drug interaction. Do not declare the combination
safe or unsafe.

### 4. Limitations and next steps
Describe what this comparison does and does not establish. Important: do NOT
claim that dosage, formulation, or side-effect information does not exist
online or in official product leaflets merely because it was not supplied.
Say that such information was not retrieved or verified for this report.
Recommend reviewing the product packaging and prescribed directions with a
qualified pharmacist or doctor. Never advise changing or stopping medicine.

Other safety rules:
- A missing ingredient record does not prove an ingredient is absent.
- No overlap found does not prove a combination is safe.
- Do not advise the user to start, stop, skip, or change a medicine or dose.
- Do not use outside knowledge to fill missing fields.
- Clearly distinguish retrieved facts from missing information.
- Use a Markdown table and all four required sections.

Return valid JSON with exactly these keys:
{"explanation":"complete Markdown report","limitations":["..."],"disclaimer":"..."}
Return JSON only, with no code fence.
"""

NOT_RETRIEVED = "Not retrieved for this report; additional published product information may exist."
DOSE_NOT_SUPPLIED = (
    "Patient-specific prescribed dose was not supplied. Published dosing "
    "guidance may exist but was not retrieved and verified for this report."
)


def _cell(value: str | None, fallback: str) -> str:
    """Escape cells so supplied text cannot break the Markdown table."""
    if not value or not value.strip():
        value = fallback
    return " ".join(value.replace("|", "\\|").split())


def _same_name(first: str, second: str) -> bool:
    return " ".join(first.casefold().split()) == " ".join(
        second.casefold().split()
    )


def _build_fallback_report(payload: AIExplanationRequest) -> str:
    """Build a data-only report if the model fails or returns a short answer."""
    if payload.result_status == "overlap_found":
        summary = (
            "The supplied records identify one or more active ingredients "
            "listed in multiple selected medicines. This indicates possible "
            "ingredient duplication, not a confirmed clinical interaction."
        )
    elif payload.result_status == "no_overlap_found":
        summary = (
            "No shared active ingredients were identified in the records used "
            "for this comparison. Missing or incomplete information means this "
            "finding does not establish that the medicine combination is safe."
        )
    else:
        summary = (
            "Some ingredient records are incomplete, so the comparison cannot "
            "be considered complete. Any overlap findings below are limited "
            "to the information supplied for this report."
        )

    lines = ["### 1. Summary", "", summary, ""]
    if payload.overlapping_ingredients:
        overlaps = "; ".join(
            f"{item.name} (listed for {', '.join(item.medicine_names)})"
            for item in payload.overlapping_ingredients
        )
        lines.extend([f"**Recorded overlapping ingredients:** {overlaps}", ""])

    lines.extend(
        [
            "### 2. Medicine comparison",
            "",
            "| Medicine | Recorded ingredients | Strength / dosage form | Manufacturer | Shared ingredients | Side effects in supplied data | Daily dose supplied |",
            "|---|---|---|---|---|---|---|",
        ]
    )

    medicines = payload.medicines
    if not medicines:
        for name in payload.medicine_names:
            values = [
                name,
                "Not supplied to this report",
                "Not retrieved for this report; additional published product information may exist.",
                "Not retrieved for this report",
                "Not established from supplied data",
                NOT_RETRIEVED,
                DOSE_NOT_SUPPLIED,
            ]
            lines.append("| " + " | ".join(_cell(v, "Not supplied") for v in values) + " |")
    else:
        for medicine in medicines:
            shared = [
                ingredient.name
                for ingredient in payload.overlapping_ingredients
                if any(
                    _same_name(medicine.name, listed_name)
                    for listed_name in ingredient.medicine_names
                )
            ]
            ingredients = medicine.generic_name or "Not supplied to this report"
            strength_form = " — ".join(
                value.strip()
                for value in [medicine.source_details, medicine.dosage_form]
                if value and value.strip()
            ) or "Not retrieved for this report; additional published product information may exist."
            manufacturer = medicine.manufacturer or "Not retrieved for this report"
            side_effects = ", ".join(medicine.side_effects) if medicine.side_effects else NOT_RETRIEVED
            daily_dose = medicine.daily_dose or DOSE_NOT_SUPPLIED
            values = [
                medicine.name,
                ingredients,
                strength_form,
                manufacturer,
                ", ".join(shared) if shared else "None identified in supplied overlap results",
                side_effects,
                daily_dose,
            ]
            lines.append("| " + " | ".join(_cell(v, "Not supplied") for v in values) + " |")

    lines.extend(
        [
            "",
            "### 3. What the result means",
            "",
            "An ingredient overlap means the supplied records list the same active ingredient in more than one selected medicine. Checking active ingredients can help identify potential duplication, but this comparison does not confirm a clinical drug interaction and cannot determine whether a combination is safe or unsafe.",
            "",
            "Product strength is not the same as a patient's prescribed daily dose. The correct directions depend on the product and the individual prescription; this report does not infer them.",
            "",
            "### 4. Limitations and next steps",
            "",
            "This report uses only details supplied to DoubleDose AI for this comparison. Product leaflets or other trusted references may contain additional approved information, but those sources were not retrieved and verified as part of this report. Therefore, a missing side-effect or dosing field should not be read as proof that the information does not exist.",
            "",
            "Review the actual package and prescribed directions with a qualified pharmacist or doctor to clarify shared ingredients and appropriate dosing. Do not change prescribed medicines based only on this automated comparison.",
        ]
    )
    return "\n".join(lines)


def _is_detailed_report(explanation: str) -> bool:
    text = explanation.strip().casefold()
    required_sections = (
        "1. summary",
        "2. medicine comparison",
        "3. what the result means",
        "4. limitations and next steps",
    )
    return (
        len(text) >= 500
        and all(section in text for section in required_sections)
        and "| medicine |" in text
        and text.count("|") >= 14
    )


def _fallback_response(
    payload: AIExplanationRequest,
    reason: str,
) -> AIExplanationResponse:
    limitations = [
        "Groq did not return a complete report, so this report was assembled "
        "from the supplied medicine records rather than generated by the AI.",
        "Product-specific prescribing information and side effects are only "
        "included when supplied to this request. Their absence here does not "
        "mean that such information does not exist in official documentation.",
    ]
    if payload.medicines_without_ingredient_data:
        limitations.append(
            "Ingredient records were unavailable for: "
            + ", ".join(payload.medicines_without_ingredient_data)
            + "."
        )
    logger.warning("Returning data-only fallback report: %s", reason)
    return AIExplanationResponse(
        explanation=_build_fallback_report(payload),
        limitations=limitations,
        disclaimer=DISCLAIMER,
    )


async def generate_overlap_explanation(
    payload: AIExplanationRequest,
) -> AIExplanationResponse:
    api_key = settings.GROQ_API_KEY.strip()
    if not api_key:
        logger.error("Groq API key is not configured; using data-only report.")
        return _fallback_response(payload, "Groq API key is not configured")

    client = AsyncGroq(api_key=api_key, timeout=35.0, max_retries=0)
    input_data = payload.model_dump_json(indent=2)
    max_attempts = 2
    last_error = "Incomplete AI response"

    try:
        for attempt in range(max_attempts):
            try:
                response = await client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    temperature=0.1,
                    max_completion_tokens=1800,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": (
                                "Generate all four report sections and a table "
                                f"containing all {len(payload.medicine_names)} selected medicines. "
                                "Do not return just a summary paragraph. Use the supplied "
                                "data and explicitly distinguish information not retrieved "
                                "for this report from information that does not exist.\n\n"
                                f"Supplied records:\n{input_data}"
                            ),
                        },
                    ],
                )
                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise ValueError("Groq returned an empty response")

                try:
                    result = AIExplanationResponse.model_validate_json(content)
                except ValidationError as exc:
                    raise ValueError("Groq returned invalid response JSON") from exc

                if not _is_detailed_report(result.explanation):
                    raise ValueError("Groq response omitted required sections or table")

                result.disclaimer = DISCLAIMER
                return result

            except (GroqError, ValueError) as exc:
                last_error = type(exc).__name__
                logger.warning(
                    "AI report attempt %s/%s failed validation or API call (%s).",
                    attempt + 1,
                    max_attempts,
                    last_error,
                )
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1.2 * (attempt + 1))

        return _fallback_response(payload, last_error)
    finally:
        await client.close()
