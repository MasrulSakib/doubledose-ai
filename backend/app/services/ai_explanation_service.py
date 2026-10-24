
import asyncio
import json
import logging
import re
from urllib.parse import quote, urlparse

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
You are the explanatory assistant for DoubleDose AI.

Write only a concise explanation of the supplied medicine-comparison results.
Do not generate a comparison table or a sources section; those are generated
separately from structured data.

Return valid JSON with exactly these fields:
- explanation: string
- limitations: array of strings
- disclaimer: string

Rules:
- Use only the supplied facts.
- Explain exact ingredient overlaps without claiming a clinical interaction.
- Discuss supplied same-class warnings only, distinguishing them from exact
  ingredient overlap.
- Do not invent side effects, dosage, interactions, or medical history.
- Do not claim that a medicine combination is safe or unsafe.
- Never advise starting, stopping, skipping, or changing medicines.
- Missing data does not prove that a fact or ingredient is absent.
- Do not give personalized dosing advice.
- Keep the explanation concise and suitable for insertion into a fixed report.
- Return JSON only, without Markdown fences.
"""


def _plain(value, fallback: str = "Not provided") -> str:
    if value is None:
        return fallback

    text = " ".join(str(value).split())
    return text if text else fallback


def _cell(value, fallback: str = "Not provided") -> str:
    """Escape Markdown table delimiters and flatten multiline values."""
    text = _plain(value, fallback)
    return text.replace("\\", "\\\\").replace("|", "\\|")


def _short_reference_text(
    value,
    max_length: int = 500,
) -> str | None:
    if not value:
        return None

    text = " ".join(str(value).split())
    if not text:
        return None

    if len(text) <= max_length:
        return text

    truncated = text[:max_length].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{truncated}… [truncated; consult the source label]"


def _valid_http_url(url) -> bool:
    if not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
            and not any(char.isspace() for char in url)
        )
    except ValueError:
        return False


def _markdown_link(label: str, url: str) -> str:
    """Create a Markdown link only for a validated HTTP(S) URL."""
    safe_label = label.replace("[", "\\[").replace("]", "\\]")
    safe_url = quote(url, safe=":/?&=%#@+,$;~!*'()-._")
    return f"[{safe_label}]({safe_url})"


def _ingredient_description(ingredient) -> str:
    if ingredient.amount is not None:
        amount = f"{ingredient.amount:g}"
        if ingredient.unit:
            amount = f"{amount} {ingredient.unit}"
        return f"{ingredient.name} ({amount})"

    return ingredient.name


def _extract_strength(source_details: str | None) -> str:
    """
    Extract strength from the existing source_details field without
    displaying unrelated IDs, generic names, or slugs in the strength column.
    """
    if not source_details:
        return "Not supplied in database record"

    patterns = (
        r"(?:^|\|)\s*Strength\s*:\s*(.*?)(?=\s*\||$)",
        r"\bStrength\s*:\s*(.*?)(?=\s*\||$)",
    )

    for pattern in patterns:
        match = re.search(pattern, source_details, re.IGNORECASE)
        if match:
            strength = match.group(1).strip().strip("*").strip()
            if strength:
                return strength

    # Some records may contain a plain strength without a "Strength:" label.
    if "|" not in source_details and len(source_details) <= 100:
        return source_details.strip()

    return "Not supplied in database record"


def _medicine_shared_ingredients(
    payload: AIExplanationRequest,
    medicine_name: str,
) -> list[str]:
    shared = []

    for overlap in payload.overlapping_ingredients:
        if any(
            name.casefold() == medicine_name.casefold()
            for name in overlap.medicine_names
        ):
            shared.append(overlap.name)

    return shared


def _collect_reference_ingredients(
    payload: AIExplanationRequest,
) -> list[str]:
    candidates = []

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

    unique = []
    seen = set()

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


def _build_comparison_table(payload: AIExplanationRequest) -> str:
    lines = [
        "| Medicine | Recorded active ingredients (amounts when supplied) "
        "| Strength / product details | Dosage form | Manufacturer "
        "| Shared ingredients | Side-effect information status "
        "| Prescribed daily dose status |",
        "|---|---|---|---|---|---|---|---|",
    ]

    medicines = payload.medicines

    if not medicines:
        for name in payload.medicine_names:
            values = [
                name,
                "Ingredient information not supplied",
                "Not supplied in database record",
                "Not provided",
                "Not provided",
                "Unable to establish from supplied records",
                "Not retrieved for this report",
                "The patient's prescribed daily dose was not supplied",
            ]
            lines.append("| " + " | ".join(_cell(v) for v in values) + " |")

        return "\n".join(lines)

    for medicine in medicines:
        ingredients = [
            _ingredient_description(item)
            for item in medicine.ingredients
        ]

        if not ingredients and medicine.generic_name:
            ingredients = [medicine.generic_name]

        shared = _medicine_shared_ingredients(payload, medicine.name)

        side_effect_status = (
            "; ".join(medicine.side_effects)
            if medicine.side_effects
            else "Not retrieved for this report"
        )

        daily_dose_status = (
            medicine.daily_dose
            if medicine.daily_dose
            else "The patient's prescribed daily dose was not supplied"
        )

        values = [
            medicine.name,
            ", ".join(ingredients) or "Ingredient information not supplied",
            _extract_strength(medicine.source_details),
            medicine.dosage_form,
            medicine.manufacturer,
            ", ".join(shared) if shared else "None identified in supplied results",
            side_effect_status,
            daily_dose_status,
        ]

        lines.append("| " + " | ".join(_cell(value) for value in values) + " |")

    return "\n".join(lines)


def _build_overlap_section(payload: AIExplanationRequest) -> str:
    lines = ["### 1. Summary", ""]

    if payload.result_status == "overlap_found":
        lines.extend([
            "The supplied records identify the following exact ingredient "
            "overlap. This is a database finding, not confirmation of a "
            "clinical interaction.",
            "",
        ])

        for item in payload.overlapping_ingredients:
            medicines = ", ".join(item.medicine_names) or "Not specified"
            lines.append(
                f"- **{_cell(item.name)}:** listed for "
                f"{_cell(medicines)}."
            )

        if not payload.overlapping_ingredients:
            lines.append(
                "The result status indicates an overlap, but no overlapping "
                "ingredient details were supplied. The result needs review."
            )

    elif payload.result_status == "no_overlap_found":
        lines.extend([
            "No shared active ingredients were identified in the supplied "
            "records. This does not establish that the combination is safe.",
        ])

    else:
        lines.extend([
            "The comparison is incomplete because some selected medicines "
            "have no linked ingredient records. Do not interpret missing "
            "ingredient data as proof that there is no overlap.",
        ])

    return "\n".join(lines)


def _build_meaning_section(payload: AIExplanationRequest) -> str:
    lines = [
        "### 3. What the result means",
        "",
        "Ingredient overlap identifies the same recorded active ingredient "
        "in multiple selected medicines. It does not by itself establish "
        "a clinical interaction or determine whether a combination is safe.",
        "",
    ]

    if payload.same_class_warnings:
        lines.extend([
            "#### Possible same-class duplication",
            "",
            "The database supplied the following therapeutic-class warnings. "
            "These are separate from exact ingredient overlap and require "
            "professional review.",
            "",
        ])

        for warning in payload.same_class_warnings:
            lines.extend([
                f"- **Class:** {_cell(warning.therapeutic_class)}",
                f"  - **Ingredients:** {_cell(', '.join(warning.ingredient_names))}",
                f"  - **Medicines:** {_cell(', '.join(warning.medicine_names))}",
                f"  - **Database note:** {_cell(warning.message)}",
                "",
            ])

        lines.append(
            "These database warnings do not confirm a clinical interaction "
            "or prove that the combination is unsafe."
        )
    else:
        lines.append(
            "No curated same-class warning was supplied for this comparison. "
            "The mapping is limited, so this does not prove that no "
            "same-class concern exists."
        )

    return "\n".join(lines)


def _build_limitations_section(
    payload: AIExplanationRequest,
) -> str:
    lines = [
        "### 4. Limitations and next steps",
        "",
        "This report is limited to the supplied medicine records and any "
        "supplementary references retrieved below. Missing information "
        "should not be interpreted as proof that the information does not exist.",
        "",
    ]

    if payload.medicines_without_ingredient_data:
        lines.append(
            "**Medicines without linked ingredient data:** "
            + ", ".join(payload.medicines_without_ingredient_data)
            + "."
        )
        lines.append("")

    if any(not medicine.ingredients for medicine in payload.medicines):
        lines.extend([
            "One or more selected medicines have no ingredient entries "
            "in the supplied records.",
            "",
        ])

    lines.extend([
        "Product strength is not an individual's prescribed daily dose. "
        "Side-effect information and prescribed directions may be incomplete.",
        "",
        "Review the actual medicine packages and prescribed directions "
        "with a qualified pharmacist or doctor. Do not change medicines "
        "or doses based only on this automated comparison.",
    ])

    return "\n".join(lines)


def _build_reference_section(references: list[dict]) -> str:
    lines = [
        "### 5. Available data sources and supplementary label information",
        "",
        "**Primary source: submitted medicine database records.**",
        "",
    ]

    if not references:
        lines.append(
            "No suitable external reference was retrieved for this report."
        )
        return "\n".join(lines)

    for reference in references:
        requested = _plain(
            reference.get("requested_ingredient"),
            "Unknown ingredient",
        )
        matched = _plain(
            reference.get("matched_ingredient"),
            "Not specified",
        )
        source_name = _plain(
            reference.get("source_name"),
            "External reference",
        )

        lines.extend([
            f"#### {_cell(requested)}",
            "",
            f"- **Matched ingredient:** {_cell(matched)}",
            f"- **Source:** {_cell(source_name)}",
        ])

        source_url = reference.get("source_url")
        if _valid_http_url(source_url):
            lines.append(
                "- **Reference URL:** "
                + _markdown_link("Open source label", source_url)
            )

        scope = _plain(
            reference.get("reference_scope"),
            "Supplementary ingredient-level reference; product-specific "
            "equivalence has not been verified.",
        )
        lines.append(f"- **Scope:** {_cell(scope)}")

        country = reference.get("source_country")
        if country:
            lines.append(f"- **Source country:** {_cell(country)}")

        fields = (
            ("label_effective_date", "Label effective date", 40),
            ("label_product_brand", "Label brand", 100),
            ("label_product_generic", "Label generic name", 150),
            ("label_manufacturer", "Label manufacturer", 150),
            ("label_dosage_form", "Label dosage form", 100),
            ("warnings", "Label warning excerpt", 500),
            ("adverse_reactions", "Adverse reaction excerpt", 500),
            ("contraindications", "Contraindication excerpt", 500),
        )

        for field, label, max_length in fields:
            value = _short_reference_text(
                reference.get(field),
                max_length=max_length,
            )
            if value:
                lines.extend([
                    "",
                    f"**{label}:**",
                    "",
                    value,
                ])

        lines.append("")

    return "\n".join(lines).strip()


def _build_fallback_report(
    payload: AIExplanationRequest,
    references: list[dict],
    ai_explanation: str | None = None,
) -> str:
    """Build a stable report with a fixed structure and deterministic data."""
    sections = [
        _build_overlap_section(payload),
        "### 2. Medicine comparison\n\n"
        + _build_comparison_table(payload),
        _build_meaning_section(payload),
        _build_limitations_section(payload),
        _build_reference_section(references),
    ]

    # AI prose is deliberately isolated from database values, comparison
    # tables, and source references.
    if ai_explanation and ai_explanation.strip():
        sections[2] += (
            "\n\n#### Additional explanation\n\n"
            + ai_explanation.strip()
        )

    return "\n\n".join(sections).strip()


def _fallback_response(
    payload: AIExplanationRequest,
    references: list[dict],
    reason: str,
) -> AIExplanationResponse:
    limitations = [
        "The report structure and medicine comparison were generated "
        "deterministically from supplied records.",
        "The same-class warning mapping is limited and does not replace "
        "a complete clinical interaction assessment.",
        "Product-specific side effects and prescribed doses were not inferred "
        "when absent from the supplied information.",
    ]

    if payload.medicines_without_ingredient_data:
        limitations.append(
            "Ingredient data is missing for: "
            + ", ".join(payload.medicines_without_ingredient_data)
            + "."
        )

    logger.warning("Using deterministic report: %s", reason)

    return AIExplanationResponse(
        explanation=_build_fallback_report(payload, references),
        limitations=limitations,
        disclaimer=DISCLAIMER,
    )


async def _generate_ai_explanation(
    client: AsyncGroq,
    payload: AIExplanationRequest,
) -> str:
    input_data = {
        "result_status": payload.result_status,
        "medicine_names": payload.medicine_names,
        "overlapping_ingredients": [
            item.model_dump(mode="json")
            for item in payload.overlapping_ingredients
        ],
        "same_class_warnings": [
            item.model_dump(mode="json")
            for item in payload.same_class_warnings
        ],
        "medicines_without_ingredient_data": (
            payload.medicines_without_ingredient_data
        ),
    }

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        temperature=0,
        max_completion_tokens=700,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Explain these supplied results in a concise paragraph. "
                    "Do not produce a table or sources section.\n\n"
                    + json.dumps(input_data, ensure_ascii=False)
                ),
            },
        ],
    )

    content = response.choices[0].message.content
    if not content or not content.strip():
        raise ValueError("Groq returned an empty response.")

    result = AIExplanationResponse.model_validate_json(content)
    explanation = result.explanation.strip()

    if not explanation or len(explanation) > 2500:
        raise ValueError("Groq returned an invalid explanation length.")

    return explanation


async def generate_overlap_explanation(
    payload: AIExplanationRequest,
) -> AIExplanationResponse:
    references = await _retrieve_references(payload)
    api_key = settings.GROQ_API_KEY.strip()

    if not api_key:
        return _fallback_response(
            payload,
            references,
            "Groq API key is not configured.",
        )

    client = AsyncGroq(
        api_key=api_key,
        timeout=35.0,
        max_retries=0,
    )

    try:
        last_error = "Incomplete AI response"

        for attempt in range(2):
            try:
                ai_explanation = await _generate_ai_explanation(
                    client,
                    payload,
                )

                limitations = [
                    "The comparison uses the supplied database records; "
                    "ingredient data may be incomplete.",
                    "Supplementary US labels are not verified against the "
                    "exact selected Bangladeshi products.",
                    "Same-class warning mappings are limited and do not "
                    "replace a complete clinical interaction assessment.",
                ]

                if payload.medicines_without_ingredient_data:
                    limitations.append(
                        "Ingredient data is missing for: "
                        + ", ".join(
                            payload.medicines_without_ingredient_data
                        )
                        + "."
                    )

                return AIExplanationResponse(
                    explanation=_build_fallback_report(
                        payload,
                        references,
                        ai_explanation=ai_explanation,
                    ),
                    limitations=limitations,
                    disclaimer=DISCLAIMER,
                )

            except (GroqError, ValueError, json.JSONDecodeError) as exc:
                last_error = type(exc).__name__
                logger.warning(
                    "AI explanation attempt %s/2 failed (%s).",
                    attempt + 1,
                    last_error,
                )

                if attempt == 0:
                    await asyncio.sleep(1.0)

        return _fallback_response(payload, references, last_error)

    finally:
        await client.close()
