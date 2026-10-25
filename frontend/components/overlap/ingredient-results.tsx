
"use client";

import type { Medicine } from "@/types/medicine";
import type { OverlapResult } from "@/types/overlap";
import type { AIExplanationResponse } from "@/types/ai-explanation";
import AIExplanationCard from "@/components/medicines/ai-explanation-card";

type IngredientResultsProps = {
  result: OverlapResult;
  selected: Medicine[];
  aiExplanation: AIExplanationResponse | null;
  aiLoading: boolean;
  aiError: string | null;
};

function medicineLabel(medicine: Medicine): string {
  return (
    medicine.brand_name ||
    medicine.generic_name ||
    `Medicine ${medicine.id}`
  );
}

export default function IngredientResults({
  result,
  selected,
  aiExplanation,
  aiLoading,
  aiError,
}: IngredientResultsProps) {
  const statusStyles = {
    overlap_found: {
      label: "Overlap found",
      badge: "border-amber-200 bg-amber-50 text-amber-800",
    },
    incomplete_data: {
      label: "Data incomplete",
      badge: "border-orange-200 bg-orange-50 text-orange-800",
    },
    no_overlap_found: {
      label: "No overlap found",
      badge: "border-emerald-200 bg-emerald-50 text-emerald-800",
    },
  } as const;

  const status = statusStyles[result.result_status];

  return (
    <section
      className="mt-6 min-w-0 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6"
      aria-labelledby="ingredient-comparison-heading"
    >
      <div className="mb-6 flex min-w-0 flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="mb-2 text-[10px] font-extrabold tracking-[1.4px] text-emerald-700">
            YOUR RESULTS
          </p>

          <h2
            id="ingredient-comparison-heading"
            className="break-words text-xl font-bold tracking-tight text-emerald-950"
          >
            Ingredient comparison
          </h2>

          <p className="mt-1.5 text-sm leading-6 text-slate-500">
            Based on the medicine records supplied to this comparison.
          </p>
        </div>

        <span
          className={`inline-flex w-fit max-w-full shrink-0 items-center rounded-full border px-3 py-1.5 text-xs font-bold ${status.badge}`}
        >
          <span
            className="mr-2 h-2 w-2 shrink-0 rounded-full bg-current"
            aria-hidden="true"
          />
          {status.label}
        </span>
      </div>

      {result.result_status === "overlap_found" && (
        <div className="mb-6 flex min-w-0 items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <span
            className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-amber-100 text-sm font-extrabold text-amber-800"
            aria-hidden="true"
          >
            !
          </span>

          <div className="min-w-0 flex-1">
            <h3 className="break-words text-sm font-bold text-amber-950">
              One or more shared ingredients were found.
            </h3>

            <p className="mt-1 text-sm leading-6 text-amber-900">
              Review the ingredients below with a pharmacist or healthcare
              professional before making medicine decisions.
            </p>
          </div>
        </div>
      )}

      {result.result_status === "no_overlap_found" && (
        <div className="mb-6 flex min-w-0 items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
          <span
            className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-emerald-100 text-sm font-extrabold text-emerald-800"
            aria-hidden="true"
          >
            ✓
          </span>

          <div className="min-w-0 flex-1">
            <h3 className="break-words text-sm font-bold text-emerald-950">
              No shared ingredients were found in the records checked.
            </h3>

            <p className="mt-1 text-sm leading-6 text-emerald-900">
              This does not establish that the combination is safe. Some
              product details may not have been retrieved for this comparison.
            </p>
          </div>
        </div>
      )}

      {result.has_incomplete_data && (
        <div className="mb-6 flex min-w-0 items-start gap-3 rounded-xl border border-orange-200 bg-orange-50 p-4">
          <span
            className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-orange-100 text-sm font-extrabold text-orange-800"
            aria-hidden="true"
          >
            !
          </span>

          <div className="min-w-0 flex-1">
            <h3 className="break-words text-sm font-bold text-orange-950">
              Some selected medicine data is incomplete.
            </h3>

            <p className="mt-1 text-sm leading-6 text-orange-900">
              Some medicine ingredient records are missing, so the comparison
              may be incomplete.
            </p>
          </div>
        </div>
      )}

      {result.overlapping_ingredients.length > 0 ? (
        <div className="mb-6 min-w-0">
          <div className="mb-3">
            <h3 className="text-base font-bold text-slate-900">
              Shared active ingredients
            </h3>

            <p className="mt-1 text-xs leading-5 text-slate-500">
              Ingredients listed in more than one selected medicine record.
            </p>
          </div>

          <div className="space-y-3">
            {result.overlapping_ingredients.map((ingredient) => (
              <article
                key={ingredient.ingredient_id}
                className="flex min-w-0 items-start gap-3 rounded-xl border border-amber-200 bg-amber-50/50 p-3 sm:p-4"
              >
                <span
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-amber-100 text-sm font-extrabold text-amber-800"
                  aria-hidden="true"
                >
                  !
                </span>

                <div className="min-w-0 flex-1">
                  <h4 className="break-words text-sm font-bold text-slate-900">
                    {ingredient.name}
                  </h4>

                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    Appears in these selected medicine records
                  </p>

                  <div className="mt-3 flex min-w-0 flex-wrap items-start gap-2">
                    {ingredient.medicine_names.map((name, index) => (
                      <span
                        key={`${name}-${index}`}
                        className="inline-flex max-w-full min-w-0 items-center whitespace-normal [overflow-wrap:anywhere] rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium leading-5 text-slate-700"
                      >
                        {name}
                      </span>
                    ))}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : result.result_status !== "incomplete_data" ? (
        <div className="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-600">
          No shared ingredients were identified in the records checked.
        </div>
      ) : null}

      {/* Possible same-class duplication — separate from exact overlap */}
      {result.same_class_warnings?.length > 0 && (
        <section className="mb-6 min-w-0 space-y-3">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Possible same-class duplication
            </h3>

            <p className="mt-1 text-xs leading-5 text-slate-500">
              Different active ingredients belonging to the same recorded
              therapeutic class. This is separate from an exact ingredient
              overlap.
            </p>
          </div>

          {result.same_class_warnings.map((warning, index) => (
            <article
              key={`${warning.therapeutic_class}-${index}`}
              className="min-w-0 rounded-xl border border-blue-200 bg-blue-50/60 p-4"
            >
              <div className="flex min-w-0 items-start gap-3">
                <span
                  aria-hidden="true"
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-blue-100 text-sm font-extrabold text-blue-800"
                >
                  i
                </span>

                <div className="min-w-0 flex-1">
                  <h4 className="break-words text-sm font-bold text-blue-950">
                    {warning.therapeutic_class}
                  </h4>

                  <p className="mt-2 text-sm leading-6 text-blue-900">
                    Different recorded active ingredients in this class were
                    found among the selected medicines.
                  </p>

                  <div className="mt-3 flex min-w-0 flex-wrap gap-2">
                    {warning.ingredient_names.map((name, ingredientIndex) => (
                      <span
                        key={`${name}-${ingredientIndex}`}
                        className="max-w-full min-w-0 whitespace-normal [overflow-wrap:anywhere] rounded-lg border border-blue-200 bg-white px-3 py-2 text-xs font-semibold leading-5 text-blue-900"
                      >
                        {name}
                      </span>
                    ))}
                  </div>

                  <p className="mt-3 text-xs font-semibold text-blue-950">
                    Medicines involved
                  </p>

                  <ul className="mt-1 list-inside list-disc space-y-1 break-words text-sm leading-6 text-blue-900">
                    {warning.medicine_names.map((name, medicineIndex) => (
                      <li key={`${name}-${medicineIndex}`}>{name}</li>
                    ))}
                  </ul>

                  <p className="mt-3 break-words text-sm leading-6 text-blue-900">
                    {warning.message}
                  </p>
                </div>
              </div>
            </article>
          ))}
        </section>
      )}

      {result.medicines_without_ingredient_data.length > 0 && (
        <div className="mb-6 min-w-0 rounded-xl border border-orange-200 bg-orange-50 p-4">
          <h3 className="break-words text-sm font-bold text-orange-950">
            Ingredient data unavailable in the current database for:
          </h3>

          <ul className="mt-2 list-inside list-disc space-y-1 break-words text-sm leading-6 text-orange-900">
            {result.medicines_without_ingredient_data.map((id) => {
              const medicine = selected.find((item) => item.id === id);

              return (
                <li key={id}>
                  {medicine ? medicineLabel(medicine) : `Medicine ID ${id}`}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <div className="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs leading-6 text-slate-600">
        <strong className="text-slate-800">Important:</strong> This comparison
        checks available records for shared ingredients. It does not assess
        every possible drug interaction, determine an individual dose, or
        establish whether a medicine combination is safe. Ask a qualified
        healthcare professional about medication concerns.
      </div>

      <AIExplanationCard
        explanation={aiExplanation}
        loading={aiLoading}
        error={aiError}
      />
    </section>
  );
}
