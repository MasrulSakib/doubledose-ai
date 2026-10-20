
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
        <section className="ai-explanation" aria-live="polite">
            <div className="ai-explanation__header">
                <div>
                    <p className="ai-explanation__eyebrow">AI-POWERED INSIGHT</p>
                    <h2>Understanding your results</h2>
                </div>

                <span className="ai-explanation__badge">Groq AI</span>
            </div>

            {loading && (
                <div className="ai-explanation__status" role="status">
                    Generating an explanation of your results...
                </div>
            )}

            {!loading && error && (
                <div className="ai-explanation__error" role="alert">
                    <p>{error}</p>
                    <p>
                        Your ingredient comparison results remain available.
                        You can try generating the explanation again.
                    </p>
                </div>
            )}

            {!loading && !error && !explanation && (
                <p className="ai-explanation__empty">
                    Check your selected medicines to generate an explanation.
                </p>
            )}

            {!loading && explanation && (
                <div className="ai-explanation__content">
                    <p>{explanation.explanation}</p>

                    {explanation.limitations.length > 0 && (
                        <div className="ai-explanation__limitations">
                            <h3>Important limitations</h3>
                            <ul>
                                {explanation.limitations.map((limitation, index) => (
                                    <li key={`${index}-${limitation}`}>{limitation}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <p className="ai-explanation__disclaimer">
                        {explanation.disclaimer}
                    </p>
                </div>
            )}
        </section>
    );
}
