"use client";

import { useState } from "react";

import { explainOverlap } from "@/lib/ai-api";
import type {
  AIExplanationRequest,
  AIExplanationResponse,
} from "@/types/ai-explanation";
import type { Medicine } from "@/types/medicine";
import type { OverlapResult } from "@/types/overlap";

type MedicineWithOptionalDetails = Medicine & {
  dosage_form?: string | null;
  manufacturer?: string | null;
  side_effects?: string[];
  daily_dose?: string | null;
  information_source?: string | null;
  source_url?: string | null;
};

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
    medicine.brand_name ||
    medicine.generic_name ||
    `Medicine ${medicine.id}`
  );
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
    "model_decommissioned",
  ].some((phrase) => message.includes(phrase));
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
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
    setChecking(false);
  }

  async function checkOverlap(selected: Medicine[]) {
    if (
      selected.length < 2 ||
      selected.length > 5 ||
      checking ||
      aiLoading
    ) {
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
      setChecking(false);

      const payload: AIExplanationRequest = {
        result_status: data.result_status,
        medicine_names: selected.map(medicineLabel),
        medicines: selected.map((medicine) => {
          const details = medicine as MedicineWithOptionalDetails;
          return {
            name: medicineLabel(medicine),
            generic_name: medicine.generic_name ?? null,
            source_details: medicine.source_display_name ?? null,
            dosage_form: details.dosage_form ?? null,
            manufacturer: details.manufacturer ?? null,
            // Only forward these when the selected medicine record actually
            // contains them. Do not infer side effects or patient dosage.
            side_effects: Array.isArray(details.side_effects)
              ? details.side_effects
              : [],
            daily_dose: details.daily_dose ?? null,
            information_source: details.information_source ?? null,
            source_url: details.source_url ?? null,
          };
        }),
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
