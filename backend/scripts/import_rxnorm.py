
import argparse
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.medicine import (
    ActiveIngredient,
    Medicine,
    MedicineIngredient,
)


BASE_URL = "https://rxnav.nlm.nih.gov/REST"
SOURCE_NAME = "RxNorm"


def fetch_branded_medicines(
    client: httpx.Client,
    search_term: str,
    limit: int,
) -> list[dict]:
    response = client.get(
        f"{BASE_URL}/drugs.json",
        params={"name": search_term},
    )
    response.raise_for_status()

    groups = (
        response.json()
        .get("drugGroup", {})
        .get("conceptGroup")
        or []
    )

    medicines = []

    for group in groups:
        if group.get("tty") != "SBD":
            continue

        for concept in group.get("conceptProperties") or []:
            if concept.get("suppress") != "N":
                continue

            if not concept.get("rxcui") or not concept.get("name"):
                continue

            # Accept only records with an explicit trailing brand label.
            match = re.search(r"\[([^\[\]]+)\]\s*$", concept["name"])
            if not match:
                continue

            medicines.append(
                {
                    "rxcui": concept["rxcui"],
                    "display_name": concept["name"],
                    "brand_name": match.group(1).strip(),
                }
            )

            if len(medicines) >= limit:
                return medicines

    return medicines


def fetch_ingredients(
    client: httpx.Client,
    medicine_rxcui: str,
) -> list[dict]:
    response = client.get(
        f"{BASE_URL}/rxcui/{medicine_rxcui}/related.json",
        params={"tty": "IN"},
    )
    response.raise_for_status()

    groups = (
        response.json()
        .get("relatedGroup", {})
        .get("conceptGroup")
        or []
    )

    ingredients = []

    for group in groups:
        if group.get("tty") != "IN":
            continue

        for concept in group.get("conceptProperties") or []:
            if concept.get("rxcui") and concept.get("name"):
                ingredients.append(
                    {
                        "rxcui": concept["rxcui"],
                        "name": concept["name"],
                    }
                )

    return ingredients


def validate_ingredients(ingredients: list[dict]) -> None:
    """Reject incomplete or duplicate RxNorm ingredient records."""
    if not ingredients:
        raise ValueError("Medicine must have at least one ingredient.")

    seen_rxcuis = set()

    for index, ingredient in enumerate(ingredients):
        rxcui = ingredient.get("rxcui")
        name = ingredient.get("name")

        if not isinstance(rxcui, str) or not rxcui.strip():
            raise ValueError(
                f"Ingredient at index {index} has a missing or invalid RxNorm ID."
            )

        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"Ingredient at index {index} has a missing or invalid name."
            )

        if rxcui in seen_rxcuis:
            raise ValueError(
                f"Duplicate RxNorm ingredient ID: {rxcui}"
            )

        seen_rxcuis.add(rxcui)


def save_medicine(
    db: Session,
    medicine_data: dict,
    ingredients: list[dict],
) -> str:
    validate_ingredients(ingredients)
    medicine = db.scalar(
        select(Medicine).where(
            Medicine.rxnorm_rxcui == medicine_data["rxcui"]
        )
    )

    if medicine is None:
        medicine = Medicine(
            brand_name=medicine_data["brand_name"],
            source_display_name=medicine_data["display_name"],
            generic_name=None,
            dosage_form=None,
            manufacturer=None,
            rxnorm_rxcui=medicine_data["rxcui"],
        )
        db.add(medicine)
        db.flush()
    else:
        medicine.brand_name = medicine_data["brand_name"]
        medicine.source_display_name = medicine_data["display_name"]

    # Keep existing ORM objects so their IDs and ingredient amounts
    # remain unchanged when source metadata is refreshed.
    existing_links = {
        link.ingredient_id: link
        for link in db.scalars(
            select(MedicineIngredient).where(
                MedicineIngredient.medicine_id == medicine.id
            )
        ).all()
    }

    source_record_id = medicine_data["rxcui"]
    source_url = (
        f"{BASE_URL}/rxcui/{source_record_id}/related.json?tty=IN"
    )
    retrieved_at = datetime.now(timezone.utc)

    for ingredient_data in ingredients:
        ingredient = db.scalar(
            select(ActiveIngredient).where(
                ActiveIngredient.rxnorm_rxcui == ingredient_data["rxcui"]
            )
        )

        if ingredient is None:
            # Reuse a same-name ingredient only when its source ID
            # is absent or matches the incoming RxNorm identifier.
            ingredient = db.scalar(
                select(ActiveIngredient).where(
                    ActiveIngredient.name == ingredient_data["name"]
                )
            )

            if ingredient is not None:
                if (
                    ingredient.rxnorm_rxcui is not None
                    and ingredient.rxnorm_rxcui
                    != ingredient_data["rxcui"]
                ):
                    raise ValueError(
                        "Ingredient name conflicts with a different "
                        f"RxNorm ID: {ingredient_data['name']}"
                    )

                ingredient.rxnorm_rxcui = ingredient_data["rxcui"]
            else:
                ingredient = ActiveIngredient(
                    name=ingredient_data["name"],
                    rxnorm_rxcui=ingredient_data["rxcui"],
                )
                db.add(ingredient)
                db.flush()

        existing_link = existing_links.get(ingredient.id)

        if existing_link is not None:
            # Refresh provenance without replacing the link or
            # overwriting its existing amount and unit.
            existing_link.source_name = SOURCE_NAME
            existing_link.source_record_id = source_record_id
            existing_link.source_url = source_url
            existing_link.retrieved_at = retrieved_at
            continue

        link = MedicineIngredient(
            medicine_id=medicine.id,
            ingredient_id=ingredient.id,
            amount=None,
            unit=None,
            source_name=SOURCE_NAME,
            source_record_id=source_record_id,
            source_url=source_url,
            retrieved_at=retrieved_at,
        )

        db.add(link)
        existing_links[ingredient.id] = link

    return medicine_data["rxcui"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a small batch of branded RxNorm concepts."
    )
    parser.add_argument("--search", default="acetaminophen")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write records to the database. Without this flag, preview only.",
    )
    args = parser.parse_args()

    if args.limit < 1 or args.limit > 20:
        parser.error("--limit must be between 1 and 20")

    try:
        with httpx.Client(timeout=20) as client:
            medicines = fetch_branded_medicines(
                client,
                args.search,
                args.limit,
            )

            if not medicines:
                print("No eligible branded medicine concepts found.")
                return

            records = []

            for medicine in medicines:
                ingredients = fetch_ingredients(
                    client,
                    medicine["rxcui"],
                )

                if not ingredients:
                    print(
                        "Skipping concept without resolved ingredients:",
                        medicine["rxcui"],
                    )
                    continue

                records.append((medicine, ingredients))

    except httpx.HTTPError as exc:
        print(f"RxNorm API request failed: {exc}")
        raise SystemExit(1) from exc

    for medicine, ingredients in records:
        print(f"\nBrand: {medicine['brand_name']}")
        print(f"Display name: {medicine['display_name']}")
        print(f"RxCUI: {medicine['rxcui']}")
        print("Ingredients:", ", ".join(i["name"] for i in ingredients))

    if not args.apply:
        print(
            f"\nDry run complete: {len(records)} medicine(s) previewed. "
            "Nothing was saved."
        )
        print("Review the results, then rerun with --apply to import.")
        return

    db = SessionLocal()

    try:
        for medicine, ingredients in records:
            save_medicine(db, medicine, ingredients)

        db.commit()
        print(f"\nImport complete: processed {len(records)} medicine(s).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
