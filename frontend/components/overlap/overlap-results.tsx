
"use client";

import type { ReactNode } from "react";

type OverlapResultsProps = {
    children?: ReactNode;
    explanation?: ReactNode;
    loading?: boolean;
    error?: string | null;
};

export default function OverlapResults({
    children,
    explanation,
    loading = false,
    error = null,
}: OverlapResultsProps) {
    return (
        <section
            aria-labelledby="overlap-results-heading"
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
        >
            <div>
                <p className="text-sm font-semibold uppercase tracking-wider text-teal-700">
                    Step 2
                </p>

                <h2
                    id="overlap-results-heading"
                    className="mt-1 text-lg font-semibold text-slate-900"
                >
                    Ingredient overlap analysis
                </h2>

                <p className="mt-1 text-sm leading-6 text-slate-500">
                    Review the ingredient comparison and the AI-assisted explanation.
                </p>
            </div>

            {loading && (
                <div
                    role="status"
                    className="mt-5 flex items-center gap-3 rounded-xl bg-slate-50 p-4 text-sm text-slate-600"
                >
                    <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-teal-600" />
                    Checking ingredients and preparing your results...
                </div>
            )}

            {error && (
                <p
                    role="alert"
                    className="mt-5 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700"
                >
                    {error}
                </p>
            )}

            {children && <div className="mt-5 space-y-4">{children}</div>}

            {explanation && (
                <div className="mt-5">
                    {explanation}
                </div>
            )}
        </section>
    );
}
