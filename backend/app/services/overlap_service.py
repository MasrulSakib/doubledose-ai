
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.medicine import (
    ActiveIngredient,
    Medicine,
    MedicineIngredient,
)
from app.schemas.medicine import (
    MedicineComparisonResponse,
    MedicineIngredientDetail,
    OverlapCheckResponse,
    OverlappingIngredient,
)
from app.services.therapeutic_class_service import (
    build_same_class_warnings,
)


def check_ingredient_overlap(
    db: Session,
    medicine_ids: list[int],
) -> OverlapCheckResponse:
    """Compare exact active ingredients and flag known same-class patterns."""

    statement = (
        select(Medicine)
        .options(
            selectinload(Medicine.ingredients).joinedload(
                MedicineIngredient.ingredient
            )
        )
        .where(Medicine.id.in_(medicine_ids))
        .order_by(Medicine.id)
    )

    medicines = list(db.scalars(statement).all())

    found_ids = {medicine.id for medicine in medicines}
    missing_ids = set(medicine_ids) - found_ids

    if missing_ids:
        raise LookupError(f"Medicine IDs not found: {sorted(missing_ids)}")

    medicines_without_ingredient_data = sorted(
        medicine.id
        for medicine in medicines
        if not medicine.ingredients
    )

    medicine_details = []

    for medicine in medicines:
        ingredient_details = []

        for association in medicine.ingredients:
            ingredient = association.ingredient

            ingredient_details.append(
                MedicineIngredientDetail(
                    id=ingredient.id,
                    name=ingredient.name,
                    amount=(
                        float(association.amount)
                        if association.amount is not None
                        else None
                    ),
                    unit=association.unit,
                    source_name=association.source_name,
                    source_record_id=association.source_record_id,
                    source_url=association.source_url,
                    retrieved_at=association.retrieved_at,
                )
            )

        medicine_details.append(
            MedicineComparisonResponse(
                id=medicine.id,
                brand_name=medicine.brand_name,
                source_display_name=medicine.source_display_name,
                generic_name=medicine.generic_name,
                dosage_form=medicine.dosage_form,
                manufacturer=medicine.manufacturer,
                ingredients=ingredient_details,
            )
        )

    ingredient_matches = defaultdict(
        lambda: {
            "name": "",
            "medicine_ids": [],
            "medicine_names": [],
        }
    )

    for medicine in medicines:
        for association in medicine.ingredients:
            ingredient = association.ingredient
            match = ingredient_matches[ingredient.id]

            match["name"] = ingredient.name

            if medicine.id not in match["medicine_ids"]:
                match["medicine_ids"].append(medicine.id)
                match["medicine_names"].append(medicine.brand_name)

    overlapping_ingredients = [
        OverlappingIngredient(
            ingredient_id=ingredient_id,
            name=ingredient["name"],
            medicine_ids=ingredient["medicine_ids"],
            medicine_names=ingredient["medicine_names"],
        )
        for ingredient_id, ingredient in ingredient_matches.items()
        if len(ingredient["medicine_ids"]) >= 2
    ]

    overlapping_ingredients.sort(key=lambda item: item.name.casefold())

    # Separate from exact ingredient overlap: this uses an explicit,
    # curated therapeutic-class mapping.
    same_class_warnings = build_same_class_warnings(medicines)

    has_overlap = bool(overlapping_ingredients)
    has_incomplete_data = bool(medicines_without_ingredient_data)

    if has_overlap:
        result_status = "overlap_found"
    elif has_incomplete_data:
        result_status = "incomplete_data"
    else:
        result_status = "no_overlap_found"

    return OverlapCheckResponse(
        medicines=medicine_details,
        has_overlap=has_overlap,
        overlapping_ingredients=overlapping_ingredients,
        same_class_warnings=same_class_warnings,
        result_status=result_status,
        has_incomplete_data=has_incomplete_data,
        medicines_without_ingredient_data=medicines_without_ingredient_data,
    )
