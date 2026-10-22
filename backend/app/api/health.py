
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db


router = APIRouter(tags=["Health"])


@router.api_route("/health", methods=["GET", "HEAD"])
def health_check(db: Session = Depends(get_db)):
    """Check API and database health."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
            },
        )

    return {
        "status": "ok",
        "database": "connected",
    }
