
from __future__ import annotations

import os
import re
import shutil

import pytesseract
from PIL import Image


# Allow configuration for local development and deployment.
# Prefer a valid explicit path, then discover Tesseract on the system PATH.
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
    r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml)\b",
    re.IGNORECASE,
)


def _preprocess_image(image: Image.Image) -> list:
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

    return [gray, contrast]


def _extract_candidate(
    image,
    config: str,
) -> tuple[str, float]:
    """Extract text and calculate average confidence for recognized words."""
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


def _normalize_text(text: str) -> str:
    """Remove repeated lines and normalize whitespace."""
    seen: set[str] = set()
    cleaned_lines: list[str] = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if not line:
            continue

        normalized = re.sub(r"[^a-z0-9]", "", line.lower())

        # Ignore exact repeated OCR lines while preserving their first
        # occurrence and the original readable text.
        if normalized and normalized in seen:
            continue

        if normalized:
            seen.add(normalized)

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _score_text(text: str, confidence: float) -> float:
    """Rank candidates using OCR confidence and medicine-related clues."""
    normalized = re.sub(r"\s+", " ", text).strip()

    if not normalized:
        return 0.0

    lowered = normalized.lower()
    score = confidence * 0.7

    # Favor readable words, not simply long strings of OCR noise.
    words = re.findall(r"[a-zA-Z]{3,}", normalized)
    score += min(len(words), 30) * 0.4

    for term in MEDICINE_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            score += 12

    if STRENGTH_PATTERN.search(lowered):
        score += 15

    alphanumeric_count = sum(char.isalnum() for char in normalized)
    symbol_count = sum(
        not char.isalnum() and not char.isspace()
        for char in normalized
    )

    if alphanumeric_count:
        score -= min(symbol_count / alphanumeric_count, 1.0) * 10

    return score


def extract_text_from_image(image: Image.Image) -> str:
    """Return the highest-ranked OCR result from multiple image variants."""
    best_text = ""
    best_score = 0.0

    for variant in _preprocess_image(image):
        for config in OCR_CONFIGS:
            text, confidence = _extract_candidate(variant, config)

            if not text.strip():
                continue

            candidate_score = _score_text(text, confidence)

            if candidate_score > best_score:
                best_score = candidate_score
                best_text = text

    return _normalize_text(best_text)
