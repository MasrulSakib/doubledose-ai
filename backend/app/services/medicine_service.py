
from sqlalchemy import case, or_, select
from sqlalchemy.orm import Session

from app.models.medicine import Medicine


def search_medicines(
    db: Session,
    query: str,
    limit: int = 20,
) -> list[Medicine]:
    """Search medicines with brand-name matches prioritized."""

    search_term = query.strip()

    if not search_term:
        return []

    exact_pattern = search_term
    prefix_pattern = f"{search_term}%"
    contains_pattern = f"%{search_term}%"

    statement = (
        select(Medicine)
        .where(
            or_(
                Medicine.brand_name.ilike(contains_pattern),
                Medicine.generic_name.ilike(contains_pattern),
                Medicine.source_display_name.ilike(contains_pattern),
            )
        )
        .order_by(
            case(
                (Medicine.brand_name.ilike(exact_pattern), 0),
                (Medicine.brand_name.ilike(prefix_pattern), 1),
                (Medicine.generic_name.ilike(exact_pattern), 2),
                (Medicine.generic_name.ilike(prefix_pattern), 3),
                else_=4,
            ),
            Medicine.brand_name,
            Medicine.id,
        )
        .limit(limit)
    )

    return list(db.scalars(statement).all())
