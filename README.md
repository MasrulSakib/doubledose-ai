# DoubleDose AI

DoubleDose AI is an AI-assisted medicine information and ingredient comparison platform designed around Bangladeshi medicine products. It combines optical character recognition (OCR), fuzzy medicine matching, active ingredient comparison, and AI-generated explanations in a single web application.

The project aims to make medicine information easier to understand and help users identify potential duplicate active ingredients before discussing their medicines with a pharmacist or other qualified healthcare professional.

> **Important:** DoubleDose AI is an informational project, not a medical diagnosis, prescribing, or clinical decision-support tool. A result showing no shared ingredients does not establish that a medicine combination is safe.

## Features

- **Medicine search:** Search a database of Bangladeshi medicine products.
- **Medicine label OCR:** Upload a medicine packaging image to extract text using Tesseract OCR.
- **Fuzzy medicine matching:** Generate candidate medicine matches from OCR text using RapidFuzz.
- **Match confirmation:** Review candidate matches when the system cannot confidently identify a medicine.
- **Ingredient comparison:** Compare selected medicines for shared recorded active ingredients.
- **Incomplete-data warnings:** Identify selected medicines with no ingredient records in the current database.
- **AI-generated explanations:** Generate explanations of ingredient overlap using the Groq API.
- **Drug-label references:** Retrieve available reference information through the openFDA API.
- **Same-class warnings:** Present possible therapeutic-class duplication separately from exact ingredient overlap, when applicable.
- **Evaluation tools:** Evaluate medicine matching and ingredient-overlap behavior using project evaluation scripts and reports.

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
- Tesseract OCR — text extraction from medicine packaging
- RapidFuzz — fuzzy string matching for medicine identification
- Groq API — AI-generated explanations
- openFDA API — external drug-label reference information
- Bangladeshi medicine product dataset — initial medicine catalogue and ingredient mapping source

## System Architecture

```text
User
  |
  v
Next.js Frontend
  |
  +--> Medicine Search
  |
  +--> Image Upload
  |      |
  |      v
  |    FastAPI OCR Endpoint
  |      |
  |      v
  |    Extracted Text
  |      |
  |      v
  |    RapidFuzz Candidate Matching
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
      Active Ingredient Comparison
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

The application separates the frontend, backend API, and database. OCR and medicine matching help identify candidate products, while ingredient comparison uses the records available in the database.

AI-generated explanations provide additional context and should not be treated as verified medical advice.

## How It Works

1. Search for a medicine or upload an image of its packaging.
2. Extract text from the uploaded image using OCR.
3. Generate candidate medicine matches from the extracted text.
4. Review and confirm the correct medicine when necessary.
5. Select two or more medicines for comparison.
6. Review shared recorded active ingredients, possible same-class warnings, and missing-data notices.
7. Read the AI-generated explanation and any available reference information.

## Evaluation

The project includes evaluation scripts for medicine matching and ingredient-overlap assessment.

### Medicine Matching

The matching evaluation compares RapidFuzz and TF-IDF on the available evaluation cases.

| Metric | RapidFuzz | TF-IDF |
|---|---:|---:|
| Top-1 accuracy | 1.00 | 0.40 |
| Top-3 accuracy | 1.00 | Not reported here |
| Mean reciprocal rank | 1.00 | Not reported here |
| Evaluation cases | 5 | 5 |

These results reflect a small evaluation set and should not be interpreted as evidence of equivalent accuracy on all real-world medicine packaging.

### Ingredient-Overlap Assessment

The project overlap assessment report evaluated **10 of 10 cases**. Consult the generated report for the underlying true-positive, false-positive, false-negative, precision, recall, and F1 values.

Evaluation scripts and reports are maintained in the backend project. The results are intended to assess implemented behavior, not to establish clinical validity.

## Data Coverage and Limitations

The current database coverage report records the following:

| Measure | Reported value |
|---|---:|
| Medicine records | 21,721 |
| Medicines with at least one ingredient link | 20,485 |
| Medicines without ingredient links | 1,236 |
| Ingredient-link coverage | 94.31% |
| Ingredient links with recorded amounts | 3 |

**Important interpretation:** The 94.31% figure means that a medicine has at least one ingredient link. It does not mean that every ingredient has been verified or that combination-product mappings are complete. Recorded ingredient amounts are also insufficient for reliable strength-level comparisons.

The application warns about medicines with no ingredient links, but partially mapped medicines may still have incomplete ingredient information.

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

The backend exposes API endpoints for medicine search, ingredient comparison, AI explanations, OCR extraction, OCR-based matching, and matcher evaluation. Available endpoints can be inspected through the deployed API's OpenAPI documentation.

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

Configure the backend environment variables in the appropriate environment file, including the database connection and Groq API key. Use the environment-variable names expected by the application and keep credentials out of source control.

Start the FastAPI server:

```powershell
uvicorn main:app --reload
```

The local API should then be available at:

`http://127.0.0.1:8000`

Interactive API documentation is available at:

`http://127.0.0.1:8000/docs`

### 2. Frontend Setup

Open a separate terminal in the `frontend` directory:

```powershell
npm install
npm run dev
```

Configure the backend API URL using the environment variable expected by the frontend. For the deployed frontend, the backend URL must point to the deployed API.

Open:

`http://localhost:3000`

If your repository uses a different package manager or dependency lockfile, follow the existing project configuration.

## Responsible Use and Safety

DoubleDose AI does not replace a pharmacist, physician, or other qualified healthcare professional.

- OCR may misread medicine names, ingredient lists, or strengths.
- A fuzzy-matching result is a candidate, not proof of product equivalence.
- Missing or incomplete ingredient mappings can cause the application to miss overlaps.
- Shared ingredients are not the only source of potential medication interactions.
- The application does not establish whether a combination is safe for an individual.
- AI-generated explanations may contain inaccurate or incomplete information.
- openFDA information may describe US-market products and may not apply directly to a medicine sold in Bangladesh.
- The project has not been clinically validated as a medical device.

Always verify medicine information against the actual packaging and consult a qualified healthcare professional before changing medication, combining medicines, or making treatment decisions.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
