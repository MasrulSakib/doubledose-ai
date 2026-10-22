import re

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.models.medicine import Medicine


MIN_BRAND_LENGTH = 4
MIN_MATCH_SCORE = 45.0
MAX_RESULTS = 20

# Common dosage forms found in medicine names and database slugs.
DOSAGE_FORMS = {
    "tablet": ("tablet", "tablets"),
    "capsule": ("capsule", "capsules"),
    "syrup": ("syrup", "syrups"),
    "suspension": ("suspension", "suspensions"),
    "suppository": ("suppository", "suppositories"),
    "injection": ("injection", "injections"),
    "infusion": ("infusion", "infusions"),
    "drops": ("drop", "drops"),
    "cream": ("cream", "creams"),
    "ointment": ("ointment", "ointments"),
    "gel": ("gel", "gels"),
    "solution": ("solution", "solutions"),
    "inhaler": ("inhaler", "inhalers"),
}


def normalize_text(text: str) -> str:
    """Normalize OCR text and medicine names for matching."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s.+/-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    """Check whether a normalized phrase occurs as complete words."""
    if not text or not phrase:
        return False

    return bool(
        re.search(
            rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])",
            text,
        )
    )


def _extract_strengths(text: str) -> set[str]:
    """Extract normalized numerical strengths from text."""
    normalized = normalize_text(text)

    pattern = re.compile(
        r"(?<!\d)(\d+(?:\.\d+)?)\s*(mg|mcg|ug|g|ml|iu|%)\b",
        re.IGNORECASE,
    )

    strengths = set()

    for value, unit in pattern.findall(normalized):
        number = float(value)
        number_text = (
            str(int(number)) if number.is_integer() else str(number)
        )

        normalized_unit = unit.lower()

        if normalized_unit == "ug":
            normalized_unit = "mcg"

        strengths.add(f"{number_text}{normalized_unit}")

    return strengths


def _extract_dosage_forms(text: str) -> set[str]:
    """Identify dosage forms mentioned in text or database slugs."""
    normalized = normalize_text(text)
    found_forms = set()

    for form, variants in DOSAGE_FORMS.items():
        for variant in variants:
            if _contains_phrase(normalized, variant):
                found_forms.add(form)
                break

    return found_forms


def _extract_generic_ingredients(generic_name: str | None) -> set[str]:
    """Extract ingredient names from the database generic-name field."""
    if not generic_name:
        return set()

    normalized = normalize_text(generic_name)

    # The generic_name field typically uses '+' between ingredients.
    ingredients = re.split(r"\s*\+\s*", normalized)

    return {
        re.sub(r"\s+", " ", ingredient).strip()
        for ingredient in ingredients
        if ingredient.strip()
    }


def _ingredient_match_score(
    normalized_ocr: str,
    generic_name: str | None,
) -> float:
    """
    Score ingredient evidence.

    Give credit for ingredients that appear in the OCR, while penalizing
    candidates that omit other clearly recognized active ingredients.
    """
    ingredients = _extract_generic_ingredients(generic_name)

    if not ingredients:
        return 0.0

    matched = sum(
        1
        for ingredient in ingredients
        if _contains_phrase(normalized_ocr, ingredient)
    )

    score = (matched / len(ingredients)) * 20.0

    # If OCR clearly identifies multiple ingredients, penalize candidates
    # that explain only a subset of them.
    if matched:
        recognized_ingredients = {
            ingredient
            for ingredient in (
                "paracetamol",
                "acetaminophen",
                "caffeine",
                "ibuprofen",
                "aspirin",
                "cetirizine",
                "loratadine",
                "omeprazole",
                "amoxicillin",
                "metformin",
            )
            if _contains_phrase(normalized_ocr, ingredient)
        }

        candidate_aliases = set(ingredients)

        # Treat paracetamol and acetaminophen as aliases.
        if "paracetamol" in candidate_aliases:
            candidate_aliases.add("acetaminophen")
        if "acetaminophen" in candidate_aliases:
            candidate_aliases.add("paracetamol")

        missing_recognized = recognized_ingredients - candidate_aliases

        if missing_recognized:
            score -= min(10.0, len(missing_recognized) * 5.0)

    return max(0.0, score)


def _strength_match_score(
    normalized_ocr: str,
    source_display_name: str | None,
) -> float:
    """
    Compare the strengths visible in OCR with the database entry.

    The score rewards candidates that explain all detected strengths,
    rather than candidates that match just one of several strengths.
    """
    if not source_display_name:
        return 0.0

    ocr_strengths = _extract_strengths(normalized_ocr)
    medicine_strengths = _extract_strengths(source_display_name)

    if not ocr_strengths or not medicine_strengths:
        return 0.0

    matching_strengths = ocr_strengths & medicine_strengths

    if not matching_strengths:
        return 0.0

    return 15.0 * len(matching_strengths) / len(ocr_strengths)


def _dosage_form_score(
    normalized_ocr: str,
    source_display_name: str | None,
) -> float:
    """Reward compatible dosage forms and penalize conflicting forms."""
    if not source_display_name:
        return 0.0

    ocr_forms = _extract_dosage_forms(normalized_ocr)
    medicine_forms = _extract_dosage_forms(source_display_name)

    if not ocr_forms or not medicine_forms:
        return 0.0

    if ocr_forms & medicine_forms:
        return 5.0

    return -10.0

def _brand_match_score(
    normalized_ocr: str,
    brand_name: str,
) -> float:
    """Score brand evidence conservatively when OCR text is noisy."""
    normalized_brand = normalize_text(brand_name)

    if not normalized_brand:
        return 0.0

    # An exact brand phrase is stronger evidence than fuzzy similarity.
    if _contains_phrase(normalized_ocr, normalized_brand):
        return 60.0

    words = normalized_ocr.split()
    brand_compact = normalized_brand.replace(" ", "")
    brand_length = len(brand_compact)

    if brand_length < MIN_BRAND_LENGTH:
        return 0.0

    best_score = 0.0

    # Match individual OCR tokens and short contiguous fragments.
    for size in range(1, min(3, len(words)) + 1):
        for start in range(len(words) - size + 1):
            fragment = " ".join(words[start : start + size])
            fragment_compact = fragment.replace(" ", "")
            fragment_length = len(fragment_compact)

            # Ignore fragments that are too short to identify a brand.
            if fragment_length < max(MIN_BRAND_LENGTH, brand_length - 2):
                continue

            # Reject fragments whose length differs substantially.
            length_ratio = min(fragment_length, brand_length) / max(
                fragment_length,
                brand_length,
            )
            if length_ratio < 0.75:
                continue

            similarity = float(fuzz.ratio(brand_compact, fragment_compact))

            # Require stronger similarity for fuzzy brand evidence.
            if similarity < 75:
                continue

            best_score = max(best_score, similarity * 0.40)

    return best_score


def _score_medicine(
    normalized_ocr: str,
    medicine: Medicine,
) -> float:
    """Combine brand, ingredient, strength, and dosage-form evidence."""
    brand_name = medicine.brand_name or ""
    source_display_name = medicine.source_display_name or ""

    score = _brand_match_score(normalized_ocr, brand_name)

    score += _ingredient_match_score(
        normalized_ocr,
        medicine.generic_name,
    )

    score += _strength_match_score(
        normalized_ocr,
        source_display_name,
    )

    score += _dosage_form_score(
        normalized_ocr,
        source_display_name,
    )

    # A longer, more specific brand should outrank its shorter base brand
    # when both are otherwise supported by the OCR text.
    if _contains_phrase(normalized_ocr, normalize_text(brand_name)):
        score += min(len(normalize_text(brand_name).split()) - 1, 2) * 3.0

    return round(max(0.0, min(100.0, score)), 1)


def match_medicines_from_ocr(
    db: Session,
    extracted_text: str,
    limit: int = 10,
) -> list[dict]:
    """
    Return ranked medicine candidates from OCR text.

    Scores represent combined textual evidence, not probabilities.
    Every OCR-based result requires confirmation.
    """
    normalized_ocr = normalize_text(extracted_text)

    if not normalized_ocr:
        return []

    medicines = (
        db.query(Medicine)
        .filter(Medicine.brand_name.isnot(None))
        .all()
    )

    if not medicines:
        return []

    ranked_results = []

    for medicine in medicines:
        brand_name = medicine.brand_name or ""

        if len(normalize_text(brand_name).replace(" ", "")) < MIN_BRAND_LENGTH:
            continue

        score = _score_medicine(normalized_ocr, medicine)

        if score < MIN_MATCH_SCORE:
            continue

        ranked_results.append((medicine, score))

    # Higher evidence scores come first. Use a specific brand as a
    # tie-breaker when candidates have equal scores.
    ranked_results.sort(
        key=lambda item: (
            item[1],
            len(normalize_text(item[0].brand_name or "").split()),
            len(normalize_text(item[0].brand_name or "")),
        ),
        reverse=True,
    )

    safe_limit = max(1, min(limit, MAX_RESULTS))

    return [
        {
            "medicine_id": medicine.id,
            "brand_name": medicine.brand_name,
            "generic_name": medicine.generic_name,
            "strength": medicine.source_display_name,
            "match_score": score,
            "needs_confirmation": True,
        }
        for medicine, score in ranked_results[:safe_limit]
    ]