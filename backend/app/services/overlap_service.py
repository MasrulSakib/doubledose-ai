
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.medicine import (
    ActiveIngredient,
    Medicine,
    MedicineIngredient,
)
from app.schemas.medicine import (
    MedicineResponse,
    OverlapCheckResponse,
    OverlappingIngredient,
)


def check_ingredient_overlap(
    db: Session,
    medicine_ids: list[int],
) -> OverlapCheckResponse:
    """Identify shared ingredients and flag missing ingredient data."""

    medicines = list(
        db.scalars(
            select(Medicine)
            .where(Medicine.id.in_(medicine_ids))
            .order_by(Medicine.id)
        ).all()
    )

    found_ids = {medicine.id for medicine in medicines}
    missing_ids = set(medicine_ids) - found_ids

    if missing_ids:
        raise LookupError(
            f"Medicine IDs not found: {sorted(missing_ids)}"
        )

    # Identify selected medicines that have ingredient records.
    ingredient_data_statement = (
        select(MedicineIngredient.medicine_id)
        .where(MedicineIngredient.medicine_id.in_(medicine_ids))
        .distinct()
    )

    medicines_with_ingredient_data = set(
        db.scalars(ingredient_data_statement).all()
    )

    medicines_without_ingredient_data = sorted(
        set(medicine_ids) - medicines_with_ingredient_data
    )

    # Retrieve ingredient records for the selected medicines.
    statement = (
        select(
            MedicineIngredient.medicine_id,
            Medicine.brand_name,
            ActiveIngredient.id,
            ActiveIngredient.name,
        )
        .join(
            Medicine,
            Medicine.id == MedicineIngredient.medicine_id,
        )
        .join(
            ActiveIngredient,
            ActiveIngredient.id == MedicineIngredient.ingredient_id,
        )
        .where(MedicineIngredient.medicine_id.in_(medicine_ids))
        .order_by(ActiveIngredient.name)
    )

    rows = db.execute(statement).all()

    ingredient_matches = defaultdict(
        lambda: {
            "name": "",
            "medicine_ids": [],
            "medicine_names": [],
        }
    )

    for row in rows:
        ingredient = ingredient_matches[row.id]
        ingredient["name"] = row.name

        if row.medicine_id not in ingredient["medicine_ids"]:
            ingredient["medicine_ids"].append(row.medicine_id)
            ingredient["medicine_names"].append(row.brand_name)

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

    has_overlap = bool(overlapping_ingredients)
    has_incomplete_data = bool(medicines_without_ingredient_data)

    if has_overlap:
        result_status = "overlap_found"
    elif has_incomplete_data:
        result_status = "incomplete_data"
    else:
        result_status = "no_overlap_found"

    return OverlapCheckResponse(
        medicines=[
            MedicineResponse.model_validate(medicine)
            for medicine in medicines
        ],
        has_overlap=has_overlap,
        overlapping_ingredients=overlapping_ingredients,
        result_status=result_status,
        has_incomplete_data=has_incomplete_data,
        medicines_without_ingredient_data=(
            medicines_without_ingredient_data
        ),
    )
