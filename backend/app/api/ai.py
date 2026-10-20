from fastapi import APIRouter, HTTPException, status
from groq import APIConnectionError, APIStatusError, RateLimitError

from app.schemas.ai_explanation import (
    AIExplanationRequest,
    AIExplanationResponse,
)
from app.services.ai_explanation_service import (
    generate_overlap_explanation,
)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post(
    "/explain-overlap",
    response_model=AIExplanationResponse,
)
async def explain_overlap(
    payload: AIExplanationRequest,
) -> AIExplanationResponse:
    try:
        return await generate_overlap_explanation(payload)

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except RateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is temporarily rate-limited. Please try again later.",
        ) from exc

    except (APIConnectionError, APIStatusError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service could not complete the request.",
        ) from exc