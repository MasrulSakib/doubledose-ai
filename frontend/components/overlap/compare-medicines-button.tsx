
"use client";

type CompareMedicinesButtonProps = {
    selectedCount: number;
    loading: boolean;
    onClick: () => void;
};

export default function CompareMedicinesButton({
    selectedCount,
    loading,
    onClick,
}: CompareMedicinesButtonProps) {
    const canCompare = selectedCount >= 2 && selectedCount <= 5 && !loading;

    return (
        <button
            type="button"
            onClick={onClick}
            disabled={!canCompare}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-teal-600 px-5 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500 sm:w-auto"
        >
            {loading ? (
                <>
                    <span
                        aria-hidden="true"
                        className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
                    />
                    Comparing medicines...
                </>
            ) : (
                <>
                    Compare medicines
                    <span aria-hidden="true">→</span>
                </>
            )}
        </button>
    );
}
