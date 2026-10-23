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
            className="mt-6 min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
            aria-live="polite"
        >
            <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                    <p className="mb-2 text-[10px] font-extrabold tracking-[1.4px] text-emerald-700">
                        YOUR RESULTS
                    </p>
                    <h2 className="text-xl font-bold tracking-tight text-emerald-950">
                        Ingredient comparison
                    </h2>
                    <p className="mt-1.5 text-sm leading-6 text-slate-500">
                        Based on the ingredient records currently available.
                    </p>
                </div>

                <span
                    className={`inline-flex w-fit shrink-0 items-center rounded-full border px-3 py-1.5 text-xs font-bold ${status.badge}`}
                >
                    <span
                        className="mr-2 h-2 w-2 rounded-full bg-current"
                        aria-hidden="true"
                    />
                    {status.label}
                </span>
            </div>

            {result.result_status === "overlap_found" && (
                <div className="mb-6 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-amber-100 text-sm font-extrabold text-amber-800">
                        !
                    </span>
                    <div>
                        <h3 className="text-sm font-bold text-amber-950">
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
                <div className="mb-6 flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-emerald-100 text-sm font-extrabold text-emerald-800">
                        ✓
                    </span>
                    <div>
                        <h3 className="text-sm font-bold text-emerald-950">
                            No shared ingredients were found in the available records.
                        </h3>
                        <p className="mt-1 text-sm leading-6 text-emerald-900">
                            This does not establish that the combination is safe. Ingredient
                            records may be incomplete.
                        </p>
                    </div>
                </div>
            )}

            {result.result_status === "incomplete_data" && (
                <div className="mb-6 flex items-start gap-3 rounded-xl border border-orange-200 bg-orange-50 p-4">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-orange-100 text-sm font-extrabold text-orange-800">
                        !
                    </span>
                    <div>
                        <h3 className="text-sm font-bold text-orange-950">
                            We couldn’t verify all selected medicines.
                        </h3>
                        <p className="mt-1 text-sm leading-6 text-orange-900">
                            Some medicines have no ingredient records, so the comparison
                            may be incomplete.
                        </p>
                    </div>
                </div>
            )}

            {result.overlapping_ingredients.length > 0 ? (
                <div className="mb-6">
                    <div className="mb-3">
                        <h3 className="text-base font-bold text-slate-900">
                            Shared active ingredients
                        </h3>
                        <p className="mt-1 text-xs leading-5 text-slate-500">
                            Ingredients appearing in more than one selected medicine.
                        </p>
                    </div>

                    <div className="space-y-3">
                        {result.overlapping_ingredients.map((ingredient) => (
                            <article
                                className="flex min-w-0 items-start gap-3 rounded-xl border border-amber-200 bg-amber-50/50 p-4"
                                key={ingredient.ingredient_id}
                            >
                                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-amber-100 text-sm font-extrabold text-amber-800">
                                    !
                                </span>

                                <div className="min-w-0 flex-1">
                                    <h4 className="break-words text-sm font-bold text-slate-900">
                                        {ingredient.name}
                                    </h4>
                                    <p className="mt-1 text-xs leading-5 text-slate-500">
                                        Appears in these selected medicines
                                    </p>

                                    <div className="mt-3 flex flex-wrap gap-2">
                                        {ingredient.medicine_names.map((name, index) => (
                                            <span
                                                className="max-w-full break-words rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700"
                                                key={`${name}-${index}`}
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
            ) : (
                result.result_status !== "incomplete_data" && (
                    <div className="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-600">
                        No shared ingredients were identified in the records checked.
                    </div>
                )
            )}

            {result.medicines_without_ingredient_data.length > 0 && (
                <div className="mb-6 rounded-xl border border-orange-200 bg-orange-50 p-4">
                    <h3 className="text-sm font-bold text-orange-950">
                        Ingredient data unavailable for:
                    </h3>
                    <ul className="mt-2 list-inside list-disc space-y-1 text-sm leading-6 text-orange-900">
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

            <div className="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs leading-6 text-slate-600">
                <strong className="text-slate-800">Important:</strong> DoubleDose AI
                checks for shared ingredients in available database records. It does
                not assess all drug interactions, determine appropriate doses, or
                establish whether a medicine combination is safe. Consult a qualified
                healthcare professional.
            </div>

            <AIExplanationCard
                explanation={aiExplanation}
                loading={aiLoading}
                error={aiError}
            />
        </section>
    );
}