
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.medicine import ActiveIngredient, Medicine, MedicineIngredient


SOURCE_NAME = "Hugging Face all-Bangladeshi-medicines"
SOURCE_URL = (
    "https://huggingface.co/datasets/"
    "Mahadih534/all-Bangladeshi-medicines"
)
SOURCE_PREFIX = "BDDrugBank ID:"
BATCH_SIZE = 500

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "data" / "medicine.csv"


def clean(value: str | None) -> str:
    return (value or "").strip()


def source_display_name(row: dict[str, str]) -> str:
    """Keep the original dataset ID and product details searchable."""
    parts = [
        f"{SOURCE_PREFIX} {clean(row.get('brand id'))}",
        f"Generic: {clean(row.get('generic')) or 'Unknown'}",
        f"Strength: {clean(row.get('strength')) or 'Unknown'}",
        f"Slug: {clean(row.get('slug'))}",
    ]
    return " | ".join(parts)[:500]


def parse_ingredient_names(
    generic: str,
    medicine_type: str,
) -> list[str]:
    """
    Parse only conservative, allopathic ingredient strings.

    A plus sign inside square brackets can describe a botanical
    mixture rather than separate active ingredients, so those
    entries are left unmapped for manual review.
    """
    generic = clean(generic)

    if not generic or medicine_type.lower() != "allopathic":
        return []

    if "[" in generic or "]" in generic:
        return []

    if "+" in generic:
        names = [part.strip() for part in generic.split("+")]
    else:
        names = [generic]

    if not names or any(not name for name in names):
        return []

    if any(len(name) > 200 for name in names):
        return []

    return list(dict.fromkeys(names))


def load_rows() -> list[dict[str, str]]:
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {CSV_PATH}"
        )

    with CSV_PATH.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)
        required = {
            "brand id",
            "brand name",
            "type",
            "slug",
            "dosage form",
            "generic",
            "strength",
            "manufacturer",
        }

        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"CSV is missing columns: {sorted(missing)}"
            )

        rows = []
        seen_ids = set()

        for row in reader:
            brand_id = clean(row.get("brand id"))
            brand_name = clean(row.get("brand name"))

            if not brand_id or not brand_name:
                continue

            if brand_id in seen_ids:
                continue

            seen_ids.add(brand_id)
            rows.append(row)

    return rows


def run_import(apply_changes: bool) -> None:
    rows = load_rows()
    print(f"CSV products loaded: {len(rows)}")
    print(f"Mode: {'IMPORT' if apply_changes else 'DRY RUN'}")

    with SessionLocal() as db:
        existing_medicines = db.scalars(
            select(Medicine)
        ).all()

        existing_source_ids = {
            medicine.source_display_name.split(" | ", 1)[0]
            for medicine in existing_medicines
            if medicine.source_display_name
            and medicine.source_display_name.startswith(
                SOURCE_PREFIX
            )
        }

        existing_ingredients = {
            ingredient.name.casefold(): ingredient
            for ingredient in db.scalars(
                select(ActiveIngredient)
            ).all()
        }

        existing_links = {
            (link.medicine_id, link.ingredient_id)
            for link in db.scalars(
                select(MedicineIngredient)
            ).all()
        }

        pending_medicines = []
        pending_links = []
        skipped_existing = 0
        unmapped_products = 0
        ingredient_names_seen = set()

        for row in rows:
            brand_id = clean(row.get("brand id"))
            source_id = f"{SOURCE_PREFIX} {brand_id}"

            if source_id in existing_source_ids:
                skipped_existing += 1
                continue

            generic = clean(row.get("generic"))
            medicine_type = clean(row.get("type"))
            ingredients = parse_ingredient_names(
                generic, medicine_type
            )

            if not ingredients:
                unmapped_products += 1

            medicine = Medicine(
                brand_name=clean(row.get("brand name"))[:200],
                source_display_name=source_display_name(row),
                generic_name=(generic[:200] or None),
                dosage_form=(
                    clean(row.get("dosage form"))[:100] or None
                ),
                manufacturer=(
                    clean(row.get("manufacturer"))[:200] or None
                ),
                rxnorm_rxcui=None,
            )

            pending_medicines.append((medicine, ingredients))
            existing_source_ids.add(source_id)

        new_count = len(pending_medicines)
        print(f"New products: {new_count}")
        print(f"Already imported: {skipped_existing}")
        print(f"Products without automatic ingredient mapping: {unmapped_products}")

        if not apply_changes:
            print("Dry run complete. No database changes made.")
            return

        imported = 0
        mapped_links = 0

        for start in range(0, len(pending_medicines), BATCH_SIZE):
            batch = pending_medicines[
                start : start + BATCH_SIZE
            ]

            for medicine, ingredient_names in batch:
                db.add(medicine)

            db.flush()

            new_ingredient_names = {
                name
                for _, names in batch
                for name in names
                if name.casefold() not in existing_ingredients
            }

            for name in sorted(new_ingredient_names):
                ingredient = ActiveIngredient(name=name)
                db.add(ingredient)
                existing_ingredients[name.casefold()] = ingredient

            db.flush()

            retrieved_at = datetime.now(timezone.utc)

            for medicine, ingredient_names in batch:
                imported += 1

                for name in ingredient_names:
                    ingredient = existing_ingredients.get(
                        name.casefold()
                    )
                    if ingredient is None:
                        continue

                    link_key = (medicine.id, ingredient.id)
                    if link_key in existing_links:
                        continue

                    db.add(
                        MedicineIngredient(
                            medicine_id=medicine.id,
                            ingredient_id=ingredient.id,
                            amount=None,
                            unit=None,
                            source_name=SOURCE_NAME,
                            source_record_id=(
                                clean(medicine.source_display_name)
                                .split(" | ", 1)[0]
                                .replace(SOURCE_PREFIX + " ", "")
                            ),
                            source_url=SOURCE_URL,
                            retrieved_at=retrieved_at,
                        )
                    )
                    existing_links.add(link_key)
                    mapped_links += 1

            db.commit()
            print(f"Committed {imported}/{new_count} products")

        print("Import complete.")
        print(f"Products imported: {imported}")
        print(f"Ingredient links created: {mapped_links}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import Bangladesh medicine catalog."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to the database. Default is dry-run.",
    )
    args = parser.parse_args()

    try:
        run_import(apply_changes=args.apply)
    except Exception:
        raise


if __name__ == "__main__":
    main()
