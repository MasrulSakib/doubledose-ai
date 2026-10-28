# DoubleDose AI — AI Methodology

## 1. Overview

DoubleDose AI combines optical character recognition (OCR), medicine-candidate retrieval, ingredient comparison, and large language model (LLM) explanations to help users inspect medicine information.

The workflow separates candidate identification from ingredient comparison and AI-generated explanations. This distinction is important because a similarity score does not prove medicine identity, and an AI-generated explanation does not independently verify clinical facts.

## 2. OCR Pipeline

The OCR workflow extracts text from uploaded medicine-package images.

### Processing steps

1. The user uploads an image of a medicine strip or box.
2. The backend processes the image and attempts text extraction.
3. The OCR workflow uses Tesseract OCR where available and supports OCR.space as a fallback.
4. Extracted text is returned to the frontend for review.
5. The user can correct recognition errors before requesting medicine candidates.

OCR output may contain misspelled brand names, merged words, incorrect strengths, or unrelated packaging text. The application therefore treats extracted text as an input for candidate retrieval rather than as verified medicine information.

A separately trained YOLO detector is not claimed as part of the current implementation.

## 3. Medicine-Matching Methods

The system supports three approaches to retrieving medicine candidates.

### 3.1 RapidFuzz

RapidFuzz compares text using fuzzy string-matching techniques. It is useful when the input contains minor spelling errors or differences in text formatting.

**Role:** Retrieve candidate medicine products from noisy or imperfect text.

**Limitation:** Similar brand names can produce misleading matches, and fuzzy similarity alone does not establish pharmaceutical equivalence.

### 3.2 TF-IDF with Character N-grams

The TF-IDF approach represents text using character n-gram features and compares the resulting vectors. Character-level features can help match partially corrupted words and textual variations.

**Role:** Provide a lexical matching baseline for medicine-candidate retrieval.

**Limitation:** Similar text does not guarantee identical active ingredients, strength, or dosage form.

### 3.3 Sentence Transformers and FAISS

The semantic-matching service encodes medicine descriptions using a Sentence Transformers model. FAISS indexes the resulting vectors and retrieves candidates using vector similarity search.

Catalogue descriptions can include available brand names, generic ingredients, product display information, dosage forms, and manufacturer details.

**Role:** Retrieve semantically similar candidates that may have less direct lexical overlap with the query.

**Limitation:** Embeddings may rank related but incorrect products highly. Semantic similarity does not verify medicine identity or clinical equivalence.

### 3.4 Candidate Reranking and Confirmation

The system can rerank retrieved candidates using available evidence such as:

- Brand-name matches
- Generic ingredient matches
- Strength matches or mismatches
- Dosage-form matches or mismatches
- Manufacturer information
- Semantic similarity

These signals influence candidate ordering. The resulting scores are not calibrated probabilities of correctness.

Users must review and confirm the intended medicine before using it in a comparison. The matching system assists identification; it does not replace verification against the actual packaging or a qualified professional's advice.

## 4. Ingredient-Overlap Analysis

Ingredient comparison is performed using the active-ingredient records associated with the selected medicine products in the database.

At a high level, the backend:

1. Receives the selected medicine records.
2. Retrieves their recorded active-ingredient links.
3. Compares the ingredient sets.
4. Identifies shared recorded ingredients.
5. Reports relevant incomplete-data warnings and applicable same-class warnings.

This comparison is deterministic with respect to the stored data and implemented rules. However, the result is only as reliable as the ingredient mappings supplied to it.

A missing ingredient link can cause the system to miss an overlap. A medicine with at least one ingredient link may also have incomplete ingredient information. The application therefore must not interpret an absence of detected overlap as proof that a combination is safe.

Ingredient overlap is not a comprehensive drug-interaction assessment. The application does not account for every patient-specific factor or every possible medication interaction.

## 5. LLM-Generated Explanations

The application uses the Groq API to generate explanatory text about comparison results.

The LLM provides a natural-language explanation layer on top of the application's data-based analysis. It does not replace the database comparison or
