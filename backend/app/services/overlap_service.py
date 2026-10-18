
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
    """Identify active ingredients shared by multiple medicines."""

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
        lambda: {"name": "", "medicine_ids": [], "medicine_names": []}
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

    return OverlapCheckResponse(
        medicines=[
            MedicineResponse.model_validate(medicine)
            for medicine in medicines
        ],
        has_overlap=bool(overlapping_ingredients),
        overlapping_ingredients=overlapping_ingredients,
    )
