
export type OverlapStatus =
  | "overlap_found"
  | "no_overlap_found"
  | "incomplete_data";

export interface MedicineIngredientDetail {
  id: number;
  name: string;
  amount: number | null;
  unit: string | null;
  source_name: string | null;
  source_record_id: string | null;
  source_url: string | null;
  retrieved_at: string | null;
}

export interface MedicineComparison {
  id: number;
  brand_name: string;
  source_display_name: string | null;
  generic_name: string | null;
  dosage_form: string | null;
  manufacturer: string | null;
  ingredients: MedicineIngredientDetail[];
}

export interface OverlappingIngredient {
  ingredient_id: number;
  name: string;
  medicine_ids: number[];
  medicine_names: string[];
}

export interface SameClassWarning {
  therapeutic_class: string;
  ingredient_names: string[];
  medicine_ids: number[];
  medicine_names: string[];
  message: string;
}

export interface OverlapResult {
  medicines: MedicineComparison[];
  has_overlap: boolean;
  overlapping_ingredients: OverlappingIngredient[];
  same_class_warnings: SameClassWarning[];
  result_status: OverlapStatus;
  has_incomplete_data: boolean;
  medicines_without_ingredient_data: number[];
}
