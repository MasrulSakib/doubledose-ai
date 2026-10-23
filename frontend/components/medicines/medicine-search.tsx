
"use client";

import type { Medicine } from "@/types/medicine";

type MedicineSearchProps = {
    query: string;
    onQueryChange: (query: string) => void;
    results: Medicine[];
    onSelect: (medicine: Medicine) => void;
    selectedMedicineIds: number[];
    searching: boolean;
    error?: string | null;
    maxMedicines?: number;
};

/**
 * Extract the strength from the existing database display string.
 *
 * Example:
 * "BDDrugBank ID: 10452 | Generic: Paracetamol |
 *  Strength: 500 mg | Slug: napatablet500-mg"
 */
function getMedicineStrength(
    sourceDisplayName?: string | null,
): string | null {
    if (!sourceDisplayName) {
        return null;
    }

    const match = sourceDisplayName.match(
        /(?:^|\|)\s*Strength:\s*([^|]+)/i,
    );

    return match?.[1]?.trim() || null;
}

/**
 * Preserve the complete source display string so that database metadata
 * remains accessible even when its strength cannot be parsed.
 */
function hasAdditionalSourceDetails(
    sourceDisplayName?: string | null,
): boolean {
    return Boolean(sourceDisplayName?.trim());
}

export default function MedicineSearch({
    query,
    onQueryChange,
    results,
    onSelect,
    selectedMedicineIds,
    searching,
    error,
    maxMedicines = 5,
}: MedicineSearchProps) {
    const selectedSet = new Set(selectedMedicineIds);
    const trimmedQuery = query.trim();
    const canSearch = trimmedQuery.length >= 2;
    const atLimit = selectedMedicineIds.length >= maxMedicines;

    return (
        <section className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <div className="mb-6">
                <p className="mb-2 text-[10px] font-extrabold tracking-[1.4px] text-emerald-700">
                    STEP 1
                </p>

                <h3 className="text-base font-bold text-emerald-950">
                    Find your medicines
                </h3>

                <p className="mt-1.5 text-xs leading-5 text-slate-500">
                    Search by brand name or medicine name, then add it to your list.
                </p>
            </div>

            <label
                htmlFor="medicine-search"
                className="mb-2 block text-xs font-semibold text-slate-700"
            >
                Medicine name
            </label>

            <div className="flex h-12 items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 transition focus-within:border-emerald-500 focus-within:ring-4 focus-within:ring-emerald-500/10">
                <svg
                    aria-hidden="true"
                    viewBox="0 0 24 24"
                    fill="none"
                    className="h-5 w-5 shrink-0 text-slate-400"
                >
                    <circle
                        cx="10.8"
                        cy="10.8"
                        r="6.8"
                        stroke="currentColor"
                        strokeWidth="1.7"
                    />
                    <path
                        d="m16 16 4.2 4.2"
                        stroke="currentColor"
                        strokeWidth="1.7"
                        strokeLinecap="round"
                    />
                </svg>

                <input
                    id="medicine-search"
                    type="search"
                    value={query}
                    onChange={(event) => onQueryChange(event.target.value)}
                    placeholder="e.g. Napa, Seclo, Renova Plus"
                    autoComplete="off"
                    aria-describedby="medicine-search-hint"
                    className="h-full min-w-0 flex-1 bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-400"
                />

                {searching && (
                    <span
                        role="status"
                        aria-label="Searching medicines"
                        className="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-emerald-100 border-t-emerald-700"
                    />
                )}
            </div>

            <p
                id="medicine-search-hint"
                className="mt-2 text-[11px] leading-5 text-slate-500"
            >
                Enter at least 2 characters to search the medicine database.
            </p>

            {error && (
                <div
                    role="alert"
                    className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-xs leading-5 text-red-800"
                >
                    {error}
                </div>
            )}

            {canSearch && !searching && !error && results.length === 0 && (
                <p className="mt-4 rounded-lg bg-slate-50 p-4 text-xs leading-5 text-slate-500">
                    No matching medicines found. Try a different brand name or spelling.
                </p>
            )}

            {results.length > 0 && (
                <div className="mt-4 overflow-hidden rounded-xl border border-slate-200">
                    <div className="bg-slate-50 px-4 py-3 text-[10px] font-bold tracking-wider text-slate-500">
                        SEARCH RESULTS ({results.length})
                    </div>

                    <div className="divide-y divide-slate-100">
                        {results.map((medicine) => {
                            const alreadySelected = selectedSet.has(medicine.id);
                            const strength = getMedicineStrength(
                                medicine.source_display_name,
                            );

                            const hasSourceDetails = hasAdditionalSourceDetails(
                                medicine.source_display_name,
                            );

                            return (
                                <div
                                    key={medicine.id}
                                    className="flex min-w-0 items-start gap-3 p-3 transition hover:bg-emerald-50/50"
                                >
                                    <div className="mt-1 grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-emerald-50 text-xs font-bold text-emerald-700">
                                        {medicine.brand_name.slice(0, 2).toUpperCase()}
                                    </div>

                                    <div className="min-w-0 flex-1">
                                        <p className="break-words text-sm font-semibold text-slate-800">
                                            {medicine.brand_name}
                                        </p>

                                        <p className="mt-1 break-words text-xs leading-5 text-slate-500">
                                            {medicine.generic_name ||
                                                "Ingredient information unavailable"}
                                        </p>

                                        {/* Restore the product strength and dosage form. */}
                                        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs leading-5 text-slate-600">
                                            {strength && (
                                                <span>
                                                    <span className="font-semibold text-slate-700">
                                                        Strength:
                                                    </span>{" "}
                                                    {strength}
                                                </span>
                                            )}

                                            {medicine.dosage_form && (
                                                <span>
                                                    <span className="font-semibold text-slate-700">
                                                        Form:
                                                    </span>{" "}
                                                    {medicine.dosage_form}
                                                </span>
                                            )}

                                            {!strength && !medicine.dosage_form && (
                                                <span className="text-amber-700">
                                                    Strength and formulation not specified in the
                                                    displayed record.
                                                </span>
                                            )}
                                        </div>

                                        {medicine.manufacturer && (
                                            <p className="mt-1.5 break-words text-[11px] leading-5 text-slate-400">
                                                {medicine.manufacturer}
                                            </p>
                                        )}

                                        {/* Keep all original source metadata accessible. */}
                                        {hasSourceDetails && (
                                            <details className="mt-2 text-[11px] text-slate-500">
                                                <summary className="w-fit cursor-pointer font-medium transition hover:text-emerald-700">
                                                    Database record details
                                                </summary>

                                                <p className="mt-2 break-words rounded-lg bg-slate-50 p-2 leading-5">
                                                    {medicine.source_display_name}
                                                </p>
                                            </details>
                                        )}
                                    </div>

                                    <button
                                        type="button"
                                        onClick={() => onSelect(medicine)}
                                        disabled={alreadySelected || atLimit}
                                        aria-label={
                                            alreadySelected
                                                ? `${medicine.brand_name} already selected`
                                                : atLimit
                                                    ? `Selection limit reached for ${medicine.brand_name}`
                                                    : `Add ${medicine.brand_name}${strength ? ` ${strength}` : ""
                                                    }`
                                        }
                                        className="mt-3 grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-emerald-200 bg-white text-xl text-emerald-700 transition hover:bg-emerald-700 hover:text-white disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-50 disabled:text-slate-400"
                                    >
                                        {alreadySelected ? "✓" : "+"}
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {atLimit && (
                <p className="mt-3 text-xs text-amber-700">
                    You have reached the limit of {maxMedicines} selected medicines.
                </p>
            )}
        </section>
    );
}
