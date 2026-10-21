
import os
from pathlib import Path

import numpy as np
from PIL import Image
from ultralytics import YOLO


_model = None
_model_path_loaded = None


def detect_label_crops(image: Image.Image) -> list[Image.Image]:
    """
    Detect medicine-label regions using custom YOLO weights.

    Returns detected image crops. Returns an empty list when a
    trained model is not configured or no usable region is detected.
    """
    global _model, _model_path_loaded

    model_path = os.getenv("YOLO_MODEL_PATH", "").strip()

    if not model_path or not Path(model_path).is_file():
        return []

    try:
        if _model is None or _model_path_loaded != model_path:
            _model = YOLO(model_path)
            _model_path_loaded = model_path

        rgb_image = np.array(image.convert("RGB"))
        results = _model.predict(
            source=rgb_image,
            conf=0.25,
            verbose=False,
        )

        crops = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                x1, y1, x2, y2 = map(
                    int, box.xyxy[0].tolist()
                )

                # Keep coordinates inside the original image.
                x1 = max(0, min(x1, image.width - 1))
                y1 = max(0, min(y1, image.height - 1))
                x2 = max(0, min(x2, image.width))
                y2 = max(0, min(y2, image.height))

                if x2 > x1 and y2 > y1:
                    crops.append(image.crop((x1, y1, x2, y2)))

        return crops

    except Exception:
        # Detection must not prevent the existing OCR fallback.
        return []
