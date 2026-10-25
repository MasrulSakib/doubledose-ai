
import re
from functools import lru_cache

from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity

from app.models.medicine import Medicine


MIN_BRAND_LENGTH = 3
MIN_MATCH_SCORE = 20.0


DOSAGE_FORMS = {
    "tablet": ("tablet", "tablets"),
    "capsule": ("capsule", "capsules"),
    "syrup": ("syrup", "syrups"),
    "suspension": ("suspension", "suspensions"),
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
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s.+/-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def contains_phrase(text: str, phrase: str) -> bool:
    if not text or not phrase:
        return False

    return bool(
        re.search(
            rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])",
            text,
        )
    )


def extract_strengths(text: str) -> set[str]:
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


def extract_dosage_forms(text: str) -> set[str]:
    normalized = normalize_text(text)
    found_forms = set()

    for form, variants in DOSAGE_FORMS.items():
        if any(contains_phrase(normalized, variant) for variant in variants):
            found_forms.add(form)

    return found_forms


def _evidence_adjustment(
    normalized_ocr: str,
    medicine: Medicine,
) -> float:
    """Adjust ranking using explicitly recognized label details."""
    adjustment = 0.0
    source = normalize_text(medicine.source_display_name or "")

    ocr_forms = extract_dosage_forms(normalized_ocr)
    medicine_forms = extract_dosage_forms(source)

    if ocr_forms and medicine_forms:
        if ocr_forms & medicine_forms:
            adjustment += 15.0
        else:
            adjustment -= 25.0

    ocr_strengths = extract_strengths(normalized_ocr)
    medicine_strengths = extract_strengths(source)

    if ocr_strengths and medicine_strengths:
        if ocr_strengths & medicine_strengths:
            adjustment += 15.0
        else:
            adjustment -= 15.0

    return adjustment


@lru_cache(maxsize=1)
def get_vectorizer():
    from sklearn.feature_extraction.text import TfidfVectorizer

    return TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        lowercase=True,
        sublinear_tf=True,
    )


def match_medicines_tfidf(
    db: Session,
    extracted_text: str,
    limit: int = 10,
) -> list[dict]:
    normalized_ocr = normalize_text(extracted_text)

    if not normalized_ocr:
        return []

    medicines = (
        db.query(Medicine)
        .filter(Medicine.brand_name.isnot(None))
        .all()
    )

    candidates = [
        medicine
        for medicine in medicines
        if medicine.brand_name
        and len(normalize_text(medicine.brand_name)) >= MIN_BRAND_LENGTH
    ]

    if not candidates:
        return []

    brand_names = [
        normalize_text(medicine.brand_name)
        for medicine in candidates
    ]

    vectorizer = get_vectorizer()

    try:
        vectors = vectorizer.fit_transform(brand_names + [normalized_ocr])
    except ValueError:
        return []

    query_vector = vectors[-1]
    medicine_vectors = vectors[:-1]
    scores = cosine_similarity(query_vector, medicine_vectors).flatten()

    ranked_results = []

    for index, medicine in enumerate(candidates):
        similarity = float(scores[index]) * 100.0

        if similarity < MIN_MATCH_SCORE:
            continue

        adjustment = _evidence_adjustment(normalized_ocr, medicine)
        normalized_brand = normalize_text(medicine.brand_name or "")
        brand_bonus = (
            30.0
            if contains_phrase(normalized_ocr, normalized_brand)
            else 0.0
        )

        ranking_score = max(
            0.0,
            min(100.0, similarity + adjustment + brand_bonus),
        )

        ranked_results.append(
            (medicine, similarity, ranking_score)
        )

    ranked_results.sort(
        key=lambda item: (
            item[2],
            item[1],
            len(normalize_text(item[0].brand_name or "")),
        ),
        reverse=True,
    )

    safe_limit = max(1, min(limit, 20))
    results = []
    seen_products = set()

    for medicine, similarity, ranking_score in ranked_results:
        brand = normalize_text(medicine.brand_name or "")
        source = normalize_text(medicine.source_display_name or "")
        form = tuple(sorted(extract_dosage_forms(source)))
        strength = tuple(sorted(extract_strengths(source)))

        product_key = (brand, form, strength)

        if product_key in seen_products:
            continue

        seen_products.add(product_key)

        results.append(
            {
                "medicine_id": medicine.id,
                "brand_name": medicine.brand_name,
                "generic_name": medicine.generic_name,
                "strength": medicine.source_display_name,
                "match_score": round(similarity, 1),
                "ranking_score": round(ranking_score, 1),
                "needs_confirmation": True,
                "matcher": "tfidf",
            }
        )

        if len(results) >= safe_limit:
            break

    return results