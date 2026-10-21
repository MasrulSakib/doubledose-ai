
from io import BytesIO

import pytesseract
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.services.detection_service import detect_label_crops
from app.services.ocr_service import extract_text_from_image
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.session import get_db
from app.services.ocr_matching_service import match_medicines_from_ocr

router = APIRouter(prefix="/ocr", tags=["OCR"])

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/extract")
async def extract_medicine_text(file: UploadFile = File(...)):
    """Extract text from a medicine photo without saving the image."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Upload a JPEG, PNG, or WebP image.",
        )

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
        image = image.convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid image.",
        )
    finally:
        await file.close()

    detection_used = False

    try:
        label_crops = detect_label_crops(image)

        if label_crops:
            extracted_text = "\n".join(
                text
                for crop in label_crops
                if (text := extract_text_from_image(crop))
            )
            detection_used = bool(extracted_text)

        else:
            extracted_text = ""

        # Fall back to the complete image if detection fails
        # or detected crops contain no readable text.
        if not extracted_text:
            extracted_text = extract_text_from_image(image)
            detection_used = False

    except pytesseract.TesseractNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="OCR engine is unavailable on this server.",
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process this image.",
        )

    return {
        "extracted_text": extracted_text,
        "text_found": bool(extracted_text),
        "detection_used": detection_used,
        "fallback_used": not detection_used,
        "message": (
            "Text extracted successfully."
            if extracted_text
            else "No text detected. Try a clearer photo or type the medicine name."
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
            else "No likely matches found. Try clearer OCR text or search by name."
        ),
    }

