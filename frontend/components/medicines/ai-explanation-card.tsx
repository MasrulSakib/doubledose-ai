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
            className="rounded-2xl border border-emerald-100 bg-white p-5 shadow-sm sm:p-6"
            aria-live="polite"
        >
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                    <p className="text-[10px] font-extrabold tracking-[1.6px] text-emerald-700">
                        AI-POWERED INSIGHT
                    </p>
                    <h2 className="mt-2 text-lg font-bold tracking-tight text-emerald-950 sm:text-xl">
                        Understanding your results
                    </h2>
                </div>

                <span className="inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-800">
                    Groq AI
                </span>
            </div>

            {loading && (
                <div
                    className="mt-5 flex items-center gap-3 rounded-xl border border-emerald-100 bg-emerald-50/70 p-4 text-sm text-emerald-900"
                    role="status"
                >
                    <span
                        aria-hidden="true"
                        className="h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-700"
                    />
                    <p>Generating an explanation of your results...</p>
                </div>
            )}

            {!loading && error && (
                <div
                    className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
                    role="alert"
                >
                    <p className="font-semibold">Unable to generate the AI explanation.</p>
                    <p className="mt-2">{error}</p>
                    <p className="mt-3 leading-6 text-red-700">
                        Your ingredient comparison results remain available. You can try
                        generating the explanation again.
                    </p>
                </div>
            )}

            {!loading && !error && !explanation && (
                <p className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-600">
                    Check your selected medicines to generate an explanation.
                </p>
            )}

            {!loading && explanation && (
                <div className="mt-5 space-y-5">
                    <p className="text-sm leading-7 text-slate-700">
                        {explanation.explanation}
                    </p>

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