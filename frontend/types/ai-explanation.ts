export type OverlapResultStatus =
  | "overlap_found"
  | "no_overlap_found"
  | "incomplete_data";

export interface OverlapIngredientInput {
  name: string;
  medicine_names: string[];
}

export interface AIExplanationRequest {
  result_status: OverlapResultStatus;
  medicine_names: string[];
  overlapping_ingredients: OverlapIngredientInput[];
  medicines_without_ingredient_data: string[];
}

export interface AIExplanationResponse {
  explanation: string;
  limitations: string[];
  disclaimer: string;
}
