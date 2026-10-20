import type {
  AIExplanationRequest,
  AIExplanationResponse,
} from "@/types/ai-explanation";

async function readError(response: Response): Promise<string> {
  try {
    const data: unknown = await response.json();

    if (
      typeof data === "object" &&
      data !== null &&
      "detail" in data &&
      typeof data.detail === "string"
    ) {
      return data.detail;
    }
  } catch {
    // The response may not contain valid JSON.
  }

  return `Request failed with status ${response.status}.`;
}

export async function explainOverlap(
  payload: AIExplanationRequest,
): Promise<AIExplanationResponse> {
  const response = await fetch("/api/ai/explain-overlap", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as AIExplanationResponse;
}
