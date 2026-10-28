from __future__ import annotations

import logging
import os
import re
import shutil
from io import BytesIO
from typing import Any

import httpx
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Tesseract configuration
# ---------------------------------------------------------

tesseract_path = os.getenv("TESSERACT_CMD", "").strip()

if tesseract_path and (
    os.path.isfile(tesseract_path) or shutil.which(tesseract_path)
):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    detected_path = shutil.which("tesseract")

    if detected_path:
        pytesseract.pytesseract.tesseract_cmd = detected_path
    elif os.name == "nt":
        windows_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

        if os.path.isfile(windows_path):
            pytesseract.pytesseract.tesseract_cmd = windows_path


OCR_CONFIGS = (
    "--oem 3 --psm 6",
    "--oem 3 --psm 11",
)

MEDICINE_TERMS = (
    "paracetamol",
    "acetaminophen",
    "tablet",
    "capsule",
    "syrup",
    "medicine",
    "pharma",
)

STRENGTH_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*"
    r"(?:mg|mcg|g|ml|iu|units?)\b",
    re.IGNORECASE,
)

OCR_SPACE_URL = "https://api.ocr.space/parse/image"


# ---------------------------------------------------------
# OCR.space fallback
# ---------------------------------------------------------

def _extract_text_with_ocr_space(image: Image.Image) -> str:
    """Extract medicine-label text using the hosted OCR.space API."""
    api_key = os.getenv("OCR_SPACE_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "OCR_SPACE_API_KEY is not configured on the server."
        )

    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    try:
        response = httpx.post(
            OCR_SPACE_URL,
            headers={"apikey": api_key},
            data={
                "language": "eng",
                "isOverlayRequired": "false",
                "scale": "true",
                "OCREngine": "2",
            },
            files={
                "file": (
                    "medicine.png",
                    image_bytes,
                    "image/png",
                )
            },
            timeout=35.0,
        )
        response.raise_for_status()
        result = response.json()

    except httpx.TimeoutException:
        logger.warning("OCR.space request timed out.")
        raise RuntimeError(
            "Hosted OCR timed out. Please try again."
        ) from None

    except httpx.HTTPError:
        logger.exception("OCR.space HTTP request failed.")
        raise RuntimeError(
            "Hosted OCR is temporarily unavailable."
        ) from None

    except ValueError:
        logger.exception("OCR.space returned invalid JSON.")
        raise RuntimeError(
            "Hosted OCR returned an invalid response."
        ) from None

    if result.get("IsErroredOnProcessing"):
        logger.error(
            "OCR.space processing error: %s",
            result.get("ErrorMessage"),
        )
        raise RuntimeError(
            "Hosted OCR could not process this image."
        )

    parsed_results = result.get("ParsedResults") or []

    extracted_text = "\n".join(
        item.get("ParsedText", "").strip()
        for item in parsed_results
        if item.get("ParsedText", "").strip()
    )

    if not extracted_text and result.get("ErrorMessage"):
        logger.warning(
            "OCR.space returned no text: %s",
            result.get("ErrorMessage"),
        )

    return _normalize_text(extracted_text)


# ---------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------

def _preprocess_image(image: Image.Image) -> list[Any]:
    """Generate image variants for printed medicine text."""
    import cv2
    import numpy as np

    rgb = np.asarray(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    height, width = gray.shape
    scale = min(3.0, max(1.0, 1800 / max(height, width)))

    if scale > 1:
        gray = cv2.resize(
            gray,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC,
        )

    contrast = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    ).apply(gray)

    denoised = cv2.GaussianBlur(contrast, (3, 3), 0)

    sharpened = cv2.addWeighted(
        contrast,
        1.5,
        cv2.GaussianBlur(contrast, (0, 0), 2),
        -0.5,
        0,
    )

    thresholded = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    # Retain the existing variants used by the local OCR pipeline.
    return [gray, contrast]


# ---------------------------------------------------------
# Local Tesseract extraction
# ---------------------------------------------------------

def _extract_candidate(
    image: Any,
    config: str,
) -> tuple[str, float]:
    """Extract text and calculate average OCR word confidence."""
    data = pytesseract.image_to_data(
        image,
        config=config,
        lang="eng",
        output_type=pytesseract.Output.DICT,
        timeout=15,
    )

    lines: dict[tuple[int, int, int, int], list[str]] = {}
    confidences: list[float] = []

    for index, raw_word in enumerate(data["text"]):
        word = raw_word.strip()

        try:
            confidence = float(data["conf"][index])
        except (TypeError, ValueError):
            continue

        if not word or confidence < 0:
            continue

        key = (
            int(data["block_num"][index]),
            int(data["par_num"][index]),
            int(data["line_num"][index]),
            int(data["page_num"][index]),
        )

        lines.setdefault(key, []).append(word)
        confidences.append(confidence)

    text = "\n".join(
        " ".join(words)
        for words in lines.values()
        if words
    )

    average_confidence = (
        sum(confidences) / len(confidences)
        if confidences
        else 0.0
    )

    return text, average_confidence


# ---------------------------------------------------------
# Text normalization and ranking
# ---------------------------------------------------------

def _normalize_text(text: str) -> str:
    """Remove repeated lines and normalize whitespace."""
    seen: set[str] = set()
    cleaned_lines: list[str] = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if not line:
            continue

        normalized = re.sub(r"[^a-z0-9]", "", line.lower())

        # Preserve the first occurrence of repeated OCR lines.
        if normalized and normalized in seen:
            continue

        if normalized:
            seen.add(normalized)

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _score_text(text: str, confidence: float) -> float:
    """Rank OCR candidates using confidence and medicine-related clues."""
    normalized = re.sub(r"\s+", " ", text).strip()

    if not normalized:
        return 0.0

    lowered = normalized.lower()
    score = confidence * 0.7

    words = re.findall(r"[a-zA-Z]{3,}", normalized)
    score += min(len(words), 30) * 0.4

    for term in MEDICINE_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            score += 12

    if STRENGTH_PATTERN.search(lowered):
        score += 15

    alphanumeric_count = sum(
        char.isalnum() for char in normalized
    )
    symbol_count = sum(
        not char.isalnum() and not char.isspace()
        for char in normalized
    )

    if alphanumeric_count:
        score -= min(
            symbol_count / alphanumeric_count,
            1.0,
        ) * 10

    return score


# ---------------------------------------------------------
# Main OCR entry point
# ---------------------------------------------------------

def extract_text_from_image(image: Image.Image) -> str:
    """
    Extract text using local Tesseract when available.
    Otherwise, fall back to OCR.space.
    """
    configured_path = (
        pytesseract.pytesseract.tesseract_cmd
    )

    tesseract_available = (
        os.path.isfile(configured_path)
        or shutil.which(configured_path) is not None
        or shutil.which("tesseract") is not None
    )

    # Render currently has no Tesseract executable, so use
    # the hosted OCR service without attempting local OCR.
    if not tesseract_available:
        logger.info(
            "Tesseract unavailable; using OCR.space fallback."
        )
        return _extract_text_with_ocr_space(image)

    best_text = ""
    best_score = 0.0

    try:
        for variant in _preprocess_image(image):
            for config in OCR_CONFIGS:
                text, confidence = _extract_candidate(
                    variant,
                    config,
                )

                if not text.strip():
                    continue

                candidate_score = _score_text(
                    text,
                    confidence,
                )

                if candidate_score > best_score:
                    best_score = candidate_score
                    best_text = text

    except pytesseract.TesseractNotFoundError:
        # Recover if the executable disappears or its configured
        # path becomes invalid after the initial availability check.
        logger.warning(
            "Tesseract executable unavailable; using OCR.space."
        )
        return _extract_text_with_ocr_space(image)

    return _normalize_text(best_text)