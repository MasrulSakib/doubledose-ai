export interface OCRExtractResponse {
  extracted_text: string;
  text_found: boolean;
  detection_used: boolean;
  fallback_used: boolean;
  message: string;
}

export interface OCRMatchRequest {
  extracted_text: string;
  limit?: number;
}

export interface OCRMedicineMatch {
  medicine_id: number;
  brand_name: string;
  generic_name: string | null;
  strength: string | null;
  match_score: number;
  needs_confirmation: boolean;
}

export interface OCRMatchResponse {
  matches: OCRMedicineMatch[];
  match_count: number;
  message: string;
}

export type OCRMatchResultsProps = {
  extractedText: string;
  onExtractedTextChange: (text: string) => void;
  matches: OCRMedicineMatch[];
  onSelectMatch: (match: OCRMedicineMatch) => void;
  selectedMedicineIds: number[];
  matching?: boolean;
  error?: string | null;
};
