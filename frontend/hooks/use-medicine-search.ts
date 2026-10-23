"use client";

import { useEffect, useState } from "react";
import type { Medicine } from "@/types/medicine";

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

export default function useMedicineSearch() {
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Medicine[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");

  useEffect(() => {
    const trimmedQuery = query.trim();

    if (trimmedQuery.length < 2) {
      return;
    }

    let cancelled = false;

    const timer = window.setTimeout(async () => {
      setSearching(true);
      setSearchError("");

      try {
        const response = await fetch(
          `/api/medicines?q=${encodeURIComponent(trimmedQuery)}&limit=10`,
          { cache: "no-store" },
        );

        if (!response.ok) {
          throw new Error(await readError(response));
        }

        const data: unknown = await response.json();

        const medicines: Medicine[] = Array.isArray(data)
          ? (data as Medicine[])
          : typeof data === "object" &&
              data !== null &&
              "items" in data &&
              Array.isArray(data.items)
            ? (data.items as Medicine[])
            : [];

        if (!cancelled) {
          setSearchResults(medicines);
        }
      } catch (error) {
        if (!cancelled) {
          setSearchResults([]);
          setSearchError(
            error instanceof Error
              ? error.message
              : "Unable to search medicines.",
          );
        }
      } finally {
        if (!cancelled) {
          setSearching(false);
        }
      }
    }, 300);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query]);

  function updateQuery(value: string) {
    setQuery(value);

    if (value.trim().length < 2) {
      setSearchResults([]);
      setSearchError("");
      setSearching(false);
    }
  }

  function clearSearch() {
    setQuery("");
    setSearchResults([]);
    setSearchError("");
    setSearching(false);
  }

  return {
    query,
    searchResults,
    searching,
    searchError,
    setQuery,
    updateQuery,
    clearSearch,
  };
}
