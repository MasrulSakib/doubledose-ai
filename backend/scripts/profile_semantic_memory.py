
import gc
import time
import tracemalloc

import psutil

from app.services.semantic_matching_service import (
    _build_catalogue_index,
    _get_model,
)
from app.db.session import SessionLocal


def report_memory(label: str) -> None:
    process = psutil.Process()
    memory_mb = process.memory_info().rss / (1024 * 1024)

    print(f"{label}: RSS memory = {memory_mb:.2f} MiB", flush=True)


def main() -> None:
    tracemalloc.start()
    report_memory("Initial")

    print("\nLoading ONNX model...", flush=True)
    model = _get_model()
    report_memory("After model loading")

    print("\nBuilding medicine catalogue index...", flush=True)
    db = SessionLocal()

    try:
        start = time.perf_counter()
        index = _build_catalogue_index(db, model)
        elapsed = time.perf_counter() - start

        report_memory("After catalogue indexing")
        print(f"Index build time: {elapsed:.2f} seconds", flush=True)
        print(f"Indexed medicine records: {len(index.records)}", flush=True)
        print(f"FAISS vectors: {index.index.ntotal}", flush=True)

    finally:
        db.close()

    current, peak = tracemalloc.get_traced_memory()
    print(f"Python traced current: {current / (1024 * 1024):.2f} MiB")
    print(f"Python traced peak: {peak / (1024 * 1024):.2f} MiB")

    gc.collect()
    report_memory("After garbage collection")


if __name__ == "__main__":
    main()
