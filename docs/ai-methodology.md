# DoubleDose AI — AI Methodology

## 1. Overview

DoubleDose AI is an AI-assisted medicine information application designed to help users inspect medicine ingredients, identify potential ingredient overlaps, and understand medicine information through AI-generated explanations.

The system combines optical character recognition (OCR), information retrieval, semantic similarity, database-backed medicine records, and a large language model (LLM). These components work together to convert medicine-label text or manually selected medicines into structured information that users can review.

The application is intended for **medicine information and preliminary ingredient-overlap checking**. It does not diagnose medical conditions, prescribe treatment, or determine whether a medicine combination is safe for an individual.

## 2. System Architecture

The application uses a modular architecture:

1. **Frontend:** Next.js, React, TypeScript, and Tailwind CSS provide the user interface for medicine search, OCR text review, candidate selection, ingredient-overlap results, and AI explanations.
2. **Backend API:** FastAPI receives frontend requests, validates inputs, coordinates matching and overlap checks, and returns structured responses.
3. **Medicine database:** PostgreSQL, hosted on Neon, stores medicine catalogue records and associated ingredient information.
4. **OCR pipeline:** Tesseract OCR and a configured OCR.space fallback extract text from uploaded medicine images.
5. **Medicine-matching pipeline:** RapidFuzz, TF-IDF, and Sentence Transformers with FAISS support candidate retrieval and ranking.
6. **AI explanation service:** The Groq API provides natural-language explanations based on the structured information supplied by the backend.
7. **Evaluation and tracking:** A custom evaluation script measures medicine-matching performance, while MLflow records experiments and associated metrics.

The system separates medicine identification, ingredient analysis, and natural-language explanation so that an LLM-generated explanation is not treated as the authoritative source of medicine identity.

## 3. Optical Character Recognition (OCR)

### 3.1 Objective

OCR allows users to upload an image of a medicine package or label rather than manually entering all the visible text.

The extracted text may contain medicine names, generic ingredients, strengths, dosage forms, manufacturer names, and other label information.

### 3.2 Processing pipeline

The OCR workflow consists of the following steps:

1. The frontend accepts a supported image format and applies the configured upload-size limit.
2. The backend validates the uploaded file and attempts to process the image.
3. Image preprocessing may use Pillow operations such as orientation correction, contrast enhancement, sharpening, and grayscale conversion.
4. Tesseract OCR extracts text from the processed image.
5. If the primary OCR process does not produce usable text, the configured OCR.space fallback can be used.
6. The extracted text is returned to the frontend for review and editing.
7. The reviewed text is submitted to the medicine-matching endpoint to retrieve possible catalogue matches.

The exact preprocessing and fallback path depends on the input image and the conditions defined in the OCR service.

### 3.3 OCR limitations

OCR quality depends on image resolution, focus, lighting, text orientation, packaging design, font size, and label condition. Medicine names and strengths can be misread, particularly when several ingredients or strengths appear together.

For this reason, OCR output is treated as **unverified text**, not as a confirmed medicine identity. Users can review and edit the extracted text before requesting candidate matches.

## 4. Medicine Matching

Medicine matching attempts to identify catalogue entries that correspond to the text extracted from a label or entered by a user.

DoubleDose AI evaluates three matching approaches:

- RapidFuzz string matching
- TF-IDF text-vector similarity
- Sentence Transformers embeddings with FAISS

These approaches provide different ways of comparing text. Their scores and rankings are useful for retrieving candidates, but they do not independently establish that a medicine has been identified correctly.

### 4.1 RapidFuzz

RapidFuzz uses fuzzy string-similarity algorithms to compare the query with medicine catalogue text.

It is useful when the query contains spelling differences, OCR character errors, partial names, or small textual variations.

**Advantages**

- Effective for approximate string matching.
- Useful for misspelled or partially extracted brand names.
- Does not require a language model to generate embeddings.

**Limitations**

- Performance depends on the selected similarity method and the text being compared.
- Semantically related names may not have strong string similarity.
- Similar-looking brand names can refer to different medicines.

### 4.2 TF-IDF

Term Frequency–Inverse Document Frequency (TF-IDF) represents text using numerical features based on the occurrence and relative importance of terms.

The query is compared with vectorized medicine catalogue documents using a similarity measure. This approach can identify records sharing informative words with the input.

**Advantages**

- Provides a lightweight text-retrieval baseline.
- Emphasizes terms that help distinguish documents.
- Does not require a pretrained semantic embedding model.

**Limitations**

- Relies heavily on overlapping vocabulary.
- May struggle with substantial spelling errors or different wording.
- Does not inherently understand that two differently worded phrases have similar meanings.

### 4.3 Sentence Transformers and FAISS

The semantic matcher uses the Sentence Transformers model:

`sentence-transformers/all-MiniLM-L6-v2`

The model encodes medicine catalogue documents and user queries into dense numerical vectors. The vectors are normalized, and FAISS `IndexFlatIP` performs similarity search using inner products. With normalized vectors, the inner product corresponds to cosine similarity.

The catalogue documents incorporate available medicine attributes, including brand name, generic name, source display name, dosage form, and manufacturer.

The semantic retrieval pipeline works as follows:

1. Build text documents from available medicine records.
2. Encode the catalogue documents into embeddings.
3. Normalize the embeddings and create a FAISS index.
4. Encode the user's query using the same model.
5. Retrieve a pool of similar catalogue records.
6. Apply additional evidence-based ranking adjustments.
7. Return the highest-ranked candidates for user review.

The in-memory catalogue index is cached to avoid rebuilding it for every request. A cache-clearing function is available for use after catalogue changes. The model and index are held in application memory, so cache behavior and memory usage depend on the deployment environment.

#### Evidence-based reranking

The semantic matcher supplements embedding similarity with checks for medicine-specific evidence, including:

- Exact brand-name mentions
- Generic ingredient mentions
- Manufacturer mentions
- Strength matches or mismatches
- Dosage-form matches or mismatches

The ranking score is an internal heuristic. It combines semantic similarity with positive and negative adjustments for matching evidence. It is not a calibrated probability of correct identification.

The implementation also limits the number of candidates returned and marks candidates as requiring confirmation.

#### Important limitations

Semantic similarity can retrieve textually or contextually related medicines that are not the intended product. A high similarity score does not guarantee an exact match, correct strength, or correct dosage form.

The semantic model is a general-purpose sentence embedding model, not a medicine-specific model trained or fine-tuned on a validated pharmaceutical matching dataset.

## 5. Ingredient Overlap Analysis

After users select medicine records, the backend examines the available ingredient information to identify potential overlaps.

The analysis depends on the quality and completeness of the catalogue's generic-name and ingredient data. Combination medicines require particular care because a single product can contain multiple active ingredients.

The application reports potential ingredient overlaps using the available structured medicine records. It can then provide an AI-generated explanation to help users understand the result.

**A reported overlap is not, by itself, proof of a harmful interaction. Likewise, no detected overlap does not prove that taking the selected medicines together is safe.** Clinical interactions can involve mechanisms beyond identical active ingredients, and the result may be incomplete if catalogue data is missing or inaccurate.

Users should consult a qualified pharmacist or healthcare professional before making medicine-use decisions.

## 6. LLM-Powered Explanations

DoubleDose AI uses the Groq API to generate natural-language explanations from structured information supplied by the backend.

The explanation service is intended to make catalogue-based findings easier to understand. Depending on the request and available data, an explanation may describe identified ingredients, potential overlap findings, and relevant limitations.

### Explanation workflow

1. The frontend sends a request to the backend.
2. The backend gathers the relevant medicine and ingredient information.
3. The explanation service constructs a request using that structured context.
4. The Groq API generates a natural-language response.
5. The backend returns the explanation to the frontend for display.

The language model is used for explanation, not as the sole mechanism for identifying medicines or determining ingredient overlap.

### Limitations and safeguards

LLMs can produce inaccurate statements, omit relevant details, or express uncertainty inadequately. Their output may also be affected by incomplete catalogue records or ambiguous medicine names.

Therefore:

- Medicine identity should be confirmed against the catalogue and product label.
- Structured ingredient data should remain the basis of overlap detection.
- AI-generated text should not replace the underlying structured result.
- Users should not interpret an explanation as a diagnosis, prescription, or guarantee of safety.
- Clinical decisions should be reviewed with a qualified healthcare professional.

## 7. Medicine-Matching Evaluation

### 7.1 Evaluation objective

The evaluation script compares the ranking performance of RapidFuzz, TF-IDF, and semantic FAISS matching.

The current evaluation uses five manually prepared, clean-text test cases. The expected medicine record for each case is used as the reference when calculating ranking metrics.

The latest recorded run produced the following results:

| Metric                            | RapidFuzz | TF-IDF | Semantic FAISS |
| --------------------------------- | --------: | -----: | -------------: |
| Evaluation cases                  |         5 |      5 |              5 |
| Top-1 accuracy                    |       80% |    80% |           100% |
| Top-3 accuracy                    |      100% |   100% |           100% |
| Mean reciprocal rank at 3 (MRR@3) |      0.90 |   0.90 |           1.00 |
| No-candidate rate                 |        0% |     0% |             0% |
| Mean time per query               |    5.65 s | 5.62 s |         0.38 s |

_These are measurements from one evaluation run, not guaranteed production performance. Query latency varies with the execution environment, model loading, caching, and other runtime conditions._

### 7.2 Evaluation metrics

**Top-1 accuracy:** The proportion of test cases for which the expected medicine appears in the first-ranked position.

**Top-3 accuracy:** The proportion of test cases for which the expected medicine appears within the first three results.

**Mean reciprocal rank at 3 (MRR@3):** The average reciprocal rank of the expected medicine when it appears within the first three results. A higher value indicates that the expected result tends to appear nearer the top.

**No-candidate rate:** The proportion of evaluation cases for which the matcher returns no candidates.

**Mean time per query:** The average measured time required to process an evaluation query in the recorded run. It is an environment-specific measurement, not a formal production latency benchmark.

### 7.3 Interpretation

In the latest recorded run, semantic FAISS achieved 100% top-1 accuracy on the five evaluation cases, while RapidFuzz and TF-IDF each achieved 80%. All three approaches achieved 100% top-3 accuracy.

These results indicate that the semantic matcher performed well on this small test set. However, five cases are insufficient to establish general superiority or reliable real-world accuracy.

For a five-case sample, the approximate 95% Wilson confidence intervals for top-1 accuracy are:

- RapidFuzz: 37.6%–96.4%
- TF-IDF: 37.6%–96.4%
- Semantic FAISS: 56.6%–100%

The wide intervals reflect the small sample size. The evaluation uses clean, manually prepared text rather than a representative collection of real medicine-package photographs and OCR errors. It therefore does not measure end-to-end accuracy from image upload through final medicine confirmation.

The reported results should be treated as **preliminary experimental findings**, not as a clinical validation or a claim of production-level accuracy.

### 7.4 Reproducibility

From the backend directory, run:

```bash
python -m scripts.evaluate_medicine_matchers
```

The evaluation script writes reports to:

- `backend/evaluation/results/matcher_report.md`
- `backend/evaluation/results/matcher_report.json`

It also logs experiment information through MLflow using the configured local tracking setup.

The generated reports should be used as the source of truth when documenting subsequent evaluation runs.

## 8. MLflow Experiment Tracking

MLflow is used to record medicine-matching evaluation runs and their associated metrics.

Experiment tracking helps compare approaches, retain evaluation history, and make changes easier to inspect. It does not independently validate the correctness of a matcher or the clinical safety of an ingredient-overlap result.

The current tracking configuration uses a local SQLite-backed MLflow store. The database and artifacts are environment-dependent and should be managed appropriately if experiments are moved to another machine or deployment environment.

## 9. Data Sources and Data Quality

The medicine catalogue was populated using a dataset of Bangladeshi medicines from Hugging Face:

`Mahadih534/all-Bangladeshi-medicines`

The imported dataset contains medicine attributes such as brand name, generic name, dosage form, manufacturer, and source display information. The catalogue also uses available ingredient mappings and identifiers from integrated medicine-data sources where applicable.

Data quality is a central limitation of the system. Catalogue records can be incomplete, inconsistent, outdated, or ambiguous. Brand names may be similar, and different products may have different strengths or formulations.

The application should therefore present candidate results for confirmation rather than assuming that a text match is definitive. Catalogue updates and improved ingredient normalization are important areas for future work.

## 10. Security, Reliability, and Safety Considerations

The system should be operated with the following principles:

- Validate uploaded files and API inputs.
- Keep API credentials and other secrets in environment variables rather than source code.
- Avoid logging sensitive user information unnecessarily.
- Treat OCR text and medicine matches as potentially incorrect.
- Keep user confirmation in the medicine-identification workflow.
- Display AI-generated explanations as informational assistance.
- Make the limitations of ingredient-overlap checks clear to users.

The application is an informational prototype and should not be used as the sole basis for medication decisions.

## 11. Current Limitations

The current implementation has several limitations:

1. **Small evaluation dataset:** The matching benchmark contains only five manually prepared text cases.
2. **No representative real-image benchmark:** The reported metrics do not establish OCR accuracy or end-to-end medicine identification accuracy on real packaging photographs.
3. **No clinical validation:** The system has not been established as a clinically validated medicine-interaction checker.
4. **Catalogue dependency:** Missing or incorrect medicine and ingredient records can affect the results.
5. **Heuristic reranking:** Ranking adjustments are manually defined and are not calibrated probabilities.
6. **General-purpose embeddings:** The semantic model is not specifically fine-tuned for pharmaceutical entity resolution.
7. **LLM uncertainty:** AI explanations can contain errors or omissions.
8. **Runtime variability:** Model initialization, caching, and deployment resources can change latency and memory consumption.
9. **No validated YOLO detector metrics:** The project does not claim a trained YOLO medicine detector or measured YOLO mAP results.

## 12. Future Improvements

Potential improvements include:

- Expand the evaluation set with verified brand names, generic names, strengths, combination medicines, and dosage forms.
- Add representative real-world medicine-label images and evaluate OCR and matching separately.
- Report top-k metrics with confidence intervals on a larger, held-out dataset.
- Measure end-to-end latency separately from model-loading and cache initialization time.
- Improve ingredient normalization and catalogue deduplication.
- Add stronger validation of strength, dosage form, and combination-ingredient matches.
- Evaluate semantic retrieval and reranking on difficult negative examples.
- Improve explanation grounding and make uncertain or incomplete source data more visible.
- Add monitoring for API errors, OCR failures, and matching quality.
- Seek appropriate domain-expert review before making any clinical claims.

## 13. Conclusion

DoubleDose AI combines OCR, catalogue-based retrieval, fuzzy matching, TF-IDF, semantic embeddings, structured ingredient analysis, and LLM-generated explanations in one application.

The initial five-case evaluation provides a useful starting point for comparing the implemented medicine-matching approaches, but it is too small to support broad accuracy claims. The system therefore emphasizes candidate review, structured data, and clear safety limitations.

Further work should focus on larger and more representative evaluations, stronger medicine-data quality, and appropriate expert validation before the application is used for higher-stakes healthcare decisions.