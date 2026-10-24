"""Measure how much of the medicine catalogue has usable ingredient data.

Usage (from backend/): python -m scripts.report_data_coverage
"""

import argparse
import json
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.medicine import ActiveIngredient, Medicine, MedicineIngredient
from app.services.ingredient_normalizer import canonical_ingredient_key

BASE_DIR = Path(__file__).resolve().parents[1]


def pct(part: int, whole: int) -> float:
    return round(100 * part / whole, 2) if whole else 0.0


def build_report() -> dict:
    with SessionLocal() as db:
        total = db.scalar(select(func.count(Medicine.id)))
        mapped_ids = set(db.scalars(select(MedicineIngredient.medicine_id).distinct()))

        unmapped = Counter()
        for medicine in db.scalars(select(Medicine)):
            if medicine.id in mapped_ids:
                continue
            generic = (medicine.generic_name or "").strip()
            if not generic:
                unmapped["empty_generic_name"] += 1
            elif "[" in generic or "]" in generic:
                unmapped["bracketed_generic_left_unmapped"] += 1
            else:
                unmapped["other_incl_herbal"] += 1

        links = db.execute(
            select(
                MedicineIngredient.medicine_id,
                MedicineIngredient.amount,
                ActiveIngredient.id,
                ActiveIngredient.name,
            ).join(ActiveIngredient, ActiveIngredient.id == MedicineIngredient.ingredient_id)
        ).all()

    per_medicine = Counter(row.medicine_id for row in links)
    by_exact, by_key = defaultdict(set), defaultdict(set)
    for row in links:
        by_exact[row.id].add(row.medicine_id)
        by_key[canonical_ingredient_key(row.name)].add(row.medicine_id)

    exact_pairs = sum(comb(len(v), 2) for v in by_exact.values())
    moiety_pairs = sum(comb(len(v), 2) for v in by_key.values())

    return {
        "medicines_total": total,
        "medicines_with_ingredient_data": len(mapped_ids),
        "ingredient_coverage_percent": pct(len(mapped_ids), total),
        "medicines_without_ingredient_data": total - len(mapped_ids),
        "why_unmapped": dict(unmapped),
        "ingredient_links": len(links),
        "links_with_amount": sum(1 for row in links if row.amount is not None),
        "distinct_ingredient_rows": len(by_exact),
        "distinct_active_moieties_after_normalisation": len(by_key),
        "ingredients_per_medicine": dict(sorted(Counter(per_medicine.values()).items())),
        "ingredient_sharing_product_pairs_exact_names": exact_pairs,
        "ingredient_sharing_product_pairs_normalised": moiety_pairs,
        "pairs_missed_by_exact_names_percent": pct(moiety_pairs - exact_pairs, moiety_pairs),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingredient-mapping coverage report.")
    parser.add_argument("--out-dir", default=str(BASE_DIR / "evaluation" / "results"))
    args = parser.parse_args()

    report = build_report()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "data_coverage.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
