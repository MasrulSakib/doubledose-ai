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
      className="rounded-2xl border border-slate-200/80 bg-white/95 p-5 shadow-sm backdrop-blur-sm transition-all sm:p-6"
    >
      <div>
        <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider text-emerald-700">
          Step 2
        </div>

        <h2
          id="overlap-results-heading"
          className="mt-2 text-lg font-semibold tracking-tight text-slate-900"
        >
          Ingredient overlap analysis
        </h2>

        <p className="mt-1 text-sm leading-6 text-slate-500">
          Review the active ingredient comparison and the AI-assisted explanation below.
        </p>
      </div>

      {loading && (
        <div
          role="status"
          className="mt-5 flex items-center gap-3 rounded-xl border border-emerald-100 bg-emerald-50/60 p-4 text-sm text-emerald-800"
        >
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
          Checking ingredients and preparing your results...
        </div>
      )}

      {error && (
        <p
          role="alert"
          className="mt-5 rounded-xl border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-700"
        >
          {error}
        </p>
      )}

      {children && <div className="mt-5 space-y-4">{children}</div>}

      {explanation && <div className="mt-5">{explanation}</div>}
    </section>
  );
}
