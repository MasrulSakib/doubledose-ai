"use client";

import type { OCRMatchResultsProps } from "@/types/ocr";

export default function OCRMatchResults({
  extractedText,
  onExtractedTextChange,
  matches,
  onSelectMatch,
  selectedMedicineIds,
  matching = false,
  error = null,
}: OCRMatchResultsProps) {
  return (
    <section
      aria-labelledby="ocr-results-heading"
      className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6"
    >
      <div>
        <p className="text-[10px] font-extrabold tracking-[.14em] text-emerald-700 uppercase">
          OCR results
        </p>
        <h2
          id="ocr-results-heading"
          className="mt-1.5 text-lg font-bold text-slate-900"
        >
          Review extracted medicine details
        </h2>
        <p className="mt-1 text-sm leading-6 text-slate-500">
          Check the extracted text and verify the suggested medicine before
          adding it to your selection.
        </p>
      </div>

      <label
        htmlFor="ocr-extracted-text"
        className="mt-5 block text-sm font-medium text-slate-700"
      >
        Extracted text
      </label>

      <textarea
        id="ocr-extracted-text"
        value={extractedText}
        onChange={(e) => onExtractedTextChange(e.target.value)}
        rows={5}
        placeholder="Extracted medicine text will appear here..."
        className="mt-2 w-full resize-y rounded-xl border border-slate-200 bg-slate-50/50 p-3 text-sm leading-6 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10"
      />

      <p className="mt-2 text-xs text-slate-500">
        Correct misspelled medicine names or other OCR errors before matching.
      </p>

      {error && (
        <p
          role="alert"
          className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800"
        >
          {error}
        </p>
      )}

      {matching && (
        <p
          role="status"
          className="mt-4 flex items-center gap-2 text-sm text-slate-500"
        >
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-emerald-600" />
          Finding possible medicine matches...
        </p>
      )}

      {!matching && matches.length > 0 && (
        <div className="mt-5 space-y-3">
          <h3 className="text-sm font-semibold text-slate-900">
            Possible matches ({matches.length})
          </h3>

          <p className="text-xs leading-5 text-amber-700">
            Similarity scores indicate text matching, not medical certainty.
            Verify the medicine name and strength on the packaging.
          </p>

          {matches.map((candidate) => {
            const alreadySelected = selectedMedicineIds.includes(
              candidate.medicine_id,
            );
            const selectionLimitReached = selectedMedicineIds.length >= 5;
            const lowScore = candidate.match_score < 65;

            return (
              <article
                key={candidate.medicine_id}
                className="rounded-xl border border-slate-200 p-4 transition hover:border-emerald-200 hover:shadow-sm"
              >
                <div className="flex items-start gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-sm font-bold text-emerald-700">
                    Rx
                  </span>

                  <div className="min-w-0 flex-1">
                    <h4 className="break-words text-sm font-semibold text-slate-900">
                      {candidate.brand_name}
                    </h4>
                    <p className="mt-1 break-words text-sm text-slate-600">
                      {candidate.generic_name || "Generic name unavailable"}
                    </p>
                    {candidate.strength && (
                      <p className="mt-1 break-words text-xs text-slate-500">
                        Strength: {candidate.strength}
                      </p>
                    )}


                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                        Text similarity: {candidate.match_score.toFixed(1)}%
                      </span>

                      {candidate.ranking_score !== undefined && (
                        <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
                          Ranking score: {candidate.ranking_score.toFixed(1)}
                        </span>
                      )}

                      <span className="text-xs text-amber-700">
                        Verify medicine name and strength
                      </span>
                    </div>

                  </div>

                  <button
                    type="button"
                    onClick={() => onSelectMatch(candidate)}
                    disabled={alreadySelected || selectionLimitReached}
                    aria-label={`Confirm and add ${candidate.brand_name}`}
                    className="shrink-0 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    {alreadySelected ? "Added" : "Add"}
                  </button>
                </div>
              </article>
            );
          })}

          {selectedMedicineIds.length >= 5 && (
            <p className="text-xs text-amber-700">
              Maximum of five medicines reached. Remove one before adding another.
            </p>
          )}
        </div>
      )}

      {!matching && extractedText.trim() && matches.length === 0 && !error && (
        <p className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
          No candidate matches are available. Review the extracted text and run
          the matching process again.
        </p>
      )}
    </section>
  );
}
