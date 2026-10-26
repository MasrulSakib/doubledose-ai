from app.db.session import SessionLocal
from scripts.evaluate_medicine_matchers import LEGACY_CASES
from app.services.semantic_matching_service import match_medicines_semantic

with SessionLocal() as db:
    for query, expected in LEGACY_CASES:
        print(f"\nQuery: {query}")
        print(f"Expected: {expected}")

        results = match_medicines_semantic(
            db=db,
            extracted_text=query,
            limit=3,
        )

        for rank, result in enumerate(results, start=1):
            print(
                f"  {rank}. {result['brand_name']} | "
                f"match={result['match_score']} | "
                f"ranking={result.get('ranking_score')}"
            )