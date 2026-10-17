
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.medicine import MedicineResponse
from app.services.medicine_service import search_medicines


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
