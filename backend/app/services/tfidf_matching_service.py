import re
from functools import lru_cache
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity
from app.models.medicine import Medicine


MIN_BRAND_LENGTH = 3
MIN_MATCH_SCORE = 0.20


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s.+-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


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
        brand_vectors = vectorizer.fit_transform(brand_names + [normalized_ocr])
    except ValueError:
        return []

    query_vector = brand_vectors[-1]
    medicine_vectors = brand_vectors[:-1]

    scores = cosine_similarity(query_vector, medicine_vectors).flatten()

    ranked_indices = sorted(
        range(len(candidates)),
        key=lambda index: float(scores[index]),
        reverse=True,
    )

    results = []

    for index in ranked_indices:
        score = float(scores[index])

        if score < MIN_MATCH_SCORE:
            continue

        medicine = candidates[index]

        results.append(
            {
                "medicine_id": medicine.id,
                "brand_name": medicine.brand_name,
                "generic_name": medicine.generic_name,
                "strength": medicine.source_display_name,
                "match_score": round(score * 100, 1),
                "needs_confirmation": True,
                "matcher": "tfidf",
            }
        )

        if len(results) >= max(1, min(limit, 20)):
            break

    return results
