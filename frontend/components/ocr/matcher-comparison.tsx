"use client";

import type { MatcherCompareResponse } from "@/types/matcher";
import type { OCRMedicineMatch } from "@/types/ocr";

type MatcherComparisonProps = {
  comparison: MatcherCompareResponse;
  selectedMedicineIds: number[];
  onSelectCandidate: (candidate: OCRMedicineMatch) => void;
  selectedCount: number;
};

function candidateStrength(candidate: OCRMedicineMatch): string | null {
  const raw = candidate.strength?.trim();

  if (!raw) return null;

  // Extract the strength from database metadata such as:
  // "BDDrugBank ID: 123 | Generic: ... | Strength: 80 mg | Slug: ..."
  const match = raw.match(/(?:^|\|\s*)Strength:\s*([^|]+)/i);

  if (match?.[1]) return match[1].trim();

  // Use the value directly when it is already a short strength string.
  if (!/^(?:BDDrugBank ID:|Generic:|Slug:)/i.test(raw)) {
    return raw;
  }

  return null;
}

export default function MatcherComparison({
  comparison,
  selectedMedicineIds,
  onSelectCandidate,
  selectedCount,
}: MatcherComparisonProps) {
  const sections = [
    {
      name: "RapidFuzz",
      description: "Fuzzy text matching",
      detail: "Compares text patterns and spelling similarities.",
      candidates: comparison.rapidfuzz ?? [],
    },
    {
      name: "TF-IDF",
      description: "Statistical text matching",
      detail: "Compares the importance of words in the text.",
      candidates: comparison.tfidf ?? [],
    },
    {
      name: "Semantic FAISS",
      description: "Meaning-based matching",
      detail: "Uses text embeddings and vector similarity.",
      candidates: comparison.semantic_faiss ?? [],
    },
  ];

  return (
    <section className="mt-5 min-w-0 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm sm:p-6">
      <div className="mb-5 flex min-w-0 flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="mb-2 text-[10px] font-extrabold tracking-[.14em] text-emerald-700 uppercase">
            Matching results
          </p>

          <h3 className="text-base font-bold text-slate-900">
            Medicine match candidates
          </h3>

          <p className="mt-1.5 text-xs leading-5 text-slate-500">
            Compare three matching methods and confirm the medicine that
            matches your package label.
          </p>
        </div>

        <span className="inline-flex w-fit max-w-full shrink-0 items-center rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-800">
          {selectedCount}/5 medicines selected
        </span>
      </div>

      <div className="mb-5 rounded-xl border border-amber-200/80 bg-amber-50/60 p-3 text-xs leading-5 text-amber-900">
        Similarity scores measure text or semantic similarity. They are not
        probabilities that a medicine is correct and do not establish medical
        equivalence. Verify the brand, active ingredients, strength, and dosage
        form before adding a candidate.
      </div>

      <div className="grid min-w-0 grid-cols-1 gap-4 lg:grid-cols-2 2xl:grid-cols-3">
        {sections.map(({ name, description, detail, candidates }) => (
          <div
            key={name}
            className="min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-white"
          >
            <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
              <div className="flex min-w-0 items-start justify-between gap-2">
                <h4 className="break-words text-sm font-bold text-slate-900">
                  {name}
                </h4>

                <span className="shrink-0 rounded-full bg-white px-2 py-1 text-[10px] font-semibold text-slate-600 ring-1 ring-slate-200">
                  {candidates.length}
                </span>
              </div>

              <p className="mt-1 text-xs font-medium text-slate-600">
                {description}
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                {detail}
              </p>
            </div>

            {candidates.length === 0 ? (
              <p className="p-4 text-sm leading-6 text-slate-500">
                No candidates returned by this matcher. This may happen when
                the method is unavailable or finds no suitable candidates.
              </p>
            ) : (
              <div className="divide-y divide-slate-100">
                {candidates.map((candidate) => {
                  const alreadySelected = selectedMedicineIds.includes(
                    candidate.medicine_id,
                  );

                  const limitReached = selectedCount >= 5;
                  const cannotAdd = limitReached || alreadySelected;

                  const score = Number(candidate.match_score);
                  const validScore =
                    Number.isFinite(score) && score >= 0 && score <= 100;

                  const lowConfidence = !validScore || score < 65;
                  const displayedScore = validScore ? score : 0;
                  const strength = candidateStrength(candidate);

                  return (
                    <article
                      key={`${name}-${candidate.medicine_id}`}
                      className="flex min-w-0 items-start gap-3 p-4 transition hover:bg-slate-50/70"
                    >
                      <span
                        aria-hidden="true"
                        className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-emerald-50 text-xs font-extrabold text-emerald-800"
                      >
                        Rx
                      </span>

                      <div className="min-w-0 flex-1">
                        <h5 className="break-words text-sm font-bold text-slate-900">
                          {candidate.brand_name}
                        </h5>

                        <p className="mt-1 break-words text-xs leading-5 text-slate-600">
                          {candidate.generic_name || "Generic name unavailable"}
                        </p>

                        {strength && (
                          <p className="mt-1 break-words text-xs leading-5 text-slate-500">
                            Strength: {strength}
                          </p>
                        )}

                        <div className="mt-3">
                          <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
                            <span className="text-[11px] font-semibold text-slate-600">
                              Similarity score
                            </span>

                            <span
                              className={`text-xs font-bold ${lowConfidence
                                ? "text-amber-700"
                                : "text-emerald-700"
                                }`}
                            >
                              {validScore
                                ? `${score.toFixed(1)}%`
                                : "Unavailable"}
                            </span>
                          </div>

                          <div
                            className="h-1.5 overflow-hidden rounded-full bg-slate-100"
                            role="progressbar"
                            aria-label={`${candidate.brand_name} text similarity score`}
                            aria-valuemin={0}
                            aria-valuemax={100}
                            aria-valuenow={displayedScore}
                          >
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${lowConfidence
                                ? "bg-amber-500"
                                : "bg-emerald-500"
                                }`}
                              style={{ width: `${displayedScore}%` }}
                            />
                          </div>
                        </div>

                        <p
                          className={`mt-2 break-words text-[11px] leading-5 ${lowConfidence
                            ? "text-amber-700"
                            : "text-slate-500"
                            }`}
                        >
                          {!validScore
                            ? "Score unavailable. Verify the medicine details carefully."
                            : lowConfidence
                              ? "Lower similarity. Carefully verify the brand, ingredients, strength, and dosage form."
                              : "Possible match only. Verify the medicine details before adding."}
                        </p>

                        <button
                          type="button"
                          className="mt-3 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-xl border border-emerald-200 px-3 py-2 text-xs font-bold text-emerald-800 transition hover:bg-emerald-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-400 sm:w-auto"
                          onClick={() => {
                            if (lowConfidence) {
                              const confirmed = window.confirm(
                                `The similarity score for "${candidate.brand_name}" is ${validScore
                                  ? `${score.toFixed(1)}%`
                                  : "unavailable"
                                }. Verify the medicine name, active ingredients, strength, and packaging. Add this candidate anyway?`,
                              );

                              if (!confirmed) return;
                            }

                            onSelectCandidate(candidate);
                          }}
                          disabled={cannotAdd}
                          aria-label={`Confirm and add ${candidate.brand_name}`}
                          title={
                            alreadySelected
                              ? "Already selected"
                              : limitReached
                                ? "Maximum of five medicines reached"
                                : "Confirm and add this medicine"
                          }
                        >
                          <span aria-hidden="true">
                            {alreadySelected ? "✓" : "+"}
                          </span>

                          {alreadySelected
                            ? "Already added"
                            : limitReached
                              ? "Selection limit reached"
                              : "Confirm and add"}
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}