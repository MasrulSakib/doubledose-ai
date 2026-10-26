
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.matcher import (
    MatcherComparisonRequest,
    MatcherComparisonResponse,
)
from app.services.ocr_matching_service import match_medicines_from_ocr
from app.services.semantic_matching_service import match_medicines_semantic
from app.services.tfidf_matching_service import match_medicines_tfidf

router = APIRouter(prefix="/matcher", tags=["Medicine Matcher"])


@router.post(
    "/compare",
    response_model=MatcherComparisonResponse,
)
def compare_medicine_matchers(
    payload: MatcherComparisonRequest,
    db: Session = Depends(get_db),
):
    rapidfuzz_results = match_medicines_from_ocr(
        db=db,
        extracted_text=payload.extracted_text,
        limit=payload.limit,
    )

    tfidf_results = match_medicines_tfidf(
        db=db,
        extracted_text=payload.extracted_text,
        limit=payload.limit,
    )

    semantic_results = match_medicines_semantic(
        db=db,
        extracted_text=payload.extracted_text,
        limit=payload.limit,
    )

    return {
        "rapidfuzz": rapidfuzz_results,
        "tfidf": tfidf_results,
        "semantic_faiss": semantic_results,
        "extracted_text": payload.extracted_text,
    }
