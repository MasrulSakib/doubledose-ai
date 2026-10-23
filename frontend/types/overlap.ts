import type { Medicine } from "@/types/medicine";

export type OverlappingIngredient = {
  ingredient_id: number;
  name: string;
  medicine_ids: number[];
  medicine_names: string[];
};

export type OverlapResult = {
  medicines: Medicine[];
  has_overlap: boolean;
  overlapping_ingredients: OverlappingIngredient[];
  result_status: "overlap_found" | "no_overlap_found" | "incomplete_data";
  has_incomplete_data: boolean;
  medicines_without_ingredient_data: number[];
};
