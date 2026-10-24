# Matcher benchmark

Seed: 42. Sources run: legacy_manual, synthetic_rendered_image.

## legacy_manual

5 hand-typed clean cases. Too small to generalise.

| Matcher | Cases | Top-1 (95% CI) | Top-3 (95% CI) | MRR@3 | No candidate | s/query |
|---|---|---|---|---|---|---|
| rapidfuzz | 5 | 0.8 [0.376, 0.964] | 1.0 [0.566, 1.0] | 0.9 | 0.0 | 1.33 |
| tfidf | 5 | 0.4 [0.118, 0.769] | 0.6 [0.231, 0.882] | 0.5 | 0.0 | 0.62 |

| Group | rapidfuzz top-1 / top-3 | tfidf top-1 / top-3 |
|---|---|---|
| clean | 0.8 / 1.0 (n=5) | 0.4 / 0.6 (n=5) |

Top-1 precision by top-1 score (is the score a usable confidence?):

- rapidfuzz: 0-45: None (n=0), 45-65: None (n=0), 65-80: None (n=0), 80-100: 0.8 (n=5)
- tfidf: 0-45: 0.5 (n=2), 45-65: 0.333 (n=3), 65-80: None (n=0), 80-100: None (n=0)

## synthetic_rendered_image

Labels rendered with a clean font, degraded, then read by the real Tesseract pipeline. Easier than real photos.

| Matcher | Cases | Top-1 (95% CI) | Top-3 (95% CI) | MRR@3 | No candidate | s/query |
|---|---|---|---|---|---|---|
| rapidfuzz | 72 | 0.833 [0.731, 0.902] | 1.0 [0.949, 1.0] | 0.91 | 0.0 | 1.57 |
| tfidf | 72 | 0.653 [0.538, 0.752] | 0.847 [0.747, 0.912] | 0.75 | 0.0 | 0.75 |

| Group | rapidfuzz top-1 / top-3 | tfidf top-1 / top-3 |
|---|---|---|
| blur_rotate | 0.833 / 1.0 (n=24) | 0.625 / 0.833 (n=24) |
| clean | 0.833 / 1.0 (n=24) | 0.667 / 0.833 (n=24) |
| noisy_low_contrast | 0.833 / 1.0 (n=24) | 0.667 / 0.875 (n=24) |

Top-1 precision by top-1 score (is the score a usable confidence?):

- rapidfuzz: 0-45: None (n=0), 45-65: 1.0 (n=1), 65-80: 0.75 (n=4), 80-100: 0.836 (n=67)
- tfidf: 0-45: 0.638 (n=69), 45-65: 1.0 (n=3), 65-80: None (n=0), 80-100: None (n=0)

## Database facts

{
  "distinct_brand_names": 13931,
  "brands_shorter_than_matcher_minimum": 234,
  "share_unmatchable_by_length": 0.0168
}

## Not measured

- sentence_transformers_faiss: not implemented in the repo; the Hugging Face model host was also unreachable from the assessment sandbox
- Real photos: none supplied (pass --images-dir).
- YOLO detector / mAP: no trained weights or detector-labelled images were available; the full-image OCR fallback is what ran.
