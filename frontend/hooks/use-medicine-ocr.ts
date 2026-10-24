"use client";

import { useEffect, useState } from "react";

import { compareMedicineMatchers, extractMedicineText } from "@/lib/ocr-api";
import type { MatcherCompareResponse } from "@/types/matcher";

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];

export default function useMedicineOCR() {
  const [ocrFile, setOcrFile] = useState<File | null>(null);
  const [ocrPreviewUrl, setOcrPreviewUrl] = useState<string | null>(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrError, setOcrError] = useState("");
  const [ocrText, setOcrText] = useState("");
  const [matcherComparison, setMatcherComparison] =
    useState<MatcherCompareResponse | null>(null);
  const [ocrMessage, setOcrMessage] = useState("");

  useEffect(() => {
    return () => {
      if (ocrPreviewUrl) {
        URL.revokeObjectURL(ocrPreviewUrl);
      }
    };
  }, [ocrPreviewUrl]);

  function handleOCRFileChange(file: File | null) {
    setOcrError("");
    setOcrText("");
    setMatcherComparison(null);
    setOcrMessage("");

    if (!file) {
      setOcrFile(null);
      setOcrPreviewUrl(null);
      return;
    }

    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      setOcrFile(null);
      setOcrPreviewUrl(null);
      setOcrError("Please select a JPEG, PNG, or WebP image.");
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setOcrFile(null);
      setOcrPreviewUrl(null);
      setOcrError("The image must be 10 MB or smaller.");
      return;
    }

    setOcrFile(file);
    setOcrPreviewUrl(URL.createObjectURL(file));
  }

  function updateOCRText(text: string) {
    setOcrText(text);
    setMatcherComparison(null);
    setOcrMessage("");
    setOcrError("");
  }

  async function runMatcherComparison(text: string) {
    const comparison = await compareMedicineMatchers({
      extracted_text: text,
      limit: 10,
    });

    setMatcherComparison(comparison);

    const rapidfuzzCount = comparison.rapidfuzz?.length ?? 0;
    const tfidfCount = comparison.tfidf?.length ?? 0;

    setOcrMessage(
      rapidfuzzCount || tfidfCount
        ? `Found ${rapidfuzzCount} RapidFuzz and ${tfidfCount} TF-IDF candidates. Review the results and confirm the correct medicine.`
        : "Text was extracted, but neither matcher found likely candidates. Try editing the text or searching manually.",
    );
  }

  async function processOCR() {
    if (!ocrFile || ocrLoading) return;

    setOcrLoading(true);
    setOcrError("");
    setOcrText("");
    setMatcherComparison(null);
    setOcrMessage("");

    try {
      const extraction = await extractMedicineText(ocrFile);
      setOcrText(extraction.extracted_text);

      if (!extraction.text_found || !extraction.extracted_text.trim()) {
        setOcrMessage(
          extraction.message ||
            "No readable text found. Try a clearer photo or search manually.",
        );
        return;
      }

      await runMatcherComparison(extraction.extracted_text);
    } catch (error) {
      setOcrError(
        error instanceof Error
          ? error.message
          : "Unable to process this image. Please try again.",
      );
    } finally {
      setOcrLoading(false);
    }
  }

  async function rematchEditedOCRText() {
    const trimmedText = ocrText.trim();

    if (!trimmedText || ocrLoading) return;

    setOcrLoading(true);
    setOcrError("");
    setMatcherComparison(null);
    setOcrMessage("");

    try {
      await runMatcherComparison(trimmedText);
    } catch (error) {
      setOcrError(
        error instanceof Error
          ? error.message
          : "Unable to compare the edited text.",
      );
    } finally {
      setOcrLoading(false);
    }
  }

  return {
    ocrFile,
    ocrPreviewUrl,
    ocrLoading,
    ocrError,
    ocrText,
    matcherComparison,
    ocrMessage,
    updateOCRText,
    setOcrText,
    handleOCRFileChange,
    processOCR,
    rematchEditedOCRText,
  };
}
