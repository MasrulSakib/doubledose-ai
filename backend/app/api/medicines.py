
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.medicine import (
    ActiveIngredient,
    Medicine,
    MedicineIngredient,
)
from app.schemas.medicine import IngredientResponse, MedicineResponse, OverlapCheckRequest, OverlapCheckResponse
from app.services.medicine_service import search_medicines
from app.services.overlap_service import check_ingredient_overlap


router = APIRouter(
    prefix="/api/v1/medicines",
    tags=["Medicines"],
)


@router.get("", response_model=list[MedicineResponse])
def get_medicines(
    q: str = Query(
        ...,
        min_length=1,
        max_length=100,
        description="Search by brand or generic medicine name",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search the medicine database."""
    return search_medicines(db=db, query=q, limit=limit)


@router.get(
    "/{medicine_id}/ingredients",
    response_model=list[IngredientResponse],
)
def get_medicine_ingredients(
    medicine_id: int,
    db: Session = Depends(get_db),
):
    """Return the active ingredients associated with a medicine."""
    medicine = db.get(Medicine, medicine_id)

    if medicine is None:
        raise HTTPException(
            status_code=404,
            detail="Medicine not found",
        )

    statement = (
        select(
            ActiveIngredient.id,
            ActiveIngredient.name,
            MedicineIngredient.amount,
            MedicineIngredient.unit,
        )
        .join(
            MedicineIngredient,
            MedicineIngredient.ingredient_id == ActiveIngredient.id,
        )
        .where(MedicineIngredient.medicine_id == medicine_id)
        .order_by(ActiveIngredient.name)
    )

    rows = db.execute(statement).all()

    return [
        IngredientResponse(
            id=row.id,
            name=row.name,
            amount=float(row.amount) if row.amount is not None else None,
            unit=row.unit,
        )
        for row in rows
    ]


@router.post("/check-overlap", response_model=OverlapCheckResponse)
def check_medicines_overlap(
    request: OverlapCheckRequest,
    db: Session = Depends(get_db),
):
    """Check for active ingredients shared by selected medicines."""
    try:
        return check_ingredient_overlap(
            db=db,
            medicine_ids=request.medicine_ids,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
