# Matcher benchmark

Seed: 42. Sources run: legacy_manual.

## legacy_manual

5 hand-typed clean cases. Too small to generalise.

| Matcher | Cases | Top-1 (95% CI) | Top-3 (95% CI) | MRR@3 | No candidate | s/query |
|---|---|---|---|---|---|---|
| rapidfuzz | 5 | 0.8 [0.376, 0.964] | 1.0 [0.566, 1.0] | 0.9 | 0.0 | 4.0 |
| tfidf | 5 | 0.8 [0.376, 0.964] | 1.0 [0.566, 1.0] | 0.9 | 0.0 | 3.92 |

| Group | rapidfuzz top-1 / top-3 | tfidf top-1 / top-3 |
|---|---|---|
| clean | 0.8 / 1.0 (n=5) | 0.8 / 1.0 (n=5) |

Top-1 precision by top-1 score (is the score a usable confidence?):

- rapidfuzz: 0-45: None (n=0), 45-65: None (n=0), 65-80: None (n=0), 80-100: 0.8 (n=5)
- tfidf: 0-45: 1.0 (n=3), 45-65: 0.5 (n=2), 65-80: None (n=0), 80-100: None (n=0)

## Not measured

- sentence_transformers_faiss: not implemented in the repo; the Hugging Face model host was also unreachable from the assessment sandbox
- Real photos: none supplied (pass --images-dir).
- YOLO detector / mAP: no trained weights or detector-labelled images were available; the full-image OCR fallback is what ran.
