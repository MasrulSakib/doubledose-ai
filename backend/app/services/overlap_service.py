
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.medicine import (
    ActiveIngredient,
    Medicine,
    MedicineIngredient,
)
from app.services.ingredient_normalizer import (
    canonical_ingredient_key,
    normalize_ingredient_name,
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

    # Return medicines in the order the caller requested them.
    request_position = {mid: position for position, mid in enumerate(medicine_ids)}
    medicines.sort(key=lambda medicine: request_position.get(medicine.id, 0))

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

    # Group by active moiety so salt, hydrate and spacing variants of the
    # same ingredient are compared as one ingredient.
    ingredient_matches = defaultdict(
        lambda: {
            "variants": {},
            "medicine_ids": [],
            "medicine_names": [],
        }
    )

    for medicine in medicines:
        for association in medicine.ingredients:
            ingredient = association.ingredient
            match = ingredient_matches[canonical_ingredient_key(ingredient.name)]

            match["variants"][ingredient.id] = ingredient.name

            if medicine.id not in match["medicine_ids"]:
                match["medicine_ids"].append(medicine.id)
                match["medicine_names"].append(medicine.brand_name)

    overlapping_ingredients = []

    for match in ingredient_matches.values():
        if len(match["medicine_ids"]) < 2:
            continue

        # Report the plainest recorded form (e.g. "Amoxicillin").
        ingredient_id, name = min(
            match["variants"].items(),
            key=lambda item: (len(normalize_ingredient_name(item[1])), item[0]),
        )

        overlapping_ingredients.append(
            OverlappingIngredient(
                ingredient_id=ingredient_id,
                name=name,
                medicine_ids=match["medicine_ids"],
                medicine_names=match["medicine_names"],
            )
        )

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
