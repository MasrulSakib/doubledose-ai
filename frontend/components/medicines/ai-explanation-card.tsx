"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { AIExplanationResponse } from "@/types/ai-explanation";

interface AIExplanationCardProps {
  explanation: AIExplanationResponse | null;
  loading: boolean;
  error: string | null;
}

export default function AIExplanationCard({
  explanation,
  loading,
  error,
}: AIExplanationCardProps) {
  return (
    <section
      className="min-w-0 rounded-2xl border border-emerald-100 bg-white p-5 shadow-sm sm:p-6"
      aria-labelledby="ai-explanation-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[10px] font-extrabold tracking-[1.6px] text-emerald-700">
            AI-POWERED INSIGHT
          </p>
          <h2
            id="ai-explanation-heading"
            className="mt-2 text-lg font-bold tracking-tight text-emerald-950 sm:text-xl"
          >
            Understanding your results
          </h2>
        </div>
        <span className="inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-800">
          Groq AI
        </span>
      </div>

      {loading && (
        <div
          className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50/70 p-5"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          <div className="flex items-start gap-3">
            <span
              aria-hidden="true"
              className="mt-1 h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-700"
            />
            <div>
              <p className="font-semibold text-emerald-950">
                AI is generating your medicine report...
              </p>
              <p className="mt-1 text-sm leading-6 text-emerald-800">
                Preparing a detailed comparison from the medicine records
                supplied to this report. Temporary connection issues may
                trigger an automatic retry.
              </p>
            </div>
          </div>
        </div>
      )}

      {!loading && error && (
        <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4" role="alert">
          <p className="font-semibold text-red-900">
            Unable to generate the AI report.
          </p>
          <p className="mt-2 break-words text-sm leading-6 text-red-800">
            {error}
          </p>
          <p className="mt-3 text-sm leading-6 text-red-700">
            Your ingredient comparison remains available. Run the comparison
            again to retry report generation.
          </p>
        </div>
      )}

      {!loading && !error && !explanation && (
        <p className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-600">
          Select at least two medicines and check their ingredient overlap to
          generate an AI report.
        </p>
      )}

      {!loading && !error && explanation && (
        <div className="mt-5 min-w-0 space-y-5">
          <div
            className={[
              "min-w-0 text-sm leading-7 text-slate-700",
              "[&_h1]:mb-3 [&_h1]:mt-6 [&_h1]:text-xl [&_h1]:font-extrabold [&_h1]:text-emerald-950",
              "[&_h2]:mb-3 [&_h2]:mt-6 [&_h2]:text-lg [&_h2]:font-bold [&_h2]:text-emerald-950",
              "[&_h3]:mb-2 [&_h3]:mt-5 [&_h3]:text-base [&_h3]:font-bold [&_h3]:text-slate-900",
              "[&_p]:my-3",
              "[&_ul]:my-3 [&_ul]:list-disc [&_ul]:space-y-2 [&_ul]:pl-6",
              "[&_ol]:my-3 [&_ol]:list-decimal [&_ol]:space-y-2 [&_ol]:pl-6",
              "[&_li]:pl-1",
              "[&_strong]:font-bold [&_strong]:text-slate-900",
              "[&_hr]:my-5 [&_hr]:border-slate-200",
              "[&_blockquote]:my-4 [&_blockquote]:border-l-4 [&_blockquote]:border-emerald-200 [&_blockquote]:pl-4 [&_blockquote]:text-slate-600",
            ].join(" ")}
          >
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ children }) => (
                  <div className="my-4 max-w-full overflow-x-auto rounded-xl border border-slate-200">
                    <table className="w-full min-w-[760px] border-collapse text-left text-xs sm:text-sm">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => (
                  <thead className="bg-emerald-50 text-emerald-950">{children}</thead>
                ),
                tbody: ({ children }) => (
                  <tbody className="divide-y divide-slate-200">{children}</tbody>
                ),
                tr: ({ children }) => <tr className="even:bg-slate-50/70">{children}</tr>,
                th: ({ children }) => (
                  <th className="border-b border-emerald-100 px-4 py-3 font-bold">{children}</th>
                ),
                td: ({ children }) => (
                  <td className="px-4 py-3 align-top leading-6 text-slate-700">{children}</td>
                ),
              }}
            >
              {explanation.explanation}
            </ReactMarkdown>
          </div>

          {explanation.limitations.length > 0 && (
            <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4">
              <h3 className="text-sm font-bold text-amber-950">
                Important limitations
              </h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-amber-900 marker:text-amber-600">
                {explanation.limitations.map((limitation, index) => (
                  <li key={`${index}-${limitation}`}>{limitation}</li>
                ))}
              </ul>
            </div>
          )}

          <p className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs leading-6 text-slate-600">
            {explanation.disclaimer}
          </p>
        </div>
      )}
    </section>
  );
}
