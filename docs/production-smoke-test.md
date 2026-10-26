# DoubleDose AI — Production Smoke Test

**Test date:** 25 October 2026  
**Environment:** Production

## Deployment URLs

- Frontend: https://doubledose-ai.vercel.app
- Backend API: https://doubledose-ai-api.onrender.com

## Test Results

| Test                                                                                            | Result |
| ----------------------------------------------------------------------------------------------- | ------ |
| Medicine search returns results                                                                 | PASS   |
| OCR upload extracts text and displays medicine candidates                                       | PASS   |
| Selecting medicines displays ingredient-overlap results and applicable incomplete-data warnings | PASS   |
| AI explanation loads or displays a useful error when the service is unavailable                 | PASS   |

## Summary

All four production smoke tests passed. The core application workflows are operational.

## Known Limitations

- OCR extraction and medicine-candidate ranking require further accuracy evaluation.
- Ingredient information may be incomplete for some medicines.
- AI-generated explanations should not be treated as a definitive medical assessment.

## Next Steps

1. Evaluate OCR performance using representative medicine-package images.
2. Record incorrect or missing medicine candidates.
3. Review application safety messaging and incomplete-data handling.
4. Finalize project documentation and capstone demonstration materials.
