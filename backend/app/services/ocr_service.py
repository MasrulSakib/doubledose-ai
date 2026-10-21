
import os

import cv2
import numpy as np
import pytesseract
from PIL import Image, UnidentifiedImageError


# Allow the executable path to be configured for local development
# and deployment.
tesseract_path = os.getenv("TESSERACT_CMD")

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
elif os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )


def extract_text_from_image(image: Image.Image) -> str:
    """Preprocess an image in memory and extract its text."""
    rgb_image = np.array(image.convert("RGB"))
    gray_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)

    enlarged = cv2.resize(
        gray_image,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC,
    )

    denoised = cv2.GaussianBlur(enlarged, (3, 3), 0)

    processed = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    text = pytesseract.image_to_string(
        processed,
        config="--oem 3 --psm 6",
    )

    return text.strip()
