
import asyncio
import json
import logging
import re
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
    "possible ingredient duplication. Same-class warnings are informational "
    "and do not establish that a combination is unsafe. Supplementary "
    "reference data may not match the exact selected Bangladeshi product. "
    "Consult a qualified doctor or pharmacist about medication concerns."
)

SYSTEM_PROMPT = """
You are the medicine comparison assistant for DoubleDose AI.

Generate a detailed Markdown report inside the JSON field "explanation".
Use submitted database records as the primary source of truth.

REQUIRED STRUCTURE:

### 1. Summary
Describe the exact ingredient-overlap status and identify the involved
medicines when an overlap is present. Do not infer that harm will occur.

### 2. Medicine comparison
Create one table row per selected medicine with these columns:
| Medicine | Recorded active ingredients and amounts | Strength / product details | Dosage form | Manufacturer | Shared ingredients | Side-effect information status | Prescribed daily dose status |

Use supplied ingredient records, amount, unit, product details, dosage form,
and manufacturer. Do not invent missing fields.
If side effects were not supplied, say:
"Not retrieved for this report."
If personal prescribed dose was not supplied, say:
"The patient's prescribed daily dose was not supplied."
Never treat product strength as an individual's daily dose.

### 3. What the result means
Explain exact ingredient overlap separately from possible same-class duplication.

When same_class_warnings are supplied:
- Add a clearly labelled subsection named "Possible same-class duplication".
- Include the supplied therapeutic class, ingredient names, and medicines.
- Explain that this is a database-driven warning for professional review,
  not confirmation of a clinical interaction or proof that the combination
  is unsafe.
- Do not add additional class warnings not present in the supplied data.

When no same-class warnings are supplied, do not invent one.

### 4. Limitations and next steps
Explain missing or incomplete information. Recommend discussing the
medicine packages and prescribed directions with a qualified pharmacist
or doctor. Never tell a person to start, stop, skip, or change a medicine.

### 5. Available data sources and supplementary label information
List supplied ingredient sources and retrieved reference data where available.
Clearly distinguish database records from supplementary external references.
A US ingredient-level label is not automatically verified for the exact
selected Bangladeshi product. Never claim a source was retrieved if it was not.

SAFETY RULES:
- Use only the supplied facts. Never invent active ingredients, side effects,
  dosage, drug interactions, symptoms, or medical history.
- Missing data does not prove that a fact or ingredient is absent.
- Product strength is not an individualized daily dose.
- Distinguish different ingredients in the same class from exact ingredient
  overlaps.
- Do not conclude that a medicine combination is safe, unsafe, or approved.
- Include every selected medicine.
- Return detailed Markdown in "explanation", not just a short paragraph.

Return valid JSON only with exactly:
"explanation" (string), "limitations" (array of strings),
and "disclaimer" (string).
Do not wrap JSON in Markdown fences.
"""


def _cell(value: str | None, fallback: str = "Not provided") -> str:
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
    if ingredient.amount is not None:
        amount = f"{ingredient.amount:g}"
        if ingredient.unit:
            amount = f"{amount} {ingredient.unit}"
        return f"{ingredient.name} ({amount})"
    return ingredient.name


def _collect_reference_ingredients(
    payload: AIExplanationRequest,
) -> list[str]:
    candidates: list[str] = []

    for medicine in payload.medicines:
        candidates.extend(
            ingredient.name.strip()
            for ingredient in medicine.ingredients
            if ingredient.name.strip()
        )

        generic = (medicine.generic_name or "").strip()
        if generic and not re.search(r"[,;+/]", generic):
            candidates.append(generic)

    candidates.extend(
        item.name.strip()
        for item in payload.overlapping_ingredients
        if item.name.strip()
    )

    unique: list[str] = []
    seen: set[str] = set()

    for name in candidates:
        key = " ".join(name.casefold().split())
        if key not in seen:
            seen.add(key)
            unique.append(name)

    return unique[:20]


async def _retrieve_references(
    payload: AIExplanationRequest,
) -> list[dict]:
    ingredients = _collect_reference_ingredients(payload)
    if not ingredients:
        return []

    try:
        from app.services.medicine_reference_service import (
            fetch_medicine_references,
        )

        return await fetch_medicine_references(ingredients)
    except Exception:
        logger.exception(
            "Supplementary reference lookup failed; continuing without it."
        )
        return []


def _build_fallback_report(
    payload: AIExplanationRequest,
    references: list[dict],
) -> str:
    if payload.result_status == "overlap_found":
        summary = (
            "The supplied records identify active ingredients listed in "
            "multiple selected medicines. This is an ingredient overlap, "
            "not confirmation of a clinical interaction."
        )
    elif payload.result_status == "no_overlap_found":
        summary = (
            "No shared active ingredients were identified in the available "
            "records. This does not establish that the combination is safe."
        )
    else:
        summary = (
            "Some selected medicines have no linked ingredient records. "
            "The comparison is incomplete and limited to the supplied data."
        )

    lines = ["### 1. Summary", "", summary, ""]

    if payload.overlapping_ingredients:
        lines.extend(["**Recorded overlapping ingredients:**", ""])
        for item in payload.overlapping_ingredients:
            lines.append(
                f"- **{_cell(item.name)}:** listed for "
                f"{', '.join(item.medicine_names)}."
            )
        lines.append("")

    lines.extend(
        [
            "### 2. Medicine comparison",
            "",
            "| Medicine | Recorded active ingredients and amounts | "
            "Strength / product details | Dosage form | Manufacturer | "
            "Shared ingredients | Side-effect information status | "
            "Prescribed daily dose status |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )

    if not payload.medicines:
        for name in payload.medicine_names:
            values = [
                name,
                "Not provided in supplied records",
                "Not provided in supplied records",
                "Not provided in supplied records",
                "Not provided in supplied records",
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
                _ingredient_description(item)
                for item in medicine.ingredients
            ]
            if not ingredients and medicine.generic_name:
                ingredients = [medicine.generic_name]

            shared = [
                item.name
                for item in payload.overlapping_ingredients
                if any(
                    listed.casefold() == medicine.name.casefold()
                    for listed in item.medicine_names
                )
            ]

            values = [
                medicine.name,
                ", ".join(ingredients) or "Ingredient information not supplied",
                medicine.source_details,
                medicine.dosage_form,
                medicine.manufacturer,
                ", ".join(shared) if shared else "None identified in supplied results",
                "; ".join(medicine.side_effects)
                if medicine.side_effects
                else "Not retrieved for this report",
                medicine.daily_dose
                or "The patient's prescribed daily dose was not supplied",
            ]
            lines.append(
                "| " + " | ".join(_cell(value) for value in values) + " |"
            )

    lines.extend(
        [
            "",
            "### 3. What the result means",
            "",
            "Exact ingredient overlap means the submitted records identify "
            "the same active ingredient in more than one selected medicine. "
            "This may help identify duplication, but it does not confirm "
            "a clinical interaction or determine whether the combination "
            "is safe or unsafe.",
            "",
        ]
    )

    if payload.same_class_warnings:
        lines.extend(
            [
                "#### Possible same-class duplication",
                "",
                "The database has flagged the following different active "
                "ingredients as belonging to the same recorded therapeutic "
                "class. This is a separate finding from exact ingredient overlap.",
                "",
            ]
        )

        for warning in payload.same_class_warnings:
            lines.extend(
                [
                    f"**Class:** {_cell(warning.therapeutic_class)}",
                    "",
                    f"**Recorded ingredients:** "
                    f"{', '.join(warning.ingredient_names)}",
                    "",
                    f"**Medicines involved:** "
                    f"{', '.join(warning.medicine_names)}",
                    "",
                    _cell(warning.message),
                    "",
                ]
            )

        lines.extend(
            [
                "This warning does not establish that the combination is "
                "unsafe or that a clinical interaction has occurred. A "
                "qualified pharmacist or prescriber should review whether "
                "the medicines are intentionally prescribed together.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "No curated same-class warning was supplied for this "
                "comparison. That does not prove that no same-class concern "
                "exists; this feature uses a limited set of known mappings.",
                "",
            ]
        )

    lines.extend(
        [
            "### 4. Limitations and next steps",
            "",
            "This report uses submitted database records and any references "
            "retrieved below. Missing information should not be interpreted "
            "as proof that the information does not exist.",
            "",
            "Review the actual medicine packaging and prescribed directions "
            "with a qualified pharmacist or doctor. Do not change medicines "
            "or doses based only on this automated comparison.",
            "",
            "### 5. Available data sources and supplementary label information",
            "",
        ]
    )

    if not references:
        lines.append(
            "No suitable external reference was retrieved for this report."
        )
    else:
        for reference in references:
            name = _cell(
                str(reference.get("requested_ingredient") or "Unknown ingredient")
            )
            matched = _cell(
                str(reference.get("matched_ingredient") or "Not specified")
            )
            source_name = _cell(
                str(reference.get("source_name") or "External reference")
            )

            lines.extend(
                [
                    f"#### {name}",
                    "",
                    f"- Matched ingredient: {matched}",
                    f"- Source: {source_name}",
                ]
            )

            url = reference.get("source_url")
            if _valid_http_url(url):
                lines.append(f"- Reference URL: {url}")

            lines.append(
                "- Scope: supplementary US ingredient-level label; not "
                "verified against the exact selected Bangladeshi product."
            )

            for field, label in (
                ("label_effective_date", "Label effective date"),
                ("label_product_brand", "Label brand"),
                ("label_product_generic", "Label generic name"),
                ("label_manufacturer", "Label manufacturer"),
                ("label_dosage_form", "Label dosage form"),
                ("adverse_reactions", "Label adverse reactions"),
                ("warnings", "Label warnings"),
                ("contraindications", "Label contraindications"),
                ("dosage_and_administration", "General label dosage guidance"),
            ):
                if reference.get(field):
                    lines.extend(
                        ["", f"**{label}:**", "", str(reference[field])]
                    )

            lines.append("")

    return "\n".join(lines)


def _is_detailed_report(
    explanation: str,
    payload: AIExplanationRequest,
) -> bool:
    text = explanation.strip().casefold()

    required_sections = (
        "1. summary",
        "2. medicine comparison",
        "3. what the result means",
        "4. limitations and next steps",
        "5. available data sources",
    )

    if len(text) < 500 or "|" not in text:
        return False

    if not all(section in text for section in required_sections):
        return False

    if not all(name.casefold() in text for name in payload.medicine_names):
        return False

    # If the backend supplied a class warning, require the generated report
    # to include that warning rather than silently dropping it.
    for warning in payload.same_class_warnings:
        if warning.therapeutic_class.casefold() not in text:
            return False
        if not any(
            ingredient.casefold() in text
            for ingredient in warning.ingredient_names
        ):
            return False

    return True


_NEGATION = re.compile(r"(not|never|n't|no|nor|without|cannot)\W+(?:\w+\W+){0,4}$")

_UNSAFE_CLAIMS = re.compile(
    r"\b(?:you\s+should\s+|you\s+must\s+|please\s+)?"
    r"(?:stop|start|skip|discontinue|increase|decrease|reduce|double)\s+"
    r"(?:taking|using|your|the|this|these)\b"
    r"|\b(?:is|are|be)\s+(?:completely\s+|totally\s+)?safe\b"
    r"|\bno\s+(?:risk|interaction)s?\b",
    re.IGNORECASE,
)


def _violates_safety_rules(explanation: str) -> bool:
    """Reject advice to change medicines or claims that a combination is safe."""
    for match in _UNSAFE_CLAIMS.finditer(explanation):
        before = explanation[max(0, match.start() - 40) : match.start()]
        before = re.split(r"[.!?\n]", before)[-1]  # negation must be in the same sentence
        if not _NEGATION.search(before):
            return True
    return False


def _is_grounded(
    explanation: str,
    payload: AIExplanationRequest,
) -> bool:
    """Require every overlap found by the database to appear in the report."""
    text = explanation.casefold()
    return all(
        item.name.casefold() in text for item in payload.overlapping_ingredients
    )


def _fallback_response(
    payload: AIExplanationRequest,
    references: list[dict],
    reason: str,
) -> AIExplanationResponse:
    limitations = [
        "Groq did not return a complete report. This report was assembled "
        "from the supplied records and any retrieved references.",
        "The same-class warning mapping is limited and does not replace "
        "a complete clinical interaction assessment.",
        "Product-specific side effects and prescribed doses were not inferred "
        "when they were absent from the supplied information.",
    ]

    if payload.medicines_without_ingredient_data:
        limitations.append(
            "Ingredient data is missing for: "
            + ", ".join(payload.medicines_without_ingredient_data)
            + "."
        )

    logger.warning("Returning data-only report fallback: %s", reason)

    return AIExplanationResponse(
        explanation=_build_fallback_report(payload, references),
        limitations=limitations,
        disclaimer=DISCLAIMER,
    )


async def generate_overlap_explanation(
    payload: AIExplanationRequest,
) -> AIExplanationResponse:
    api_key = settings.GROQ_API_KEY.strip()
    references = await _retrieve_references(payload)

    if not api_key:
        return _fallback_response(
            payload, references, "Groq API key is not configured."
        )

    input_data = {
        "medicine_comparison": payload.model_dump(mode="json"),
        "supplementary_references": references,
    }

    client = AsyncGroq(
        api_key=api_key,
        timeout=35.0,
        max_retries=0,
    )

    max_attempts = 2
    last_error = "Incomplete AI response"

    try:
        for attempt in range(max_attempts):
            try:
                response = await client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    temperature=0.1,
                    max_completion_tokens=3000,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": (
                                "Generate the complete five-section report. "
                                "Include the exact overlaps and all supplied "
                                "same-class warnings in a separate subsection. "
                                "Include every selected medicine and use "
                                "only the supplied facts. Do not return only "
                                "a short summary.\n\n"
                                + json.dumps(
                                    input_data,
                                    ensure_ascii=False,
                                    indent=2,
                                )
                            ),
                        },
                    ],
                )

                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise ValueError("Groq returned an empty response.")

                result = AIExplanationResponse.model_validate_json(content)

                if not _is_detailed_report(result.explanation, payload):
                    raise ValueError(
                        "Groq response omitted required report sections, "
                        "a selected medicine, or a supplied same-class warning."
                    )

                if _violates_safety_rules(result.explanation):
                    raise ValueError(
                        "Groq response gave medicine-change advice or a safety claim."
                    )

                if not _is_grounded(result.explanation, payload):
                    raise ValueError(
                        "Groq response omitted an overlap found in the database."
                    )

                result.disclaimer = DISCLAIMER
                return result

            except (GroqError, ValueError) as exc:
                last_error = type(exc).__name__
                logger.warning(
                    "AI report attempt %s/%s failed (%s).",
                    attempt + 1,
                    max_attempts,
                    last_error,
                )

                if attempt < max_attempts - 1:
                    await asyncio.sleep(1.2 * (attempt + 1))

        return _fallback_response(payload, references, last_error)
    finally:
        await client.close()
