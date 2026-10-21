import type {
  OCRExtractResponse,
  OCRMatchRequest,
  OCRMatchResponse,
} from "@/types/ocr";

async function readErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const body: unknown = await response.json();

    if (
      typeof body === "object" &&
      body !== null &&
      "detail" in body &&
      typeof body.detail === "string"
    ) {
      return body.detail;
    }
  } catch {
    // Use the fallback when the response is not valid JSON.
  }

  return fallback;
}

export async function extractMedicineText(
  file: File,
): Promise<OCRExtractResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/ocr/extract", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(
        response,
        "Unable to extract text from the image.",
      ),
    );
  }

  return (await response.json()) as OCRExtractResponse;
}

export async function matchMedicinesFromText(
  payload: OCRMatchRequest,
): Promise<OCRMatchResponse> {
  const response = await fetch("/api/ocr/match", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Unable to match medicines."),
    );
  }

  return (await response.json()) as OCRMatchResponse;
}
