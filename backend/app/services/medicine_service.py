
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.medicine import Medicine


def search_medicines(
    db: Session,
    query: str,
    limit: int = 20,
) -> list[Medicine]:
    """Search medicines by brand name or generic name."""
    search_term = query.strip()

    if not search_term:
        return []

    statement = (
        select(Medicine)
        .where(
            or_(
                Medicine.brand_name.ilike(f"%{search_term}%"),
                Medicine.generic_name.ilike(f"%{search_term}%"),
                Medicine.source_display_name.ilike(f"%{query}%"),
            )
        )
        .order_by(Medicine.brand_name)
        .limit(limit)
    )

    return list(db.scalars(statement).all())
