from __future__ import annotations

import logging
import os
import re
import threading
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.medicine import Medicine

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CANDIDATE_LIMIT = 10
MAX_CANDIDATE_LIMIT = 50

_model: Any = None
_model_name_loaded: str | None = None
_cache_lock = threading.RLock()


@dataclass
class MedicineIndex:
    records: list[dict[str, Any]]
    index: Any
    model_name: str


_catalogue_cache: MedicineIndex | None = None


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower()
    value = re.sub(r"[^a-z0-9+./\-\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _get_model() -> Any:
    global _model, _model_name_loaded

    from sentence_transformers import SentenceTransformer

    model_name = (
        os.getenv("SENTENCE_TRANSFORMER_MODEL", DEFAULT_MODEL_NAME).strip()
        or DEFAULT_MODEL_NAME
    )

    with _cache_lock:
        if _model is None or _model_name_loaded != model_name:
            _model = SentenceTransformer(model_name)
            _model_name_loaded = model_name

        return _model


def _medicine_document(medicine: Medicine) -> str:
    fields = [
        medicine.brand_name,
        medicine.generic_name,
        medicine.source_display_name,
        medicine.dosage_form,
        medicine.manufacturer,
    ]

    return " ".join(
        normalized
        for field in fields
        if (normalized := _normalize_text(field))
    )


def _extract_strengths(text: str | None) -> set[str]:
    normalized = _normalize_text(text)

    pattern = (
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:mg|mcg|g|ml|iu|units?)"
        r"(?:\s*/\s*\d+(?:\.\d+)?\s*(?:ml|mg|g))?\b"
    )

    return {
        re.sub(r"\s+", "", match)
        for match in re.findall(pattern, normalized)
    }


def _extract_dosage_forms(text: str | None) -> set[str]:
    normalized = _normalize_text(text)

    aliases = {
        "tablet": ("tablet", "tablets", "tab"),
        "capsule": ("capsule", "capsules", "cap"),
        "syrup": ("syrup",),
        "suspension": ("suspension",),
        "injection": ("injection", "injectable"),
        "infusion": ("infusion",),
        "suppository": ("suppository", "suppositories"),
        "drops": ("drops", "drop"),
        "cream": ("cream",),
        "ointment": ("ointment",),
        "inhaler": ("inhaler",),
    }

    found: set[str] = set()

    for canonical, terms in aliases.items():
        if any(
            re.search(rf"\b{re.escape(term)}\b", normalized)
            for term in terms
        ):
            found.add(canonical)

    return found


def _record_for(medicine: Medicine, document: str) -> dict[str, Any]:
    return {
        "medicine_id": medicine.id,
        "brand_name": medicine.brand_name,
        "generic_name": medicine.generic_name,
        "strength": medicine.source_display_name,
        "dosage_form": medicine.dosage_form,
        "manufacturer": medicine.manufacturer,
        "document": document,
    }


def _build_catalogue_index(
    db: Session,
    model: Any,
) -> MedicineIndex:
    import faiss
    import numpy as np

    medicines = db.query(Medicine).order_by(Medicine.id.asc()).all()

    records: list[dict[str, Any]] = []
    documents: list[str] = []

    for medicine in medicines:
        if not (medicine.brand_name or "").strip():
            continue

        document = _medicine_document(medicine)

        if not document:
            continue

        records.append(_record_for(medicine, document))
        documents.append(document)

    model_name = _model_name_loaded or DEFAULT_MODEL_NAME

    if not documents:
        return MedicineIndex([], faiss.IndexFlatIP(1), model_name)

    vectors = model.encode(
        documents,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=64,
    )

    vectors = np.asarray(vectors, dtype=np.float32)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    return MedicineIndex(records, index, model_name)


def clear_semantic_catalogue_cache() -> None:
    """Clear the in-memory catalogue index after catalogue changes."""
    global _catalogue_cache

    with _cache_lock:
        _catalogue_cache = None


def _get_catalogue_index(
    db: Session,
    model: Any,
) -> MedicineIndex:
    global _catalogue_cache

    model_name = _model_name_loaded or DEFAULT_MODEL_NAME

    with _cache_lock:
        if (
            _catalogue_cache is None
            or _catalogue_cache.model_name != model_name
        ):
            _catalogue_cache = _build_catalogue_index(db, model)

        return _catalogue_cache


def _rerank_score(
    query: str,
    semantic_score: float,
    record: dict[str, Any],
) -> float:
    """Rerank candidates using semantic similarity and medicine evidence."""
    query_normalized = _normalize_text(query)
    brand = _normalize_text(record.get("brand_name"))
    generic = _normalize_text(record.get("generic_name"))
    manufacturer = _normalize_text(record.get("manufacturer"))
    dosage_form = _normalize_text(record.get("dosage_form"))

    score = max(0.0, min(1.0, semantic_score)) * 100
    query_tokens = set(query_normalized.split())

    if brand and re.search(
        rf"(?<![a-z0-9]){re.escape(brand)}(?![a-z0-9])",
        query_normalized,
    ):
        score += 20.0

    if generic:
        candidate_ingredients = {
            ingredient.strip()
            for ingredient in generic.split("+")
            if ingredient.strip()
        }

        all_ingredients_mentioned = (
            bool(candidate_ingredients)
            and all(
                re.search(
                    rf"(?<![a-z0-9]){re.escape(ingredient)}(?![a-z0-9])",
                    query_normalized,
                )
                for ingredient in candidate_ingredients
            )
        )

        if len(candidate_ingredients) == 1:
            ingredient = next(iter(candidate_ingredients))

            if re.search(
                rf"(?<![a-z0-9]){re.escape(ingredient)}(?![a-z0-9])",
                query_normalized,
            ):
                score += 8.0

        elif len(candidate_ingredients) > 1:
            if all_ingredients_mentioned:
                score += 8.0
            else:
                score -= 15.0

    manufacturer_tokens = manufacturer.split()

    if manufacturer:
        manufacturer_matches = (
            manufacturer in query_normalized
            or (
                len(manufacturer_tokens) >= 2
                and manufacturer_tokens[0] in query_tokens
            )
        )

        if manufacturer_matches:
            score += 8.0

    query_strengths = _extract_strengths(query_normalized)
    candidate_strengths = _extract_strengths(record.get("strength"))

    if query_strengths:
        if query_strengths.intersection(candidate_strengths):
            score += 8.0
        else:
            score -= 18.0

    query_forms = _extract_dosage_forms(query_normalized)
    candidate_forms = _extract_dosage_forms(dosage_form)

    if query_forms:
        if query_forms.intersection(candidate_forms):
            score += 6.0
        else:
            score -= 20.0

    return round(max(0.0, min(120.0, score)), 1)


def match_medicines_semantic(
    db: Session,
    extracted_text: str,
    limit: int = DEFAULT_CANDIDATE_LIMIT,
) -> list[dict[str, Any]]:
    """Retrieve and rerank semantic medicine candidates for confirmation."""
    import numpy as np

    query = _normalize_text(extracted_text)

    if len(query) < 2:
        return []

    safe_limit = max(1, min(int(limit), MAX_CANDIDATE_LIMIT))

    try:
        model = _get_model()
        catalogue = _get_catalogue_index(db, model)

        if not catalogue.records:
            return []

        query_vector = model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        query_vector = np.asarray(query_vector, dtype=np.float32)

        candidate_count = min(
            max(safe_limit * 30, 100),
            len(catalogue.records),
        )

        similarities, indices = catalogue.index.search(
            query_vector,
            candidate_count,
        )

    except Exception:
        logger.exception("Semantic medicine matching failed.")
        return []

    candidates: list[dict[str, Any]] = []

    for similarity, position in zip(similarities[0], indices[0]):
        if position < 0 or position >= len(catalogue.records):
            continue

        record = catalogue.records[int(position)]
        semantic_similarity = float(similarity)

        semantic_score = round(
            max(0.0, min(1.0, semantic_similarity)) * 100,
            1,
        )

        ranking_score = _rerank_score(
            query,
            semantic_similarity,
            record,
        )

        candidates.append({
            "medicine_id": record["medicine_id"],
            "brand_name": record["brand_name"],
            "generic_name": record["generic_name"],
            "strength": record["strength"],
            "match_score": semantic_score,
            "ranking_score": ranking_score,
            "needs_confirmation": True,
            "matcher": "semantic_faiss",
        })

    candidates.sort(
        key=lambda item: (
            item["ranking_score"],
            item["match_score"],
        ),
        reverse=True,
    )

    return candidates[:safe_limit]