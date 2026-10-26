# DoubleDose AI — User Guide

## 1. Overview

DoubleDose AI helps users search for medicines, identify medicines from package images, compare ingredient information, and view AI-generated explanations of potential ingredient overlap.

The application is intended for informational and educational use. It does not provide medical diagnoses, prescribe medicines, or replace advice from a qualified healthcare professional.

## 2. Accessing the Application

- **Frontend:** https://doubledose-ai.vercel.app
- **Backend API documentation:** https://doubledose-ai-api.onrender.com/docs

Open the frontend URL in a modern web browser. The backend API documentation is available for reviewing the application's API endpoints.

## 3. Searching for Medicines

1. Open the application.
2. Locate the medicine search field.
3. Enter at least two characters of a medicine name.
4. Review the matching results.
5. Select the correct medicine from the results.

Check the displayed medicine information carefully. Similar brand names may refer to different products.

**Screenshot:** `images/medicine-search.png`

## 4. Identifying Medicines from Package Images

1. Locate the medicine image upload section.
2. Upload a supported medicine-package image.
3. Wait for the OCR process to extract text.
4. Review the extracted text and suggested medicine candidates.
5. Confirm the correct medicine manually before proceeding.

OCR may misread brand names, strengths, or ingredient information. If the suggested candidates are incorrect, use manual search when available.

**Screenshot:** `images/ocr-candidates.png`

## 5. Comparing Medicines

1. Search for medicines or select them from OCR suggestions.
2. Confirm the selected products.
3. Select the medicines you want to compare, following the application's selection limit.
4. Run the ingredient-overlap comparison.
5. Review the displayed ingredient information and warnings.

If ingredient data is missing or incomplete, interpret the result cautiously. A missing overlap result does not establish that combining the medicines is safe.

**Screenshot:** `images/ingredient-overlap.png`

## 6. Viewing AI-Generated Explanations

When an AI explanation is available, review it alongside the ingredient comparison and any displayed references or warnings.

AI-generated content may be inaccurate or incomplete. If the explanation service is unavailable, follow the message shown by the application and rely on verified information from an appropriate healthcare professional.

**Screenshot:** `images/ai-explanation.png`

## 7. Important Safety Information

- Do not use the application to diagnose a condition or decide independently whether to start, stop, or combine medicines.
- OCR can extract incorrect text, and medicine matching can suggest the wrong product.
- Ingredient records may be incomplete or lack strength and amount information.
- AI-generated explanations are not clinically validated medical advice.
- External drug-label references may describe products or regulatory information that differ from those available in Bangladesh.
- Consult a qualified pharmacist or physician about possible interactions and medication decisions.

## 8. Troubleshooting

**No medicine search results:** Check the spelling or try another part of the brand name.

**Incorrect OCR candidates:** Review the extracted text and search for the medicine manually.

**Missing ingredient information:** Treat the comparison as incomplete; do not interpret missing data as proof of safety.

**AI explanation unavailable:** Retry later if appropriate. The AI service may be temporarily unavailable or may return an error.

**Application or API unavailable:** Try again later. The deployed service may be starting up or temporarily unavailable.
