import re
from io import BytesIO

import pytesseract
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.detection_service import detect_label_crops
from app.services.ocr_matching_service import match_medicines_from_ocr
from app.services.ocr_service import extract_text_from_image
from app.services.semantic_matching_service import match_medicines_semantic


router = APIRouter(prefix="/ocr", tags=["OCR"])

MAX_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _rank_extracted_text(text: str) -> tuple[int, int, int, int]:
    """Prefer OCR results containing medicine names and strength information."""
    normalized = re.sub(r"\s+", " ", text).strip().lower()

    medicine_terms = (
        "paracetamol",
        "acetaminophen",
        "tablet",
        "capsule",
        "syrup",
        "medicine",
        "pharma",
    )

    medicine_score = sum(
        1
        for term in medicine_terms
        if re.search(rf"\b{re.escape(term)}\b", normalized)
    )

    has_strength = int(
        bool(
            re.search(
                r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml)\b",
                normalized,
            )
        )
    )

    readable_words = len(re.findall(r"\b[a-z]{3,}\b", normalized))
    useful_characters = sum(char.isalnum() for char in normalized)

    return (
        medicine_score,
        has_strength,
        readable_words,
        useful_characters,
    )


@router.post("/extract")
async def extract_medicine_text(file: UploadFile = File(...)):
    """Extract text from a medicine photo without saving the image."""

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Upload a JPEG, PNG, or WebP image.",
        )

    try:
        contents = await file.read(MAX_IMAGE_SIZE + 1)

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        if len(contents) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Image must be 10 MB or smaller.",
            )

        try:
            image = Image.open(BytesIO(contents))
            image.load()
            image = ImageOps.exif_transpose(image).convert("RGB")
        except (UnidentifiedImageError, OSError):
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid image.",
            ) from None

    finally:
        await file.close()

    try:
        candidates: list[tuple[str, bool]] = []

        # Try text from detected medicine-label regions first.
        label_crops = detect_label_crops(image)

        for crop in label_crops or []:
            text = extract_text_from_image(crop).strip()

            if text:
                candidates.append((text, True))

        # Also process the complete image as a fallback.
        full_image_text = extract_text_from_image(image).strip()

        if full_image_text:
            candidates.append((full_image_text, False))

    except pytesseract.TesseractNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="OCR engine is unavailable on this server.",
        ) from None

    except RuntimeError as exc:
        if "timeout" in str(exc).lower():
            raise HTTPException(
                status_code=422,
                detail="OCR took too long. Try a smaller or clearer image.",
            ) from None

        raise HTTPException(
            status_code=500,
            detail="Unable to process this image.",
        ) from None

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process this image.",
        ) from None

    if candidates:
        extracted_text, detection_used = max(
            candidates,
            key=lambda candidate: _rank_extracted_text(candidate[0]),
        )

        # Normalize whitespace while preserving extracted words.
        extracted_text = "\n".join(
            line.strip()
            for line in extracted_text.splitlines()
            if line.strip()
        )
    else:
        extracted_text = ""
        detection_used = False

    text_found = bool(extracted_text.strip())

    return {
        "extracted_text": extracted_text,
        "text_found": text_found,
        "detection_used": detection_used,
        "fallback_used": not detection_used,
        "message": (
            "Text extracted successfully."
            if text_found
            else (
                "No text detected. Try a clearer photo "
                "or type the medicine name."
            )
        ),
    }


class OCRMatchRequest(BaseModel):
    extracted_text: str = Field(min_length=1, max_length=20_000)
    limit: int = Field(default=10, ge=1, le=20)




@router.post("/match")
def match_ocr_medicines(
    payload: OCRMatchRequest,
    db: Session = Depends(get_db),
):
    """Match extracted OCR text against the medicine database."""

    try:
        matches = match_medicines_semantic(
            db=db,
            extracted_text=payload.extracted_text,
            limit=payload.limit,
        )
    except Exception:
        # Preserve OCR matching if semantic matching is unavailable.
        matches = match_medicines_from_ocr(
            db=db,
            extracted_text=payload.extracted_text,
            limit=payload.limit,
        )

    return {
        "matches": matches,
        "match_count": len(matches),
        "message": (
            "Review the candidate matches and confirm the medicine."
            if matches
            else (
                "No likely matches found. Try clearer OCR text "
                "or search by name."
            )
        ),
    }

