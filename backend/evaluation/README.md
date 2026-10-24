# Evaluation

Evaluation reports measure development-stage performance for DoubleDose AI's medicine overlap checker, medicine matcher, and OCR pipeline.

The original overlap and data-coverage evaluations used a local SQLite copy built from `data/medicine.csv` (21,714 products, using the same import script as production). The reconstructed overlap evaluation uses the current database mappings and a separate, small regression dataset.

## Reproduce

Run these commands from `backend/`:

```bash
export DATABASE_URL=sqlite:///local.db
# Or use your Neon database URL for read-only evaluation.

python -c "from app.db.session import engine; from app.db.base import Base; import app.models; Base.metadata.create_all(engine)"

# Only for a fresh local database:
python -m scripts.import_bd_medicines --apply

# Historical/default overlap evaluation:
python -m scripts.evaluate_overlap

# Reconstructed preliminary regression evaluation:
python -m scripts.evaluate_overlap \
  --cases evaluation/overlap_cases_reconstructed.json \
  --out-dir evaluation/results/reconstructed

python -m scripts.report_data_coverage
python -m scripts.evaluate_medicine_matchers --synthetic 50 --mlflow-uri sqlite:///mlflow.db
python -m scripts.evaluate_medicine_matchers --synthetic-images 24 --no-mlflow
python -m pytest -q tests
```

Use a disposable local database when importing data or creating tables. Do not run import or schema-changing commands against production unless intended.

## What each result means

| Result                                           | Evidence type                                                                                                                                                                 | Report                                                                                 |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Historical overlap precision/recall/F1           | 36 hand-labelled combinations from real records. Labels were not pharmacist-verified. Cases were selected to expose known failures, so results are not a population estimate. | `results/overlap_report.md`, `results/overlap_report_before_fix.md`                    |
| Reconstructed overlap regression                 | 10 preliminary cases using verified BDDrugBank source IDs and current database mappings. Expected labels are provisional and not pharmacist-verified.                         | `results/reconstructed/overlap_report.md`, `results/reconstructed/overlap_report.json` |
| Share of missed medicine pairs                   | Counted over the database using the normaliser as the reference. This is not an independently validated ground truth.                                                         | `results/data_coverage.json`                                                           |
| Matcher top-1/top-3/MRR on noisy text            | Synthetic OCR-style noise applied to real database records (300 cases in the recorded evaluation).                                                                            | `results/matcher_report_synthetic_text.md`                                             |
| Matcher accuracy through Tesseract               | Synthetic labels rendered in a clean font, degraded, then processed by the real OCR pipeline (72 images in the recorded evaluation).                                          | `results/matcher_report_synthetic_images.md`                                           |
| Real-photo accuracy, YOLO mAP, embedding matcher | Not measured; no real-photo evaluation set or usable trained detector weights were available.                                                                                 | Not available                                                                          |

## Interpreting the reconstructed overlap results

The reconstructed regression run evaluated 10 cases and reported:

- Combination-level precision, recall, and F1: **1.00**
- Ingredient-level precision, recall, and F1: **1.00**
- Result-status accuracy: **1.00**
- Request-order preservation: **10/10**
- Reported failures: **0**

These results show that the implementation passed this small regression set. They do **not** establish general clinical accuracy, dataset-wide correctness, or patient safety. The test cases are limited, and their expected labels have not been independently verified by a pharmacist.

Ingredient coverage also requires careful interpretation: a medicine with at least one mapped ingredient may still have incomplete ingredient data.

## Evaluating with real photos

To evaluate real medicine photos, place the images in a folder and create a `labels.csv` file with these columns:

```csv
image_file,expected_brand
example.jpg,Example Brand
```

Run:

```bash
python -m scripts.evaluate_medicine_matchers --images-dir <folder>
```

The report can then include a `real_photo` section split into `detector` and `full_image_fallback`, depending on the evaluation script's available pipeline paths.

## Limitations

- Overlap labels have not been independently verified by a pharmacist.
- The reconstructed overlap dataset is a small developer regression set, not a representative clinical validation study.
- Database ingredient mappings can be missing or incomplete.
- Synthetic OCR performance may not reflect real-world photographs, including glare, blur, perspective distortion, packaging variation, and low lighting.
- Real-photo detector performance and embedding-matcher performance have not been established.
- DoubleDose AI is a decision-support prototype, not a substitute for professional medical advice or pharmacist review.
