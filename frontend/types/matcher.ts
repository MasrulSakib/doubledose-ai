import type { OCRMedicineMatch } from "@/types/ocr";

export interface MatcherCompareRequest {
  extracted_text: string;
  limit?: number;
}

export interface MatcherCompareResponse {
  extracted_text: string;
  rapidfuzz: OCRMedicineMatch[];
  tfidf: OCRMedicineMatch[];
}
