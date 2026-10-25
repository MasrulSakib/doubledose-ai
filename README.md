# DoubleDose AI

DoubleDose AI is an AI-assisted medicine information and ingredient comparison platform designed around Bangladeshi medicine products. It combines optical character recognition (OCR), fuzzy medicine matching, active ingredient comparison, and AI-generated explanations in a single web application.

The project aims to make medicine information easier to understand and help users identify potential duplicate active ingredients before discussing their medicines with a pharmacist or other qualified healthcare professional.

> **Important:** DoubleDose AI is an informational project, not a medical diagnosis, prescribing, or clinical decision-support tool. A result showing no shared ingredients does not establish that a medicine combination is safe.

## Features

- **Medicine search:** Search a database of Bangladeshi medicine products.
- **Medicine label OCR:** Upload medicine packaging images to extract text using Tesseract OCR, with image-processing and fallback support.
- **Fuzzy medicine matching:** Generate candidate medicine matches using RapidFuzz and TF-IDF approaches.
- **Candidate ranking:** Use recognized brand names, strengths, and dosage forms to help rank candidate matches.
- **Match confirmation:** Review and confirm candidate medicines before adding them to the comparison.
- **Ingredient comparison:** Compare selected medicines for shared recorded active ingredients.
- **Incomplete-data warnings:** Identify selected medicines without recorded ingredient links.
- **AI-generated explanations:** Generate explanations of ingredient overlap using the Groq API.
- **Drug-label references:** Retrieve available reference information through the openFDA API.
- **Same-class warnings:** Present possible therapeutic-class duplication separately from exact ingredient overlap, when applicable.
- **Evaluation tools:** Evaluate medicine matching and ingredient-overlap behavior using project scripts and reports.

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

- **Tesseract OCR:** Text extraction from medicine packaging.
- **RapidFuzz:** Fuzzy string matching for medicine identification.
- **scikit-learn TF-IDF:** Character n-gram similarity-based candidate retrieval and ranking.
- **Groq API:** AI-generated explanations.
- **openFDA API:** External drug-label reference information.
- **Bangladeshi medicine product dataset:** Initial medicine catalogue and ingredient mapping source.

## System Architecture

```text
User
 |
 v
Next.js Frontend
 |
 +--> Medicine Search
 |
 +--> Medicine Image Upload
 |       |
 |       v
 |    FastAPI OCR Endpoint
 |       |
 |       v
 |    Extracted Text
 |       |
 |       +--> RapidFuzz Matching
 |       |
 |       +--> TF-IDF Matching
 |                 |
 |                 v
 |          Candidate Ranking
 |
 +--> Medicine Selection
          |
          v
      FastAPI Backend
          |
          v
      PostgreSQL (Neon)
          |
          v
      Ingredient Comparison
          |
          +--> Overlap Results
          +--> Incomplete-Data Warnings
          +--> Same-Class Warnings
          |
          v
      Groq API / Available Reference Data
          |
          v
      Results and AI Explanation
```

The application separates the frontend, backend API, and database. OCR and medicine matching help identify candidate products, while ingredient comparison relies on the ingredient records available in the database.

AI-generated explanations provide additional context and should not be treated as verified medical advice.

## How It Works

1. Search for a medicine or upload an image of its packaging.
2. Extract text from the uploaded image using OCR.
3. Generate candidate medicine matches from the extracted text.
4. Review and confirm the correct medicine.
5. Select two or more medicines for comparison.
6. Review shared recorded active ingredients, possible same-class warnings, and missing-data notices.
7. Read the AI-generated explanation and any available reference information.

## Evaluation

The project includes evaluation scripts for medicine matching and ingredient-overlap assessment.

### Medicine Matching

The latest recorded manual benchmark compares RapidFuzz and TF-IDF using five hand-typed medicine identification cases.

| Metric                       | RapidFuzz | TF-IDF |
| ---------------------------- | --------: | -----: |
| Top-1 accuracy               |       80% |    80% |
| Top-3 accuracy               |      100% |   100% |
| Mean reciprocal rank (MRR@3) |      0.90 |   0.90 |
| No-candidate rate            |        0% |     0% |
| Mean time per query          |    4.00 s | 3.92 s |
| Evaluation cases             |         5 |      5 |

These results indicate that both approaches ranked the expected medicine first in four of five cases and included it within the top three in all five cases.

**Limitations:** This is a small benchmark of clean, manually written queries. It does not establish performance on real-world packaging images, noisy OCR output, or the full Bangladeshi medicine catalogue. The reported query times are environment-dependent.

Similarity scores and adjusted ranking scores are not calibrated probabilities of correctness. Candidate results require user confirmation.

### Ingredient-Overlap Assessment

The project includes an ingredient-overlap assessment covering **10 of 10 evaluation cases**. Consult the generated reports in `backend/evaluation/results/` for the recorded true positives, false positives, false negatives, precision, recall, and F1 score.

Evaluation results assess implemented behavior; they do not establish clinical validity.

### Additional Evaluation Limitations

- Real medicine photographs have not been included in the latest manual benchmark.
- A trained YOLO detector and detector-labelled evaluation dataset were not available for the documented assessment.
- A sentence-transformer and FAISS-based matcher is not implemented in the evaluated matching pipeline.

## Data Coverage and Limitations

The current database coverage report records the following figures:

| Measure                                     | Reported value |
| ------------------------------------------- | -------------: |
| Medicine records                            |         21,721 |
| Medicines with at least one ingredient link |         20,485 |
| Medicines without ingredient links          |          1,236 |
| Ingredient-link coverage                    |         94.31% |
| Ingredient links with recorded amounts      |              3 |

**Important interpretation:** The 94.31% figure means that a medicine has at least one ingredient link. It does not mean that every ingredient has been verified or that combination-product mappings are complete. Recorded ingredient amounts are also insufficient for reliable strength-level comparisons.

The application warns about medicines with no ingredient links. However, a medicine with at least one ingredient link may still have incomplete ingredient information. Therefore, an overlap result may be incomplete even when the application finds a shared ingredient.

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
├── LICENSE
└── README.md
```

## Live Deployment

- **Frontend:** https://doubledose-ai.vercel.app
- **Backend API:** https://doubledose-ai-api.onrender.com
- **API documentation:** https://doubledose-ai-api.onrender.com/docs

The backend provides API endpoints for the implemented medicine search, ingredient comparison, AI explanations, OCR extraction, and medicine matching functionality. The deployed OpenAPI documentation lists the available endpoints.

## Running Locally

The frontend and backend run as separate applications.

### Prerequisites

- Python and pip
- Node.js and npm
- A configured Neon PostgreSQL database or compatible PostgreSQL instance
- A Groq API key for AI-generated explanations
- Tesseract OCR installed for local OCR functionality

### 1. Backend Setup

Open PowerShell in the `backend` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure the backend environment variables using the names expected by the application. These include the database connection settings and Groq API key. Keep credentials out of source control.

Start the FastAPI server:

```powershell
uvicorn main:app --reload
```

The local API should be available at:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

### 2. Frontend Setup

Open a separate terminal in the `frontend` directory:

```powershell
npm install
npm run dev
```

Configure the frontend's backend API URL using the environment variable expected by the application. For the deployed frontend, this must point to the deployed backend API.

Open:

`http://localhost:3000`

If the repository uses a different package manager or dependency lockfile, follow the existing project configuration.

## Responsible Use and Safety

DoubleDose AI does not replace a pharmacist, physician, or other qualified healthcare professional.

- OCR may misread medicine names, ingredient lists, or strengths.
- A fuzzy-matching result is a candidate, not proof of product equivalence.
- Missing or incomplete ingredient mappings can cause the application to miss overlaps.
- Shared ingredients are not the only source of potential medication interactions.
- The application does not establish whether a medicine combination is safe for an individual.
- AI-generated explanations may contain inaccurate or incomplete information.
- openFDA information may describe US-market products and may not apply directly to medicines sold in Bangladesh.
- The project has not been clinically validated as a medical device.

Always verify medicine information against the actual packaging and consult a qualified healthcare professional before changing medication, combining medicines, or making treatment decisions.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
