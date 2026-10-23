"use client";

import { useState } from "react";

import { explainOverlap } from "@/lib/ai-api";
import type {
  AIExplanationRequest,
  AIExplanationResponse,
} from "@/types/ai-explanation";
import type { Medicine } from "@/types/medicine";
import type { OverlapResult } from "@/types/overlap";

async function readError(response: Response): Promise<string> {
  try {
    const data: unknown = await response.json();

    if (typeof data === "object" && data !== null) {
      if ("detail" in data && typeof data.detail === "string") {
        return data.detail;
      }

      if ("message" in data && typeof data.message === "string") {
        return data.message;
      }
    }

    return "Something went wrong. Please try again.";
  } catch {
    return "Something went wrong. Please try again.";
  }
}

function medicineLabel(medicine: Medicine): string {
  return (
    medicine.brand_name || medicine.generic_name || `Medicine ${medicine.id}`
  );
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function isPermanentAIError(error: unknown): boolean {
  const message = error instanceof Error ? error.message.toLowerCase() : "";

  return [
    "api key is not configured",
    "invalid api key",
    "unauthorized",
    "forbidden",
    "invalid request",
    "validation error",
  ].some((phrase) => message.includes(phrase));
}

async function generateExplanationWithRetry(
  payload: AIExplanationRequest,
): Promise<AIExplanationResponse> {
  const maxAttempts = 2;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      return await explainOverlap(payload);
    } catch (error) {
      if (attempt === maxAttempts || isPermanentAIError(error)) {
        throw error;
      }

      await wait(1200);
    }
  }

  throw new Error("Unable to generate an AI explanation.");
}

export default function useMedicineOverlap() {
  const [result, setResult] = useState<OverlapResult | null>(null);
  const [checking, setChecking] = useState(false);
  const [checkError, setCheckError] = useState("");

  const [aiExplanation, setAiExplanation] =
    useState<AIExplanationResponse | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  function resetResults() {
    setResult(null);
    setCheckError("");
    setAiExplanation(null);
    setAiError(null);
    setAiLoading(false);
  }

  async function checkOverlap(selected: Medicine[]) {
    if (selected.length < 2 || selected.length > 5 || checking) {
      return;
    }

    setChecking(true);
    setCheckError("");
    setResult(null);
    setAiExplanation(null);
    setAiError(null);
    setAiLoading(false);

    try {
      const response = await fetch("/api/medicines/check-overlap", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          medicine_ids: selected.map((medicine) => medicine.id),
        }),
      });

      if (!response.ok) {
        throw new Error(await readError(response));
      }

      const data: OverlapResult = await response.json();
      setResult(data);

      const selectedNamesById = new Map(
        selected.map((medicine) => [medicine.id, medicineLabel(medicine)]),
      );

      const payload: AIExplanationRequest = {
        result_status: data.result_status,

        medicine_names: data.medicines.map(
          (medicine) =>
            medicine.brand_name ||
            medicine.generic_name ||
            `Medicine ${medicine.id}`,
        ),

        medicines: data.medicines.map((medicine) => ({
          name:
            medicine.brand_name ||
            medicine.generic_name ||
            `Medicine ${medicine.id}`,
          generic_name: medicine.generic_name,
          source_details: medicine.source_display_name,
          dosage_form: medicine.dosage_form,
          manufacturer: medicine.manufacturer,
          ingredients: medicine.ingredients.map((ingredient) => ({
            name: ingredient.name,
            amount: ingredient.amount,
            unit: ingredient.unit,
            source_name: ingredient.source_name,
            source_record_id: ingredient.source_record_id,
            source_url: ingredient.source_url,
            retrieved_at: ingredient.retrieved_at,
          })),
          side_effects: [],
          daily_dose: null,
        })),

        overlapping_ingredients: data.overlapping_ingredients.map(
          (ingredient) => ({
            name: ingredient.name,
            medicine_names: ingredient.medicine_names,
          }),
        ),

        same_class_warnings: (data.same_class_warnings ?? []).map(
          (warning) => ({
            therapeutic_class: warning.therapeutic_class,
            ingredient_names: warning.ingredient_names,
            medicine_ids: warning.medicine_ids,
            medicine_names: warning.medicine_names,
            message: warning.message,
          }),
        ),

        medicines_without_ingredient_data:
          data.medicines_without_ingredient_data.map(
            (id) => selectedNamesById.get(id) ?? `Medicine ID ${id}`,
          ),
      };

      setAiLoading(true);

      try {
        const explanation = await generateExplanationWithRetry(payload);
        setAiExplanation(explanation);
      } catch (error) {
        setAiError(
          error instanceof Error
            ? error.message
            : "Unable to generate an AI explanation. Please try again.",
        );
      } finally {
        setAiLoading(false);
      }
    } catch (error) {
      setCheckError(
        error instanceof Error
          ? error.message
          : "Unable to compare these medicines.",
      );
    } finally {
      setChecking(false);
    }
  }

  return {
    result,
    checking,
    checkError,
    aiExplanation,
    aiLoading,
    aiError,
    checkOverlap,
    resetResults,
  };
}
