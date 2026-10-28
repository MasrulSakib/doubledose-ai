# DoubleDose AI

DoubleDose AI is an AI-assisted medicine information and ingredient comparison platform focused on Bangladeshi medicine products. It combines optical character recognition (OCR), multiple medicine-matching approaches, active ingredient comparison, and AI-generated explanations in a single web application.

The project aims to help users identify potential duplicate active ingredients and understand medicine information before discussing their medicines with a pharmacist or other qualified healthcare professional.

> **Important:** DoubleDose AI is an educational prototype, not a medical diagnosis, prescribing, or clinically validated decision-support tool. A result showing no shared ingredients does not establish that a medicine combination is safe.

## Features

- **Medicine search:** Search a catalogue of Bangladeshi medicine products.
- **Medicine label OCR:** Upload medicine packaging images to extract text using OCR, with image preprocessing and fallback support.
- **OCR text correction:** Review and edit extracted text before searching for matching medicines.
- **Multiple medicine-matching approaches:** Generate candidate matches using RapidFuzz, TF-IDF, and semantic similarity with Sentence Transformers and FAISS.
- **Candidate reranking:** Use available brand names, generic ingredients, strengths, dosage forms, and manufacturer information to improve candidate ordering.
- **Match confirmation:** Review candidate products before adding them to the comparison.
- **Ingredient comparison:** Identify shared recorded active ingredients among selected medicines.
- **Incomplete-data warnings:** Highlight medicines with missing ingredient links and communicate limitations in the available catalogue data.
- **AI-generated explanations:** Generate additional explanations of ingredient overlap through the Groq API.
- **Drug-label references:** Retrieve available reference information through the openFDA API.
- **Same-class warnings:** Present possible therapeutic-class duplication separately from exact ingredient overlap when applicable.
- **Evaluation tools:** Evaluate medicine-matching approaches and ingredient-overlap behavior using project scripts and reports.

## Technology Stack

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Redux Toolkit

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL hosted on Neon

### AI and Data Processing

- **OCR:** Tesseract OCR and an OCR.space fallback for text extraction.
- **Image processing:** Pillow and OpenCV for image preprocessing.
- **RapidFuzz:** Fuzzy string matching for candidate retrieval.
- **scikit-learn TF-IDF:** Character n-gram similarity for medicine-name matching.
- **Sentence Transformers:** Text embeddings for semantic medicine matching.
- **FAISS:** Vector similarity search over the medicine catalogue.
- **Groq API:** AI-generated explanations.
- **openFDA API:** External drug-label reference information.
- **Bangladeshi medicine dataset:** Initial medicine catalogue and ingredient-mapping source.
- **MLflow:** Experiment tracking for supported matcher evaluation workflows.

## System Architecture

```text
                         User
                           |
                           v
                    Next.js Frontend
                           |
             +-------------+-------------+
             |                           |
             v                           v
       Medicine Search             Image Upload
             |                           |
             |                           v
             |                      FastAPI OCR
             |                           |
             |                  OCR / Image Processing
             |                           |
             |                           v
             |                    Extracted Text
             |                           |
             |             +-------------+-------------+
             |             |             |             |
             |             v             v             v
             |         RapidFuzz      TF-IDF     Semantic Matching
             |                                      (Embeddings
             |                                       + FAISS)
             |             |             |             |
             |             +-------------+-------------+
             |                           |
             |                           v
             |                    Ranked Candidates
             |                           |
             +---------------------------+
                                         |
                                         v
                                 User Confirmation
                                         |
                                         v
                                  Medicine Selection
                                         |
                                         v
                                   FastAPI Backend
                                         |
                                         v
                                  PostgreSQL / Neon
                                         |
                                         v
                                Ingredient Comparison
                                         |
                     +-------------------+-------------------+
                     |                   |                   |
                     v                   v                   v
                Ingredient          Incomplete-Data     Same-Class
                  Overlap              Warnings          Warnings
                     |                   |                   |
                     +-------------------+-------------------+
                                         |
                                         v
                               Groq / Reference Data
                                         |
                                         v
                                Results and Explanation
```

The frontend, backend API, and database are separate components. OCR and medicine matching generate candidate products; the user must review and confirm the intended medicine. Ingredient comparison relies on the ingredient records available in the database.

The semantic matcher complements string-based approaches by comparing text embeddings. It does not independently verify a medicine's identity, ingredients, or clinical equivalence.

AI-generated explanations provide additional context and should not be treated as verified medical advice.

## How It Works

1. Search for a medicine or upload an image of its packaging.
2. Extract text from the image using the available OCR service.
3. Review and, if necessary, correct the extracted text.
4. Generate medicine candidates using the available matching approaches.
5. Review and confirm the correct product.
6. Select medicines for comparison, subject to the application's selection limit.
7. Review shared recorded ingredients, possible same-class warnings, and incomplete-data notices.
8. Read the AI-generated explanation and any available reference information.
9. Verify the results with a qualified healthcare professional before making medication decisions.

## Medicine Matching

DoubleDose AI supports three complementary matching approaches.

| Approach          | Method                                        | Purpose                                                          |
| ----------------- | --------------------------------------------- | ---------------------------------------------------------------- |
| RapidFuzz         | Fuzzy string similarity                       | Finds candidates despite spelling differences and imperfect text |
| TF-IDF            | Character n-gram vectorization and similarity | Compares medicine-name patterns                                  |
| Semantic matching | Sentence Transformer embeddings and FAISS     | Retrieves candidates based on semantic similarity                |

The system can rerank candidates using available product information, including brand name, generic ingredients, strength, dosage form, and manufacturer.

The approaches have different strengths. Fuzzy matching can perform well on recognizable product names, while semantic matching can retrieve related descriptions with less direct lexical overlap. Neither approach guarantees that the highest-ranked result is the correct product.

**Candidate scores are ranking signals, not calibrated probabilities of correctness.** OCR errors, missing catalogue fields, combination products, and similar brand names can affect the results. Users must confirm candidate identities before comparison.

## Evaluation

The repository includes scripts and reports for evaluating medicine matching and ingredient-overlap behavior.

### Medicine-Matching Evaluation

The matcher evaluation workflow compares approaches using manually prepared medicine-identification queries. One recorded evaluation run reported the following results:

| Metric                     | RapidFuzz | TF-IDF |
| -------------------------- | --------: | -----: |
| Top-1 accuracy             |      100% |    40% |
| Top-3 accuracy             |      100% |    60% |
| Mean reciprocal rank (MRR) |      1.00 |   0.50 |
| Evaluation cases           |         5 |      5 |

These figures describe that particular five-case evaluation run; they should not be interpreted as stable estimates of performance across the full medicine catalogue.

The repository's evaluation scripts and generated outputs are the source of truth for reproducing or updating the results. Different query sets, catalogue states, or evaluation runs may produce different metrics.

**Evaluation limitations:**

- The benchmark is small and uses manually prepared queries.
- It does not establish accuracy on real-world medicine packaging images or noisy OCR output.
- Results may vary with catalogue coverage, preprocessing, and the matching configuration.
- A high score does not establish pharmaceutical equivalence or clinical correctness.
- The recorded results should be refreshed whenever the evaluation dataset or matcher implementation changes.

### Ingredient-Overlap Assessment

The project includes an ingredient-overlap assessment covering 10 evaluation cases in the documented assessment workflow.

Consult `backend/evaluation/results/` for the available generated reports and recorded metrics, including true positives, false positives, false negatives, precision, recall, and F1 score where reported.

These evaluations assess implementation behavior on the tested cases. They do not establish clinical validity, complete ingredient coverage, or the ability to detect every possible medication interaction.

## Data Coverage and Limitations

The application uses a medicine catalogue assembled from a Bangladeshi medicine product dataset and associated ingredient mappings.

Catalogue size and ingredient-link coverage can change as data is imported, corrected, or updated. Consult the current database coverage report or generated evaluation artifacts for the latest verified figures rather than assuming that the catalogue is complete.

Important distinctions:

- A medicine having at least one ingredient link does not mean every active ingredient has been recorded correctly.
- Combination products may have incomplete ingredient mappings.
- Ingredient amounts and strength-level details may be missing.
- Similar brand names do not necessarily represent the same medicine.
- Missing ingredient data can cause the application to miss a potential overlap.
- The system's overlap analysis is not a comprehensive drug-interaction checker.

The application can warn when a medicine has no recorded ingredient links. However, a medicine with at least one link may still have incomplete information. Therefore, an overlap result can be incomplete even when the system finds a shared ingredient.

## Project Structure

```text
doubledose-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── evaluation/
│   │   └── results/
│   ├── scripts/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   └── types/
├── docs/
│   ├── ai-methodology.md
│   ├── user-guide.md
│   ├── production-smoke-test.md
│   └── images/
├── LICENSE
└── README.md
```

This is a high-level structure; individual files and folders may differ as the project evolves.

## Live Deployment

- **Frontend:** [https://doubledose-ai.vercel.app](https://doubledose-ai.vercel.app)
- **Backend API:** [https://doubledose-ai-api.onrender.com](https://doubledose-ai-api.onrender.com)
- **API documentation:** [https://doubledose-ai-api.onrender.com/docs](https://doubledose-ai-api.onrender.com/docs)

The backend exposes API endpoints for the implemented medicine search, ingredient comparison, AI explanations, OCR extraction, and medicine matching workflows. Consult the deployed OpenAPI documentation for the currently available endpoints and request schemas.

Deployment availability and third-party service limits may affect the application.

## Running Locally

The frontend and backend run as separate applications.

### Prerequisites

- Python and pip
- Node.js and npm
- A Neon PostgreSQL database or compatible PostgreSQL instance
- A Groq API key for AI-generated explanations
- An OCR.space API key if using the hosted OCR fallback locally
- Tesseract OCR installed if using local Tesseract OCR

### 1. Backend Setup

Open PowerShell in the `backend` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure the environment variables expected by the backend. These may include:

- Database connection settings
- Groq API key and model configuration
- OCR.space API key
- Semantic-matching configuration, if enabled

Use the actual variable names defined in the application's settings and service files. Do not commit secrets or production credentials to source control.

If the application uses Alembic migrations, apply the repository's migrations to the configured database before starting the API.

Start the FastAPI server:

```powershell
uvicorn main:app --reload
```

Local API:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

### 2. Frontend Setup

Open a separate terminal in the `frontend` directory:

```powershell
npm install
npm run dev
```

Configure the frontend's backend API URL using the environment variable expected by the application. For the deployed frontend, this should point to the deployed backend API.

Open:

`http://localhost:3000`

Use the package manager and lockfile already present in the repository if they differ from these examples.

### Optional Local OCR and Semantic Matching

Local Tesseract OCR requires the Tesseract executable to be installed and discoverable by the application, or explicitly configured in its settings.

Semantic matching requires the relevant Python dependencies and a compatible Sentence Transformer model. The model may need to be downloaded the first time it is loaded. If semantic matching is disabled or unavailable, the application may fall back to another supported matching approach.

## Responsible Use and Safety

DoubleDose AI does not replace a pharmacist, physician, or other qualified healthcare professional.

- OCR may misread medicine names, ingredients, and strengths.
- A matching result is a candidate, not proof of product equivalence.
- Incomplete ingredient mappings can cause missed overlaps.
- Shared ingredients are only one consideration in medication safety.
- The absence of shared recorded ingredients does not establish that a combination is safe.
- Therapeutic-class warnings are informational and may not capture every relevant medicine relationship.
- AI-generated explanations may contain inaccurate or incomplete information.
- External openFDA information may describe US-market products and may not apply directly to medicines sold in Bangladesh.
- The project has not been clinically validated as a medical device.

Always verify medicine information against the actual packaging and consult a qualified healthcare professional before combining medicines, changing medication, or making treatment decisions.

## Additional Documentation

- [AI Methodology](docs/ai-methodology.md) — describes the OCR pipeline, medicine-matching approaches, ingredient comparison, AI integration, evaluation, and limitations.
- [User Guide](docs/user-guide.md) — explains how to use the application.
- [Production Smoke Test Report](docs/production-smoke-test.md) — documents production functionality checks.

### Application Screenshots

Store screenshots captured from the actual application in `docs/images/`. Add or update these files before linking to them in the README.

Suggested screenshots:

- `docs/images/medicine-search.png`
- `docs/images/ocr-candidates.png`
- `docs/images/ingredient-overlap.png`
- `docs/images/ai-explanation.png`

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
