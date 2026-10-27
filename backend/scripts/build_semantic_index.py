
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import faiss
import numpy as np

from app.db.session import SessionLocal
from app.models.medicine import Medicine
from app.services.semantic_matching_service import (
    ENCODE_BATCH_SIZE,
    _encode_texts,
    _medicine_document,
    _record_for,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "semantic"
INDEX_PATH = OUTPUT_DIR / "medicines.faiss"
RECORDS_PATH = OUTPUT_DIR / "medicines.json"


def main() -> None:
    started = time.perf_counter()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Loading medicine records from the database...")
    db = SessionLocal()

    try:
        medicines = db.query(Medicine).order_by(Medicine.id.asc()).all()

        # Copy the needed fields into plain dictionaries before closing
        # the database session. Embedding generation needs no DB connection.
        snapshots = [
            {
                "medicine_id": medicine.id,
                "brand_name": medicine.brand_name,
                "generic_name": medicine.generic_name,
                "source_display_name": medicine.source_display_name,
                "dosage_form": medicine.dosage_form,
                "manufacturer": medicine.manufacturer,
            }
            for medicine in medicines
            if (medicine.brand_name or "").strip()
        ]
    finally:
        db.close()

    del medicines
    logger.info("Loaded %s medicine records.", len(snapshots))

    records: list[dict] = []
    documents: list[str] = []

    for item in snapshots:
        # Build the same document used by the semantic matching service.
        document = " ".join(
            str(value)
            for value in (
                item["brand_name"],
                item["generic_name"],
                item["source_display_name"],
                item["dosage_form"],
                item["manufacturer"],
            )
            if value
        )

        # Reuse the production normalization and record formatting.
        class MedicineSnapshot:
            pass

        medicine = MedicineSnapshot()
        medicine.id = item["medicine_id"]
        medicine.brand_name = item["brand_name"]
        medicine.generic_name = item["generic_name"]
        medicine.source_display_name = item["source_display_name"]
        medicine.dosage_form = item["dosage_form"]
        medicine.manufacturer = item["manufacturer"]

        document = _medicine_document(medicine)

        if document:
            documents.append(document)
            records.append(_record_for(medicine, document))

    del snapshots

    if not documents:
        raise RuntimeError("No valid medicine documents were found.")

    logger.info("Encoding %s medicine documents...", len(documents))
    vectors = np.empty((len(documents), 384), dtype=np.float32)

    for start in range(0, len(documents), ENCODE_BATCH_SIZE):
        end = min(start + ENCODE_BATCH_SIZE, len(documents))
        vectors[start:end] = _encode_texts(
            documents[start:end],
            batch_size=ENCODE_BATCH_SIZE,
        )

        if end % 512 == 0 or end == len(documents):
            logger.info("Encoded %s / %s", end, len(documents))

    logger.info("Creating and saving the FAISS index...")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    # Write temporary files first so incomplete builds do not replace
    # the existing usable artifacts.
    index_temp = INDEX_PATH.with_suffix(".faiss.tmp")
    records_temp = RECORDS_PATH.with_suffix(".json.tmp")

    faiss.write_index(index, str(index_temp))

    with records_temp.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, separators=(",", ":"))

    index_temp.replace(INDEX_PATH)
    records_temp.replace(RECORDS_PATH)

    logger.info("Index saved: %s", INDEX_PATH)
    logger.info("Records saved: %s", RECORDS_PATH)
    logger.info("Indexed records: %s", index.ntotal)
    logger.info("FAISS index size: %.2f MiB", INDEX_PATH.stat().st_size / 1048576)
    logger.info("Metadata size: %.2f MiB", RECORDS_PATH.stat().st_size / 1048576)
    logger.info("Total build time: %.1f seconds", time.perf_counter() - started)


if __name__ == "__main__":
    main()
