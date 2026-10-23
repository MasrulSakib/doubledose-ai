export type AIExplanationStatus =
  | "overlap_found"
  | "no_overlap_found"
  | "incomplete_data";

export interface OverlapIngredientInput {
  name: string;
  medicine_names: string[];
}

export interface AIExplanationMedicineInput {
  name: string;
  generic_name?: string | null;
  source_details?: string | null;
  dosage_form?: string | null;
  manufacturer?: string | null;
  side_effects?: string[];
  daily_dose?: string | null;
  information_source?: string | null;
  source_url?: string | null;
}

export interface AIExplanationRequest {
  result_status: AIExplanationStatus;
  medicine_names: string[];
  medicines?: AIExplanationMedicineInput[];
  overlapping_ingredients: OverlapIngredientInput[];
  medicines_without_ingredient_data: string[];
}

export interface AIExplanationResponse {
  explanation: string;
  limitations: string[];
  disclaimer: string;
}
