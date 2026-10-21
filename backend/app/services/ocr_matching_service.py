
import re

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.models.medicine import Medicine


MIN_BRAND_LENGTH = 5
MIN_MATCH_SCORE = 65.0


def normalize_text(text: str) -> str:
    """Normalize OCR text and medicine names for matching."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s.+-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def match_medicines_from_ocr(
    db: Session,
    extracted_text: str,
    limit: int = 10,
) -> list[dict]:
    """
    Return likely medicine candidates from OCR text.

    Matching scores measure textual similarity, not the probability
    of correct identification. Every candidate requires confirmation.
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

    # Normalize brand names once for this request.
    choices = {
        medicine.id: normalize_text(medicine.brand_name)
        for medicine in medicines
        if medicine.brand_name
    }

    if not choices:
        return []

    # Prepare OCR fragments so names can be found among other text.
    words = normalized_ocr.split()
    fragments = {normalized_ocr}

    for size in (1, 2, 3, 4, 5):
        for start in range(len(words) - size + 1):
            fragment = " ".join(words[start : start + size])

            if len(fragment.replace(" ", "")) >= MIN_BRAND_LENGTH:
                fragments.add(fragment)

    # Exact normalized brand-name matches are preferred.
    padded_ocr = f" {normalized_ocr} "
    best_scores: dict[int, float] = {}

    for medicine_id, brand_name in choices.items():
        if len(brand_name.replace(" ", "")) < MIN_BRAND_LENGTH:
            continue

        # A complete brand name appearing in OCR text is a strong
        # textual match, but still needs human confirmation.
        if f" {brand_name} " in padded_ocr:
            best_scores[medicine_id] = 100.0
            continue

        best_score = 0.0

        for fragment in fragments:
            # Avoid comparing a longer brand against a much shorter
            # fragment, which can produce misleading similarity scores.
            fragment_length = len(fragment.replace(" ", ""))
            brand_length = len(brand_name.replace(" ", ""))

            if fragment_length < MIN_BRAND_LENGTH:
                continue

            if min(fragment_length, brand_length) / max(
                fragment_length, brand_length
            ) < 0.6:
                continue

            score = fuzz.ratio(brand_name, fragment)
            best_score = max(best_score, float(score))

        if best_score >= MIN_MATCH_SCORE:
            best_scores[medicine_id] = round(best_score, 1)

    ranked_ids = sorted(
        best_scores,
        key=lambda medicine_id: best_scores[medicine_id],
        reverse=True,
    )[: max(1, min(limit, 20))]

    medicines_by_id = {
        medicine.id: medicine for medicine in medicines
    }

    results = []

    for medicine_id in ranked_ids:
        medicine = medicines_by_id[medicine_id]

        results.append(
            {
                "medicine_id": medicine.id,
                "brand_name": medicine.brand_name,
                "generic_name": medicine.generic_name,
                "strength": medicine.source_display_name,
                "match_score": best_scores[medicine_id],
                "needs_confirmation": True,
            }
        )

    return results
