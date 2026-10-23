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
      setAiLoading(true);

      const payload: AIExplanationRequest = {
        result_status: data.result_status,
        medicine_names: selected.map(medicineLabel),
        overlapping_ingredients: data.overlapping_ingredients.map(
          (ingredient) => ({
            name: ingredient.name,
            medicine_names: ingredient.medicine_names,
          }),
        ),
        medicines_without_ingredient_data:
          data.medicines_without_ingredient_data.map((id) => {
            const medicine = selected.find((item) => item.id === id);

            return medicine ? medicineLabel(medicine) : `Medicine ID ${id}`;
          }),
      };

      try {
        const explanation = await explainOverlap(payload);
        setAiExplanation(explanation);
      } catch (error) {
        setAiError(
          error instanceof Error
            ? error.message
            : "Unable to generate an AI explanation.",
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
