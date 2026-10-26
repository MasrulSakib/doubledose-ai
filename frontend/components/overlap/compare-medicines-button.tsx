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
      className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-5 py-3 text-sm font-semibold text-white shadow-md shadow-emerald-600/20 transition-all hover:from-emerald-700 hover:to-teal-700 hover:shadow-lg hover:shadow-emerald-600/25 active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none disabled:active:scale-100 sm:w-auto"
    >
      {loading ? (
        <>
          <span
            aria-hidden="true"
            className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"
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
