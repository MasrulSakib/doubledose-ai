
import asyncio
import logging
from urllib.parse import urlparse

from groq import AsyncGroq, GroqError

from app.core.config import settings
from app.schemas.ai_explanation import (
    AIExplanationRequest,
    AIExplanationResponse,
)

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "DoubleDose AI compares available medicine records and identifies "
    "possible ingredient duplication. It does not determine whether a "
    "medicine combination is safe or unsafe. This report is not a substitute "
    "for advice from a qualified doctor or pharmacist."
)

SYSTEM_PROMPT = """
You are the medicine comparison assistant for DoubleDose AI.

Generate a detailed, readable Markdown report inside the JSON field
"explanation". Use the supplied structured medicine records as the source
of truth. Do not invent, infer, or silently change medical facts.

REQUIRED SECTIONS:

### 1. Summary
Explain the comparison status and identify all recorded overlapping
ingredients and the selected medicines containing them.

### 2. Medicine comparison
Create a Markdown table containing one row for every selected medicine.
Use these columns:

| Medicine | Recorded active ingredients | Product strength/details | Dosage form | Manufacturer | Shared ingredients | Side effects information | Dose information |

For each medicine:
- List every supplied active ingredient, including its amount and unit
  when those values are present.
- Include supplied source details, dosage form and manufacturer.
- Identify the shared ingredients using the supplied overlap results.
- If side-effect information is absent, say:
  "Not retrieved for this report; verified product-specific information
  was not supplied."
- If daily dose is absent, say:
  "The patient's prescribed daily dose was not supplied."
- Never interpret product strength as an individual's daily dose.
- Do not claim that the absence of information in this request means the
  information does not exist in published product documentation.

### 3. What the result means
Explain the actual recorded ingredient overlap in plain language.
Distinguish an exact active-ingredient overlap from a possible same-class
duplication. Only mention same-class duplication if the supplied records
contain reliable information supporting the classification.

Do not claim that an overlap proves a clinical interaction, that a
combination is safe, or that harm will occur.

### 4. Limitations and next steps
State what the records do and do not establish. Explain that product-specific
side-effect and prescribing information was not retrieved if no such data
was supplied. Recommend reviewing the actual packaging and prescription
with a qualified pharmacist or doctor.

### 5. Available data sources
Where source URLs or names are supplied, list them alongside the relevant
medicine or ingredient. A source URL is not proof that the information has
been reviewed or verified. Never describe a source as official unless the
input establishes that fact.

ADDITIONAL RULES:
1. Include all selected medicines; do not omit a medicine because some
   information is missing.
2. Use the supplied generic names and ingredient records. If they conflict,
   disclose the discrepancy rather than guessing.
3. Missing data does not prove that an ingredient or side effect is absent.
4. Do not give individualized dosing instructions.
5. Never tell the user to start, stop, skip, or change a medicine or dose.
6. Keep the report detailed but clear. A single-paragraph answer is
   insufficient.
7. Return valid JSON only, with exactly these keys:
   "explanation" (string), "limitations" (array of strings),
   "disclaimer" (string).
8. Put the Markdown report in "explanation". Do not wrap the JSON in a
   Markdown code fence.
"""


def _cell(value: str | None, fallback: str = "Not provided") -> str:
    """Format a value for a Markdown table cell."""
    if not value or not value.strip():
        value = fallback

    return " ".join(value.replace("|", "\\|").split())


def _valid_http_url(url: str | None) -> bool:
    if not url:
        return False

    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def _ingredient_description(ingredient) -> str:
    name = ingredient.name

    if ingredient.amount is not None:
        amount = f"{ingredient.amount:g}"
        if ingredient.unit:
            amount = f"{amount} {ingredient.unit}"
        return f"{name} ({amount})"

    if ingredient.unit:
        return f"{name} (amount not provided; unit listed: {ingredient.unit})"

    return name


def _build_fallback_report(payload: AIExplanationRequest) -> str:
    """Build a structured report strictly from submitted database records."""
    if payload.result_status == "overlap_found":
        summary = (
            "The supplied records identify one or more active ingredients "
            "listed in multiple selected medicines. This is a recorded "
            "ingredient overlap, not confirmation of a clinical interaction."
        )
    elif payload.result_status == "no_overlap_found":
        summary = (
            "No shared active ingredients were identified among the "
            "available ingredient records. Missing or incomplete data "
            "means this result does not establish that the combination "
            "is safe."
        )
    else:
        summary = (
            "Some selected medicines have no linked ingredient records. "
            "The comparison is therefore incomplete, and any overlap "
            "finding is limited to the information recorded."
        )

    lines = [
        "### 1. Summary",
        "",
        summary,
        "",
    ]

    if payload.overlapping_ingredients:
        lines.extend(
            [
                "**Recorded overlapping ingredients:**",
                "",
            ]
        )

        for item in payload.overlapping_ingredients:
            lines.append(
                f"- **{_cell(item.name)}**: listed for "
                + ", ".join(item.medicine_names)
                + "."
            )

        lines.append("")

    lines.extend(
        [
            "### 2. Medicine comparison",
            "",
            "| Medicine | Recorded active ingredients | Product strength/details | "
            "Dosage form | Manufacturer | Shared ingredients | "
            "Side effects information | Dose information |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )

    medicines_by_id = {}
    for medicine in payload.medicines:
        medicines_by_id[medicine.name.casefold()] = medicine

    if not payload.medicines:
        for name in payload.medicine_names:
            values = [
                name,
                "Not provided in the supplied records",
                "Not provided in the supplied records",
                "Not provided in the supplied records",
                "Not provided in the supplied records",
                "Unable to establish from supplied records",
                "Not retrieved for this report",
                "The patient's prescribed daily dose was not supplied",
            ]
            lines.append(
                "| " + " | ".join(_cell(value) for value in values) + " |"
            )
    else:
        for medicine in payload.medicines:
            ingredients = [
                _ingredient_description(ingredient)
                for ingredient in medicine.ingredients
            ]

            if not ingredients and medicine.generic_name:
                ingredients = [medicine.generic_name]

            shared = [
                item.name
                for item in payload.overlapping_ingredients
                if any(
                    listed_name.casefold() == medicine.name.casefold()
                    for listed_name in item.medicine_names
                )
            ]

            values = [
                medicine.name,
                ", ".join(ingredients)
                or "Ingredient information not retrieved for this medicine",
                medicine.source_details,
                medicine.dosage_form,
                medicine.manufacturer,
                ", ".join(shared) if shared else "None identified in supplied results",
                (
                    "; ".join(medicine.side_effects)
                    if medicine.side_effects
                    else "Not retrieved for this report"
                ),
                (
                    medicine.daily_dose
                    if medicine.daily_dose
                    else "The patient's prescribed daily dose was not supplied"
                ),
            ]

            lines.append(
                "| " + " | ".join(_cell(value) for value in values) + " |"
            )

    lines.extend(
        [
            "",
            "### 3. What the result means",
            "",
            "An ingredient overlap means that the supplied medicine records "
            "list the same active ingredient in more than one selected "
            "medicine. This can help identify possible duplication, but "
            "does not, by itself, establish whether a combination is safe "
            "or unsafe or confirm a clinical drug interaction.",
            "",
            "The recorded product strength and dosage form describe the "
            "product information available to this comparison. They do not "
            "establish the dose prescribed for an individual patient.",
            "",
            "### 4. Limitations and next steps",
            "",
            "This report uses the information submitted to DoubleDose AI. "
            "Product leaflets or other trusted references may contain "
            "additional details that have not been retrieved here. Missing "
            "side-effect or dosage information must not be interpreted as "
            "proof that the information does not exist.",
            "",
            "Review the actual medicine packaging and prescribed directions "
            "with a qualified pharmacist or doctor. Do not change medicines "
            "or doses based only on this automated comparison.",
            "",
            "### 5. Available data sources",
            "",
        ]
    )

    has_sources = False

    for medicine in payload.medicines:
        for ingredient in medicine.ingredients:
            if not ingredient.source_name and not ingredient.source_url:
                continue

            has_sources = True
            source_label = ingredient.source_name or "Recorded ingredient source"

            if _valid_http_url(ingredient.source_url):
                source_text = f"[{source_label}]({ingredient.source_url})"
            else:
                source_text = source_label

            lines.append(
                f"- **{medicine.name} — {ingredient.name}:** {source_text}"
            )

            if ingredient.retrieved_at:
                lines.append(
                    f"  - Recorded retrieval timestamp: {ingredient.retrieved_at}"
                )

    if not has_sources:
        lines.append(
            "No ingredient source names or URLs were supplied for this report."
        )

    return "\n".join(lines)


def _is_detailed_report(
    explanation: str,
    medicine_names: list[str],
) -> bool:
    """Reject responses that omit key report sections or selected medicines."""
    text = explanation.strip().casefold()

    required_sections = (
        "1. summary",
        "2. medicine comparison",
        "3. what the result means",
        "4. limitations and next steps",
        "5. available data sources",
    )

    if not all(section in text for section in required_sections):
        return False

    if "|" not in text or len(text) < 500:
        return False

    return all(name.casefold() in text for name in medicine_names)


def _fallback_response(
    payload: AIExplanationRequest,
    reason: str,
) -> AIExplanationResponse:
    limitations = [
        "Groq did not return a complete report; this report was assembled "
        "from the supplied database records instead.",
        "Product-specific side effects and published dosing guidance have "
        "not been verified unless explicitly supplied in the input.",
    ]

    if payload.medicines_without_ingredient_data:
        limitations.append(
            "Ingredient data is missing for: "
            + ", ".join(payload.medicines_without_ingredient_data)
            + "."
        )

    logger.warning("Returning data-only report fallback: %s", reason)

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
        raise RuntimeError("Groq API key is not configured.")

    client = AsyncGroq(
        api_key=api_key,
        timeout=35.0,
        max_retries=0,
    )

    input_data = payload.model_dump_json(indent=2)
    max_attempts = 2
    last_error = "Incomplete AI response"

    try:
        for attempt in range(max_attempts):
            try:
                response = await client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    temperature=0.1,
                    max_completion_tokens=2500,
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": (
                                "Create the complete five-section Markdown "
                                "report. Include every selected medicine, "
                                "its supplied active ingredients, amounts, "
                                "source details, dosage form, manufacturer, "
                                "overlapping ingredients, and source metadata. "
                                "Do not invent information absent from the "
                                "request. Do not return just a short summary.\n\n"
                                f"Supplied medicine records:\n{input_data}"
                            ),
                        },
                    ],
                )

                content = response.choices[0].message.content

                if not content or not content.strip():
                    raise ValueError("Groq returned an empty response.")

                result = AIExplanationResponse.model_validate_json(content)

                if not _is_detailed_report(
                    result.explanation,
                    payload.medicine_names,
                ):
                    raise ValueError(
                        "Groq response omitted required report sections, "
                        "the comparison table, or selected medicine names."
                    )

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
