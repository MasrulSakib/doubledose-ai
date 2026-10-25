
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
    const match = candidate.strength?.match(
        /(?:\|\s*)?\*?Strength:\s*\*?(.*?)(?:\s*\||$)/i,
    );

    return match?.[1]?.trim() || null;
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
            candidates: comparison.rapidfuzz ?? [],
        },
        {
            name: "TF-IDF",
            description: "Text similarity matching",
            candidates: comparison.tfidf ?? [],
        },
    ];

    return (
        <section className="mt-5 min-w-0 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
            <div className="mb-5 flex min-w-0 flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                    <p className="mb-2 text-[10px] font-extrabold tracking-[1.4px] text-emerald-700">
                        MATCHING RESULTS
                    </p>

                    <h3 className="text-base font-bold text-emerald-950">
                        Medicine match candidates
                    </h3>

                    <p className="mt-1.5 text-xs leading-5 text-slate-500">
                        Compare suggestions from two matching methods and confirm the
                        medicine that matches your label.
                    </p>
                </div>

                <span className="inline-flex w-fit max-w-full shrink-0 items-center rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-800">
                    {selectedCount}/5 medicines selected
                </span>
            </div>

            <div className="mb-5 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
                Similarity scores measure text similarity, not the probability that a
                medicine is correct or proof of medical equivalence. Verify the brand,
                active ingredients, strength, and packaging before adding a candidate.
            </div>

            <div className="grid min-w-0 grid-cols-1 gap-5 xl:grid-cols-2">
                {sections.map(({ name, description, candidates }) => (
                    <div
                        className="min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-white"
                        key={name}
                    >
                        <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
                            <h4 className="text-sm font-bold text-slate-900">{name}</h4>

                            <p className="mt-1 text-xs text-slate-500">
                                {description} &middot; {candidates.length}{" "}
                                {candidates.length === 1 ? "candidate" : "candidates"}
                            </p>
                        </div>

                        {candidates.length === 0 ? (
                            <p className="p-4 text-sm leading-6 text-slate-500">
                                No candidates returned by this matcher.
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
                                    const strength = candidateStrength(candidate);
                                    const displayedScore = validScore ? score : 0;

                                    return (
                                        <article
                                            className="flex min-w-0 items-start gap-3 p-4 transition hover:bg-slate-50/70"
                                            key={`${name}-${candidate.medicine_id}`}
                                        >
                                            <span
                                                aria-hidden="true"
                                                className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-emerald-50 text-xs font-extrabold text-emerald-800"
                                            >
                                                Rx
                                            </span>

                                            <div className="min-w-0 flex-1">
                                                <h5 className="break-words text-sm font-bold text-slate-900">
                                                    {candidate.brand_name}
                                                </h5>

                                                <p className="mt-1 break-words text-xs leading-5 text-slate-600">
                                                    {candidate.generic_name ||
                                                        "Generic name unavailable"}
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
                                                            className={`h-full rounded-full ${lowConfidence
                                                                    ? "bg-amber-500"
                                                                    : "bg-emerald-600"
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
                                                            ? "Lower text similarity. Verify the medicine name, strength, and packaging carefully."
                                                            : "Possible text match only. Verify the medicine name, strength, and packaging before adding."}
                                                </p>

                                                <button
                                                    className="mt-3 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-lg border border-emerald-200 px-3 py-2 text-xs font-bold text-emerald-800 transition hover:bg-emerald-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-400 sm:w-auto"
                                                    type="button"
                                                    onClick={() => {
                                                        if (lowConfidence) {
                                                            const confirmed = window.confirm(
                                                                `This is ${validScore
                                                                    ? `a lower-similarity match (${score.toFixed(1)}%).`
                                                                    : "a match with an unavailable or invalid score."
                                                                } Verify the medicine name, strength, and packaging carefully. Add "${candidate.brand_name}" anyway?`,
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