# Matcher benchmark

Seed: 42. Sources run: legacy_manual, synthetic_text.

## legacy_manual

5 hand-typed clean cases. Too small to generalise.

| Matcher | Cases | Top-1 (95% CI) | Top-3 (95% CI) | MRR@3 | No candidate | s/query |
|---|---|---|---|---|---|---|
| rapidfuzz | 5 | 0.8 [0.376, 0.964] | 1.0 [0.566, 1.0] | 0.9 | 0.0 | 1.43 |
| tfidf | 5 | 0.4 [0.118, 0.769] | 0.6 [0.231, 0.882] | 0.5 | 0.0 | 0.76 |

| Group | rapidfuzz top-1 / top-3 | tfidf top-1 / top-3 |
|---|---|---|
| clean | 0.8 / 1.0 (n=5) | 0.4 / 0.6 (n=5) |

Top-1 precision by top-1 score (is the score a usable confidence?):

- rapidfuzz: 0-45: None (n=0), 45-65: None (n=0), 65-80: None (n=0), 80-100: 0.8 (n=5)
- tfidf: 0-45: 0.5 (n=2), 45-65: 0.333 (n=3), 65-80: None (n=0), 80-100: None (n=0)

## synthetic_text

Noisy text generated from real database records. A stress test, not real OCR.

| Matcher | Cases | Top-1 (95% CI) | Top-3 (95% CI) | MRR@3 | No candidate | s/query |
|---|---|---|---|---|---|---|
| rapidfuzz | 300 | 0.777 [0.726, 0.82] | 0.913 [0.876, 0.94] | 0.838 | 0.033 | 1.67 |
| tfidf | 300 | 0.597 [0.54, 0.651] | 0.69 [0.636, 0.74] | 0.641 | 0.113 | 0.67 |

| Group | rapidfuzz top-1 / top-3 | tfidf top-1 / top-3 |
|---|---|---|
| brand_generic/high | 0.54 / 0.78 (n=50) | 0.36 / 0.38 (n=50) |
| brand_generic/low | 0.76 / 0.98 (n=50) | 0.64 / 0.84 (n=50) |
| brand_generic/medium | 0.72 / 0.92 (n=50) | 0.48 / 0.58 (n=50) |
| brand_only/high | 0.74 / 0.82 (n=50) | 0.5 / 0.54 (n=50) |
| brand_only/low | 1.0 / 1.0 (n=50) | 0.88 / 0.94 (n=50) |
| brand_only/medium | 0.9 / 0.98 (n=50) | 0.72 / 0.86 (n=50) |

Top-1 precision by top-1 score (is the score a usable confidence?):

- rapidfuzz: 0-45: None (n=0), 45-65: 0.707 (n=75), 65-80: 0.863 (n=153), 80-100: 0.774 (n=62)
- tfidf: 0-45: 0.584 (n=185), 45-65: 0.87 (n=77), 65-80: 1.0 (n=4), 80-100: None (n=0)

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
