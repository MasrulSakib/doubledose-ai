export type AIExplanationStatus =
  | "overlap_found"
  | "no_overlap_found"
  | "incomplete_data";

export interface OverlapIngredientInput {
  name: string;
  medicine_names: string[];
}

export interface SameClassWarningInput {
  therapeutic_class: string;
  ingredient_names: string[];
  medicine_ids: number[];
  medicine_names: string[];
  message: string;
}

export interface AIExplanationIngredientInput {
  name: string;
  amount?: number | null;
  unit?: string | null;
  source_name?: string | null;
  source_record_id?: string | null;
  source_url?: string | null;
  retrieved_at?: string | null;
}

export interface AIExplanationMedicineInput {
  name: string;
  generic_name?: string | null;
  source_details?: string | null;
  dosage_form?: string | null;
  manufacturer?: string | null;
  ingredients?: AIExplanationIngredientInput[];
  side_effects?: string[];
  daily_dose?: string | null;
}

export interface AIExplanationRequest {
  result_status: AIExplanationStatus;
  medicine_names: string[];
  medicines?: AIExplanationMedicineInput[];
  overlapping_ingredients: OverlapIngredientInput[];
  same_class_warnings?: SameClassWarningInput[];
  medicines_without_ingredient_data: string[];
}

export interface AIExplanationResponse {
  explanation: string;
  limitations: string[];
  disclaimer: string;
}
