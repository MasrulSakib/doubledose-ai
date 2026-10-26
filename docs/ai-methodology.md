# DoubleDose AI — AI Methodology

## 1. Overview

DoubleDose AI is an AI-assisted medicine information application focused on medicine products in Bangladesh. Its workflow combines optical character recognition (OCR), text-based medicine matching, ingredient-record comparison, and AI-generated explanations.

The system helps users identify possible shared active ingredients among selected medicines. It is an informational tool and has not been clinically validated as a medical device.

## 2. OCR and Image Processing

The application accepts medicine-package images and extracts text using Tesseract OCR. Image processing and fallback extraction are used to improve the availability of text from uploaded images.

OCR output can contain spelling errors, incomplete words, or incorrect readings of brand names and strengths. Therefore, extracted text is treated as an input for candidate retrieval rather than a verified medicine identity.

The application returns candidate medicines for the user to review and confirm.

## 3. Medicine Matching

The evaluated implementation compares two text-matching approaches.

### RapidFuzz

RapidFuzz performs fuzzy string matching to retrieve medicine candidates when the OCR text or search text is not an exact match for the database name. This helps accommodate spelling differences and imperfect text extraction.

### TF-IDF

The TF-IDF approach uses character n-gram text features and similarity scoring to retrieve and rank medicine candidates. Character-level features can help identify partially matching names despite some textual differences.

### Candidate ranking and confirmation

The implementation also considers available evidence such as brand-name matches, medicine strength, and dosage form when ranking candidates. Ranking scores are not calibrated probabilities of correctness. The user must review and confirm the intended medicine.

A sentence-transformer and FAISS-based matcher is not implemented in the evaluated pipeline.

## 4. Ingredient-Overlap Analysis

After the user selects medicines, the backend compares the active-ingredient records available in the database.

The system reports recorded shared ingredients and identifies medicines for which ingredient data is unavailable. It can also present possible therapeutic-class duplication separately from exact ingredient overlap when applicable.

The result depends on the completeness and correctness of the stored ingredient mappings. A medicine with at least one ingredient link may still have incomplete ingredient information.

Ingredient-overlap analysis does not assess every possible drug interaction, determine appropriate doses, or establish whether a combination is safe for an individual.

## 5. AI-Generated Explanations

DoubleDose AI uses the Groq API to generate natural-language explanations of ingredient-overlap results.

The AI explanation is an additional interpretation layer. It does not replace the database comparison, independently verify medicine identities, or establish clinical safety.

AI-generated content may be incomplete or inaccurate. The application handles unavailable AI services by displaying an appropriate error or fallback message.

## 6. External Reference Information

The application can retrieve available drug-label reference information through the openFDA API. Such references may describe products marketed in the United States and may not directly apply to every medicine sold in Bangladesh.

## 7. Evaluation

### Medicine matching

The latest recorded manual benchmark used five hand-typed medicine identification cases.

| Metric                    |    RapidFuzz |       TF-IDF |
| ------------------------- | -----------: | -----------: |
| Top-1 accuracy            |          80% |          80% |
| Top-3 accuracy            |         100% |         100% |
| Mean reciprocal rank at 3 |         0.90 |         0.90 |
| No-candidate rate         |           0% |           0% |
| Mean time per query       | 4.00 seconds | 3.92 seconds |
| Evaluation cases          |            5 |            5 |

This small benchmark does not establish performance on real medicine photographs or noisy OCR output. Query times depend on the execution environment.

### Ingredient-overlap regression assessment

The recorded developer regression assessment covered 10 cases. The report recorded 100% precision, recall, F1, and result-status accuracy for the evaluated cases.

These expected labels were reconstructed using source identifiers and current database mappings. They are provisional and have not been independently verified by a pharmacist. The assessment is not representative clinical validation.

### Data coverage

The current data-coverage report records 21,721 medicine records, of which 20,485 have at least one ingredient link. This corresponds to 94.31% ingredient-link coverage. The report records 1,236 medicines without ingredient links and only three ingredient links with recorded amounts.

Ingredient-link coverage must not be interpreted as proof that all ingredient mappings are complete or verified.

## 8. Limitations and Future Work

- Evaluate OCR and matching on a larger set of real medicine-package photographs.
- Measure top-1 and top-k retrieval performance using independently labelled examples.
- Review medicine and ingredient mappings with qualified domain experts.
- Improve the completeness of ingredient names, strengths, and amounts.
- Calibrate candidate confidence only after collecting a sufficiently representative evaluation dataset.
- Evaluate additional matching approaches only when they can be implemented and compared fairly.
- Continue improving error handling and the clarity of safety warnings.

## 9. Responsible Use

DoubleDose AI is not a diagnostic, prescribing, or clinical decision-support tool. Users should verify medicine names against the actual packaging and consult a qualified pharmacist or healthcare professional before making medication decisions.
