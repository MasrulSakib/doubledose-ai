from __future__ import annotations

import json
import logging
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from app.models.medicine import Medicine

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CANDIDATE_LIMIT = 10
MAX_CANDIDATE_LIMIT = 50
ENCODE_BATCH_SIZE = 16
MAX_SEQUENCE_LENGTH = 256
EMBEDDING_DIMENSION = 384

# semantic_matching_service.py is located at backend/app/services/.
DEFAULT_INDEX_DIR = Path(__file__).resolve().parents[2] / "data" / "semantic"

_model: Any = None
_model_name_loaded: str | None = None
_tokenizer: Any = None
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
    """Load the quantized ONNX model and lightweight tokenizer."""
    global _model, _model_name_loaded, _tokenizer

    import onnxruntime as ort
    from huggingface_hub import hf_hub_download
    from tokenizers import Tokenizer

    model_name = (
        os.getenv("SENTENCE_TRANSFORMER_MODEL", DEFAULT_MODEL_NAME).strip()
        or DEFAULT_MODEL_NAME
    )

    with _cache_lock:
        if _model is not None and _model_name_loaded == model_name:
            return _model

        logger.info("Loading direct ONNX inference session: %s", model_name)

        model_path = hf_hub_download(
            repo_id=model_name,
            filename="onnx/model_quint8_avx2.onnx",
        )
        tokenizer_path = hf_hub_download(
            repo_id=model_name,
            filename="tokenizer.json",
        )

        tokenizer = Tokenizer.from_file(tokenizer_path)
        tokenizer.enable_truncation(max_length=MAX_SEQUENCE_LENGTH)

        pad_token_id = tokenizer.token_to_id("[PAD]")
        if pad_token_id is None:
            raise RuntimeError("The tokenizer has no [PAD] token.")

        tokenizer.enable_padding(
            pad_id=pad_token_id,
            pad_token="[PAD]",
        )

        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.graph_optimization_level = (
            ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        )

        session = ort.InferenceSession(
            model_path,
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )

        input_names = {item.name for item in session.get_inputs()}
        required_inputs = {
            "input_ids",
            "attention_mask",
            "token_type_ids",
        }

        if not required_inputs.issubset(input_names):
            raise RuntimeError(
                f"Unexpected ONNX inputs: {sorted(input_names)}"
            )

        output_names = {item.name for item in session.get_outputs()}
        if "last_hidden_state" not in output_names:
            raise RuntimeError(
                f"Unexpected ONNX outputs: {sorted(output_names)}"
            )

        _model = session
        _tokenizer = tokenizer
        _model_name_loaded = model_name

        logger.info("Direct ONNX model and tokenizer loaded successfully")
        return _model


def _get_tokenizer() -> Any:
    _get_model()
    return _tokenizer


def _encode_texts(
    texts: list[str],
    batch_size: int = ENCODE_BATCH_SIZE,
) -> np.ndarray:
    """Create normalized sentence embeddings using direct ONNX inference."""
    if not texts:
        return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)

    model = _get_model()
    tokenizer = _get_tokenizer()
    batch_size = max(1, batch_size)
    embeddings: list[np.ndarray] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        encoded = tokenizer.encode_batch(batch)

        input_ids = np.asarray(
            [item.ids for item in encoded], dtype=np.int64
        )
        attention_mask = np.asarray(
            [item.attention_mask for item in encoded], dtype=np.int64
        )
        token_type_ids = np.asarray(
            [item.type_ids for item in encoded], dtype=np.int64
        )

        input_feed = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
        }

        token_embeddings = model.run(
            ["last_hidden_state"], input_feed
        )[0]

        mask = attention_mask[:, :, np.newaxis].astype(
            np.float32, copy=False
        )
        summed = np.sum(token_embeddings * mask, axis=1)
        counts = np.maximum(mask.sum(axis=1), 1e-9)
        sentence_embeddings = summed / counts

        norms = np.linalg.norm(
            sentence_embeddings, axis=1, keepdims=True
        )
        sentence_embeddings /= np.maximum(norms, 1e-12)

        embeddings.append(
            np.asarray(sentence_embeddings, dtype=np.float32)
        )

        del encoded, input_feed, input_ids, attention_mask, token_type_ids
        del token_embeddings, mask, summed, counts
        del sentence_embeddings, norms

    return np.concatenate(embeddings, axis=0)


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
    """Extract strengths and concentration numerators from text."""
    normalized = _normalize_text(text)

    pattern = (
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:mg|mcg|g|ml|iu|units?)"
        r"(?:\s*/\s*\d+(?:\.\d+)?\s*(?:ml|mg|g))?\b"
    )

    strengths: set[str] = set()

    for match in re.findall(pattern, normalized):
        compact = re.sub(r"\s+", "", match)
        strengths.add(compact)

        # 120 mg/5 ml can match a query specifying 120 mg.
        # The complete concentration is retained as a separate value.
        if "/" in compact:
            strengths.add(compact.split("/", maxsplit=1)[0])

    return strengths


def _extract_dosage_forms(text: str | None) -> set[str]:
    """Detect dosage forms in normal text and concatenated catalogue slugs."""
    normalized = _normalize_text(text)

    aliases = {
        "tablet": ("tablets", "tablet", "tabs", "tab"),
        "capsule": ("capsules", "capsule", "caps", "cap"),
        "syrup": ("syrup",),
        "suspension": ("suspension",),
        "injection": ("injection", "injectable", "injections"),
        "infusion": ("infusion",),
        "suppository": ("suppositories", "suppository"),
        "drops": ("drops", "drop"),
        "cream": ("cream",),
        "ointment": ("ointment",),
        "inhaler": ("inhaler",),
    }

    found: set[str] = set()

    for canonical, terms in aliases.items():
        for term in terms:
            # Word boundaries handle normal text.
            if re.search(rf"\b{re.escape(term)}\b", normalized):
                found.add(canonical)
                break

            # Slugs may concatenate the brand and dosage form:
            # napasyrup120-mg5-ml, napasuppository125-mg.
            if re.search(
                rf"(?<=[a-z]){re.escape(term)}(?=[0-9\s./-]|$)",
                normalized,
            ):
                found.add(canonical)
                break

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


def _load_catalogue_index(model_name: str) -> MedicineIndex:
    """Load the prebuilt FAISS index and its matching metadata."""
    import faiss

    index_dir = Path(
        os.getenv("SEMANTIC_INDEX_DIR", str(DEFAULT_INDEX_DIR))
    ).expanduser()

    index_path = index_dir / "medicines.faiss"
    records_path = index_dir / "medicines.json"

    missing_files = [
        str(path)
        for path in (index_path, records_path)
        if not path.is_file()
    ]

    if missing_files:
        raise FileNotFoundError(
            "Semantic index artifacts are missing: "
            + ", ".join(missing_files)
            + ". Generate the artifacts with "
            "`python -m scripts.build_semantic_index` "
            "and include them in the deployment."
        )

    logger.info("Loading saved semantic index from %s", index_dir)

    index = faiss.read_index(str(index_path))

    with records_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise RuntimeError(
            f"Invalid semantic metadata format: {records_path}"
        )

    if index.d != EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Semantic index dimension mismatch: expected "
            f"{EMBEDDING_DIMENSION}, got {index.d}."
        )

    if index.ntotal != len(records):
        raise RuntimeError(
            f"Semantic index/metadata mismatch: index contains "
            f"{index.ntotal} vectors, but metadata contains "
            f"{len(records)} records."
        )

    required_fields = {
        "medicine_id",
        "brand_name",
        "generic_name",
        "strength",
        "dosage_form",
        "manufacturer",
        "document",
    }

    for position, record in enumerate(records):
        if not isinstance(record, dict):
            raise RuntimeError(
                f"Invalid metadata record at position {position}."
            )

        missing_fields = required_fields.difference(record)

        if missing_fields:
            raise RuntimeError(
                f"Metadata record {position} is missing fields: "
                f"{sorted(missing_fields)}"
            )

    logger.info(
        "Saved semantic index loaded: %s medicine records",
        index.ntotal,
    )

    return MedicineIndex(
        records=records,
        index=index,
        model_name=model_name,
    )


def clear_semantic_catalogue_cache() -> None:
    """Clear the in-memory catalogue index after catalogue changes."""
    global _catalogue_cache

    with _cache_lock:
        _catalogue_cache = None


def _get_catalogue_index(
    db: Session,
    model: Any = None,
) -> MedicineIndex:
    """Return the cached index, loading saved artifacts when needed."""
    global _catalogue_cache

    model_name = _model_name_loaded or DEFAULT_MODEL_NAME

    with _cache_lock:
        if (
            _catalogue_cache is None
            or _catalogue_cache.model_name != model_name
        ):
            # Load prebuilt artifacts; never rebuild embeddings at runtime.
            _catalogue_cache = _load_catalogue_index(model_name)

        return _catalogue_cache




def _rerank_score(
    query: str,
    semantic_score: float,
    record: dict[str, Any],
) -> float:
    """Rerank candidates while prioritizing strength and dosage-form compatibility."""
    query_normalized = _normalize_text(query)
    brand = _normalize_text(record.get("brand_name"))
    generic = _normalize_text(record.get("generic_name"))
    manufacturer = _normalize_text(record.get("manufacturer"))

    candidate_description = " ".join(
        str(record.get(field) or "")
        for field in ("dosage_form", "strength", "document")
    )
    candidate_description = _normalize_text(candidate_description)

    score = max(0.0, min(1.0, semantic_score)) * 100
    query_tokens = set(query_normalized.split())

    # Brand and ingredient evidence.
    if brand and re.search(
        rf"(?<![a-z0-9]){re.escape(brand)}(?![a-z0-9])",
        query_normalized,
    ):
        score += 20.0

    if generic:
        ingredients = {
            ingredient.strip()
            for ingredient in generic.split("+")
            if ingredient.strip()
        }

        mentioned = {
            ingredient
            for ingredient in ingredients
            if re.search(
                rf"(?<![a-z0-9]){re.escape(ingredient)}(?![a-z0-9])",
                query_normalized,
            )
        }

        if len(ingredients) == 1 and mentioned:
            score += 8.0
        elif len(ingredients) > 1:
            score += 8.0 if mentioned == ingredients else -15.0

    manufacturer_tokens = manufacturer.split()
    if manufacturer and (
        manufacturer in query_normalized
        or (
            len(manufacturer_tokens) >= 2
            and manufacturer_tokens[0] in query_tokens
        )
    ):
        score += 8.0

    # Strength compatibility.
    query_strengths = _extract_strengths(query_normalized)
    candidate_strengths = _extract_strengths(candidate_description)

    if query_strengths:
        if query_strengths.intersection(candidate_strengths):
            score += 8.0
        else:
            score -= 35.0

    # Dosage-form compatibility.
    query_forms = _extract_dosage_forms(query_normalized)
    candidate_forms = _extract_dosage_forms(candidate_description)

    if query_forms:
        if query_forms.intersection(candidate_forms):
            score += 6.0
        else:
            score -= 35.0

    return round(max(0.0, min(120.0, score)), 1)


def match_medicines_semantic(
    db: Session,
    extracted_text: str,
    limit: int = DEFAULT_CANDIDATE_LIMIT,
) -> list[dict[str, Any]]:
    """Retrieve and rerank semantic medicine candidates for confirmation."""
    query = _normalize_text(extracted_text)

    if len(query) < 2:
        return []

    safe_limit = max(1, min(int(limit), MAX_CANDIDATE_LIMIT))

    try:
        _get_model()
        catalogue = _get_catalogue_index(db)

        if not catalogue.records:
            return []

        query_vector = _encode_texts([query], batch_size=1)

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