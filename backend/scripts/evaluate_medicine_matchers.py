
import json
from pathlib import Path

import mlflow
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.medicine import Medicine
from app.services.ocr_matching_service import match_medicines_from_ocr
from app.services.tfidf_matching_service import match_medicines_tfidf


# Small initial evaluation set. Expand with verified label examples.
EVALUATION_CASES = [
    {
        "text": "A-Cof Syrup Dextromethorphan Pseudoephedrine Triprolidine",
        "expected_brand": "A-Cof",
    },
    {
        "text": "E-Cof syrup Pseudoephedrine Guaiphenasine Triprolidine",
        "expected_brand": "E-Cof",
    },
    {
        "text": "A-Cold syrup Bromhexine Hydrochloride",
        "expected_brand": "A-Cold",
    },
    {
        "text": "A-Clox capsule 500 mg Cloxacillin Sodium",
        "expected_brand": "A-Clox",
    },
    {
        "text": "Syrup Zinc Zinc Sulfate Monohydrate",
        "expected_brand": "Syrup Zinc",
    },
]


def calculate_metrics(
    db: Session,
    matcher_name: str,
    matcher_function,
) -> dict:
    top1_correct = 0
    top3_correct = 0
    reciprocal_ranks = []

    for case in EVALUATION_CASES:
        results = matcher_function(
            db=db,
            extracted_text=case["text"],
            limit=3,
        )

        expected = case["expected_brand"].casefold()
        ranked_brands = [
            item["brand_name"].casefold()
            for item in results
        ]

        if ranked_brands and ranked_brands[0] == expected:
            top1_correct += 1

        if expected in ranked_brands[:3]:
            top3_correct += 1

        rank = next(
            (
                index
                for index, brand in enumerate(ranked_brands, start=1)
                if brand == expected
            ),
            None,
        )
        reciprocal_ranks.append(1 / rank if rank else 0)

    total = len(EVALUATION_CASES)

    metrics = {
        "top1_accuracy": top1_correct / total,
        "top3_accuracy": top3_correct / total,
        "mean_reciprocal_rank": sum(reciprocal_ranks) / total,
        "evaluation_cases": total,
    }

    print(f"\n{matcher_name}")
    print(json.dumps(metrics, indent=2))

    return metrics


def main() -> None:
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("doubledose-medicine-matching")

    db = SessionLocal()

    try:
        with mlflow.start_run(run_name="rapidfuzz-vs-tfidf"):
            rapidfuzz_metrics = calculate_metrics(
                db,
                "RapidFuzz",
                match_medicines_from_ocr,
            )

            tfidf_metrics = calculate_metrics(
                db,
                "TF-IDF",
                match_medicines_tfidf,
            )

            mlflow.log_param("dataset", "initial_manual_evaluation")
            mlflow.log_param("matcher_limit", 3)
            mlflow.log_param("evaluation_cases", len(EVALUATION_CASES))

            for name, value in rapidfuzz_metrics.items():
                mlflow.log_metric(f"rapidfuzz_{name}", value)

            for name, value in tfidf_metrics.items():
                mlflow.log_metric(f"tfidf_{name}", value)

            print("\nMLflow run recorded successfully.")
            print("Tracking directory: backend/mlruns")

    finally:
        db.close()


if __name__ == "__main__":
    main()
