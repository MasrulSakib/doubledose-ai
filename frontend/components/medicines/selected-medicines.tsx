"use client";

import MedicineCard from "@/components/medicines/medicine-card";
import type { Medicine } from "@/types/medicine";

type SelectedMedicinesProps = {
    medicines: Medicine[];
    onRemove: (medicineId: number) => void;
    maxMedicines?: number;
};

export default function SelectedMedicines({
    medicines,
    onRemove,
    maxMedicines = 5,
}: SelectedMedicinesProps) {
    const remaining = Math.max(0, maxMedicines - medicines.length);

    return (
        <section className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                    <h3 className="text-base font-bold text-emerald-950">
                        Selected medicines
                    </h3>
                    <p className="mt-1.5 text-xs leading-5 text-slate-500">
                        Choose 2–{maxMedicines} medicines to check for ingredient overlap.
                    </p>
                </div>

                <span className="shrink-0 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-800">
                    {medicines.length}/{maxMedicines}
                </span>
            </div>

            {medicines.length === 0 ? (
                <div className="flex min-h-44 flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center">
                    <span className="mb-4 grid h-10 w-10 place-items-center rounded-full bg-white text-xl text-emerald-700 shadow-sm">
                        +
                    </span>
                    <p className="text-sm font-semibold text-slate-700">
                        No medicines selected yet
                    </p>
                    <p className="mt-1.5 text-xs leading-5 text-slate-500">
                        Search for a medicine and add it here.
                    </p>
                </div>
            ) : (
                <div className="flex flex-col gap-3">
                    {medicines.map((medicine, index) => (
                        <div
                            key={medicine.id}
                            className="flex min-w-0 items-start gap-3 rounded-xl border border-slate-200 bg-white p-3"
                        >
                            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-emerald-50 text-xs font-bold text-emerald-800">
                                {index + 1}
                            </span>

                            <div className="min-w-0 flex-1">
                                <p className="break-words text-sm font-semibold text-slate-800">
                                    {medicine.brand_name}
                                </p>
                                <p className="mt-1 break-words text-xs leading-5 text-slate-500">
                                    {medicine.generic_name || "Ingredient information unavailable"}
                                </p>
                                {medicine.manufacturer && (
                                    <p className="mt-1 break-words text-[11px] text-slate-400">
                                        {medicine.manufacturer}
                                    </p>
                                )}
                            </div>

                            <button
                                type="button"
                                onClick={() => onRemove(medicine.id)}
                                aria-label={`Remove ${medicine.brand_name}`}
                                className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-xl text-slate-400 transition hover:bg-red-50 hover:text-red-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-500"
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>
            )}

            <div className="mt-4 flex items-center justify-between gap-3 text-[11px] text-slate-500">
                <span>
                    {remaining > 0
                        ? `${remaining} more ${remaining === 1 ? "medicine" : "medicines"} can be added`
                        : "Selection limit reached"}
                </span>

                {medicines.length < 2 && (
                    <span className="text-amber-700">Select at least 2</span>
                )}
            </div>
        </section>
    );
}
