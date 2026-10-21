
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import AIExplanationCard from "@/components/medicines/ai-explanation-card";
import { explainOverlap } from "@/lib/ai-api";
import type {
  AIExplanationRequest,
  AIExplanationResponse,
} from "@/types/ai-explanation";

type Medicine = {
  id: number;
  brand_name: string;
  source_display_name?: string | null;
  generic_name?: string | null;
  dosage_form?: string | null;
  manufacturer?: string | null;
};

type OverlappingIngredient = {
  ingredient_id: number;
  name: string;
  medicine_ids: number[];
  medicine_names: string[];
};

type OverlapResult = {
  medicines: Medicine[];
  has_overlap: boolean;
  overlapping_ingredients: OverlappingIngredient[];
  result_status: "overlap_found" | "no_overlap_found" | "incomplete_data";
  has_incomplete_data: boolean;
  medicines_without_ingredient_data: number[];
};

async function readError(response: Response): Promise<string> {
  try {
    const data = await response.json();

    return (
      data.detail ??
      data.message ??
      "Something went wrong. Please try again."
    );
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

function medicineStrength(medicine: Medicine): string | null {
  const match = medicine.source_display_name?.match(
    /\|\s*Strength:\s*(.*?)\s*\|/i,
  );

  return match?.[1]?.trim() || null;
}

function medicineDetails(medicine: Medicine): string {
  return [
    medicineStrength(medicine),
    medicine.dosage_form,
    medicine.manufacturer,
  ]
    .filter(Boolean)
    .join(" · ");
}


export default function Home() {
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Medicine[]>([]);
  const [selected, setSelected] = useState<Medicine[]>([]);
  const [result, setResult] = useState<OverlapResult | null>(null);

  const [searching, setSearching] = useState(false);
  const [checking, setChecking] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [checkError, setCheckError] = useState("");

  const [aiExplanation, setAiExplanation] =
    useState<AIExplanationResponse | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  // Search the medicine database with a short debounce.

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

        const data = await response.json();

        const medicines: Medicine[] = Array.isArray(data)
          ? data
          : Array.isArray(data.items)
            ? data.items
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


  function resetResults() {
    setResult(null);
    setCheckError("");
    setAiExplanation(null);
    setAiError(null);
    setAiLoading(false);
  }

  function addMedicine(medicine: Medicine) {
    if (selected.some((item) => item.id === medicine.id)) return;
    if (selected.length >= 5) return;

    setSelected((current) => [...current, medicine]);
    setQuery("");
    setSearchResults([]);
    setSearchError("");
    resetResults();
  }

  function removeMedicine(id: number) {
    setSelected((current) =>
      current.filter((item) => item.id !== id),
    );

    resetResults();
  }

  // Compare the selected medicines, then request an AI explanation.
  async function checkOverlap() {
    if (selected.length < 2 || selected.length > 5) return;

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

      // Show the deterministic comparison before requesting AI.
      setResult(data);
      setChecking(false);
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

            return medicine
              ? medicineLabel(medicine)
              : `Medicine ID ${id}`;
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

  const canCheck = selected.length >= 2 && selected.length <= 5;

  return (
    <main className="app-shell">
      <header className="topbar">
        <Link
          className="brand"
          href="/"
          aria-label="DoubleDose AI home"
        >
          <span className="brand-mark">
            D<span>+</span>
          </span>
          <span className="brand-name">
            DoubleDose<span> AI</span>
          </span>
        </Link>

        <div className="topbar-right">
          <span className="status-dot" />
          <span>Ingredient checker</span>
        </div>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow">
            <span className="eyebrow-dot" />
            YOUR MEDICINE COMPANION
          </div>

          <h1>
            Know what’s
            <br />
            <span>inside your medicines.</span>
          </h1>

          <p className="hero-description">
            Compare active ingredients across your medicines and identify
            potential overlaps in one place.
          </p>

          <div className="hero-points">
            <span>
              <span className="check-icon">✓</span> Ingredient comparison
            </span>
            <span>
              <span className="check-icon">✓</span> Clear explanations
            </span>
          </div>
        </div>

        <div className="hero-illustration" aria-hidden="true">
          <div className="illustration-orbit orbit-one" />
          <div className="illustration-orbit orbit-two" />

          <div className="illustration-card">
            <div className="illustration-pill">
              <span />
              <span />
            </div>
            <div className="illustration-line line-long" />
            <div className="illustration-line line-short" />
            <div className="illustration-status">
              <span>✓</span>
              Ingredient check
            </div>
          </div>

          <span className="floating-cross cross-one">+</span>
          <span className="floating-cross cross-two">+</span>
          <span className="floating-dot dot-one" />
          <span className="floating-dot dot-two" />
        </div>
      </section>

      <section className="workspace">
        <div className="section-heading">
          <div>
            <div className="section-kicker">LET’S GET STARTED</div>
            <h2>Compare your medicines</h2>
            <p>Search for a medicine, then add it to your comparison.</p>
          </div>

          <div className="selection-count">
            <strong>{selected.length}</strong> / 5 selected
          </div>
        </div>

        <div className="comparison-grid">
          <section className="panel search-panel">
            <div className="panel-heading">
              <span className="step-number">01</span>
              <div>
                <h3>Find medicines</h3>
                <p>Search by medicine or brand name.</p>
              </div>
            </div>

            <label className="search-label" htmlFor="medicine-search">
              Medicine name
            </label>

            <div className="search-box">
              <span className="search-icon" aria-hidden="true">
                ⌕
              </span>

              <input
                id="medicine-search"
                value={query}

                onChange={(event) => {
                  const value = event.target.value;

                  setQuery(value);

                  if (value.trim().length < 2) {
                    setSearchResults([]);
                    setSearching(false);
                    setSearchError("");
                  }
                }}

                placeholder="e.g. acetaminophen"
                autoComplete="off"
              />

              {searching && (
                <span className="spinner" aria-label="Searching" />
              )}
            </div>

            <div className="search-hint">
              Type at least 2 characters to search your medicine database.
            </div>

            {searchError && (
              <div className="inline-error" role="alert">
                {searchError}
              </div>
            )}

            {query.trim().length >= 2 &&
              !searching &&
              !searchError &&
              searchResults.length === 0 && (
                <div className="empty-search">
                  No matching medicines found. Try another name.
                </div>
              )}

            {query.trim().length >= 2 && searchResults.length > 0 && (
              <div className="search-results">
                <div className="results-label">SEARCH RESULTS</div>

                {searchResults.map((medicine) => {
                  const alreadySelected = selected.some(
                    (item) => item.id === medicine.id,
                  );

                  return (
                    <button
                      key={medicine.id}
                      type="button"
                      className="search-result"
                      onClick={() => addMedicine(medicine)}
                      disabled={alreadySelected || selected.length >= 5}
                    >
                      <span className="medicine-symbol">Rx</span>

                      <span className="medicine-result-copy">
                        <strong>{medicineLabel(medicine)}</strong>
                        <span>{medicine.generic_name || "Generic name unavailable"}</span>
                        <span>{medicineDetails(medicine) || "Details unavailable"}</span>
                      </span>

                      <span className="add-symbol">
                        {alreadySelected ? "✓" : "+"}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}

            <div className="search-footer">
              <span className="footer-shield">i</span>
              Results depend on the medicines available in the database.
            </div>
          </section>

          <section className="panel selected-panel">
            <div className="panel-heading">
              <span className="step-number">02</span>
              <div>
                <h3>Your comparison</h3>
                <p>Select 2 to 5 different medicines.</p>
              </div>
            </div>

            {selected.length === 0 ? (
              <div className="selection-empty">
                <div className="empty-pills">
                  <span className="empty-pill">Rx</span>
                  <span className="empty-plus">+</span>
                  <span className="empty-pill empty-pill-muted">Rx</span>
                </div>

                <strong>No medicines added yet</strong>
                <p>Your selected medicines will appear here.</p>
              </div>
            ) : (
              <div className="selected-list">
                {selected.map((medicine, index) => (
                  <div
                    className="selected-medicine"
                    key={medicine.id}
                  >
                    <span className="selected-index">
                      {String(index + 1).padStart(2, "0")}
                    </span>

                    <span className="medicine-result-copy">
                      <strong>{medicineLabel(medicine)}</strong>
                      <span>{medicine.generic_name || "Generic name unavailable"}</span>
                      <span>{medicineDetails(medicine) || "Details unavailable"}</span>
                    </span>

                    <button
                      className="remove-button"
                      type="button"
                      onClick={() => removeMedicine(medicine.id)}
                      aria-label={`Remove ${medicineLabel(medicine)}`}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="comparison-actions">
              <button
                className="primary-button"
                type="button"
                onClick={checkOverlap}
                disabled={!canCheck || checking}
              >
                {checking ? (
                  <>
                    <span className="button-spinner" />
                    Checking ingredients…
                  </>
                ) : (
                  <>
                    Check ingredient overlap
                    <span aria-hidden="true">→</span>
                  </>
                )}
              </button>

              <span className="button-note">
                {selected.length < 2
                  ? `Add ${2 - selected.length} more ${2 - selected.length === 1 ? "medicine" : "medicines"
                  } to compare`
                  : `${selected.length} medicines ready to compare`}
              </span>
            </div>

            {checkError && (
              <div className="inline-error" role="alert">
                {checkError}
              </div>
            )}
          </section>
        </div>

        {result && (
          <section className="results-panel" aria-live="polite">
            <div className="result-heading">
              <div>
                <div className="section-kicker">YOUR RESULTS</div>
                <h2>Ingredient comparison</h2>
                <p>Based on the ingredient records currently available.</p>
              </div>

              <span
                className={`result-badge ${result.result_status === "overlap_found"
                  ? "badge-warning"
                  : result.result_status === "incomplete_data"
                    ? "badge-incomplete"
                    : "badge-clear"
                  }`}
              >
                {result.result_status === "overlap_found"
                  ? "Overlap found"
                  : result.result_status === "incomplete_data"
                    ? "Data incomplete"
                    : "No overlap found"}
              </span>
            </div>

            {result.result_status === "overlap_found" && (
              <div className="result-summary summary-warning">
                <span className="summary-icon">!</span>
                <div>
                  <strong>
                    One or more shared ingredients were found.
                  </strong>
                  <p>
                    Review the ingredients below with a pharmacist or
                    healthcare professional before making medicine decisions.
                  </p>
                </div>
              </div>
            )}

            {result.result_status === "no_overlap_found" && (
              <div className="result-summary summary-clear">
                <span className="summary-icon">✓</span>
                <div>
                  <strong>
                    No shared ingredients were found in the available records.
                  </strong>
                  <p>
                    This does not establish that the combination is safe.
                    Ingredient records may be incomplete.
                  </p>
                </div>
              </div>
            )}

            {result.result_status === "incomplete_data" && (
              <div className="result-summary summary-incomplete">
                <span className="summary-icon">!</span>
                <div>
                  <strong>We couldn’t verify all selected medicines.</strong>
                  <p>
                    Some medicines have no ingredient records, so the
                    comparison may be incomplete.
                  </p>
                </div>
              </div>
            )}

            {result.overlapping_ingredients.length > 0 ? (
              <div className="ingredient-section">
                <h3>Shared active ingredients</h3>

                <div className="ingredient-list">
                  {result.overlapping_ingredients.map((ingredient) => (
                    <article
                      className="ingredient-card"
                      key={ingredient.ingredient_id}
                    >
                      <span className="ingredient-icon">!</span>

                      <div className="ingredient-copy">
                        <strong>{ingredient.name}</strong>
                        <span>Appears in these selected medicines</span>

                        <div className="medicine-tags">
                          {ingredient.medicine_names.map((name, index) => (
                            <span key={`${name}-${index}`}>{name}</span>
                          ))}
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            ) : (
              result.result_status !== "incomplete_data" && (
                <div className="no-shared-ingredients">
                  No shared ingredients were identified in the records checked.
                </div>
              )
            )}

            {result.medicines_without_ingredient_data.length > 0 && (
              <div className="missing-data">
                <strong>Ingredient data unavailable for:</strong>
                <ul>
                  {result.medicines_without_ingredient_data.map((id) => {
                    const medicine = selected.find((item) => item.id === id);

                    return (
                      <li key={id}>
                        {medicine
                          ? medicineLabel(medicine)
                          : `Medicine ID ${id}`}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            <div className="result-disclaimer">
              <strong>Important:</strong> DoubleDose AI checks for shared
              ingredients in available database records. It does not assess
              all drug interactions, determine appropriate doses, or establish
              whether a medicine combination is safe. Consult a qualified
              healthcare professional.
            </div>

            <AIExplanationCard
              explanation={aiExplanation}
              loading={aiLoading}
              error={aiError}
            />
          </section>
        )}
      </section>

      <footer className="site-footer">
        <Link className="footer-brand" href="/">
          DoubleDose AI
        </Link>
        <span>Built to help you understand ingredient overlap.</span>
        <span className="footer-disclaimer">
          Not a substitute for professional medical advice.
        </span>
      </footer>
    </main>
  );
}
