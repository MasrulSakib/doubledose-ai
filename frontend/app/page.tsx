"use client";

import { useAppDispatch, useAppSelector } from "@/lib/hooks";
import {
  addMedicine,
  removeMedicine,
  clearMedicines,
} from "@/lib/features/medicines/medicineSlice";

import SiteHeader from "@/components/layout/site-header";
import SiteFooter from "@/components/layout/site-footer";
import HeroSection from "@/components/layout/hero-section";
import MedicineSearch from "@/components/medicines/medicine-search";
import SelectedMedicines from "@/components/medicines/selected-medicines";
import OCRUpload from "@/components/ocr/ocr-upload";
import MatcherComparison from "@/components/ocr/matcher-comparison";
import IngredientResults from "@/components/overlap/ingredient-results";

import useMedicineOCR from "@/hooks/use-medicine-ocr";
import useMedicineSearch from "@/hooks/use-medicine-search";
import useMedicineOverlap from "@/hooks/use-medicine-overlap";

import type { Medicine } from "@/types/medicine";
import type { OCRMedicineMatch } from "@/types/ocr";

export default function Home() {
  const dispatch = useAppDispatch();

  const selectedMedicines = useAppSelector(
    (state) => state.medicines.selectedMedicines,
  );

  const search = useMedicineSearch();
  const ocr = useMedicineOCR();
  const overlap = useMedicineOverlap();

  const selectedMedicineIds = selectedMedicines.map(
    (medicine) => medicine.id,
  );

  const canCheck =
    selectedMedicines.length >= 2 && selectedMedicines.length <= 5;

  function handleAddMedicine(medicine: Medicine) {
    if (
      selectedMedicines.some((item) => item.id === medicine.id) ||
      selectedMedicines.length >= 5
    ) {
      return;
    }

    dispatch(addMedicine(medicine));
    search.clearSearch();
    overlap.resetResults();
  }

  function handleRemoveMedicine(id: number) {
    dispatch(removeMedicine(id));
    overlap.resetResults();
  }

  function handleAddOCRCandidate(candidate: OCRMedicineMatch) {
    const medicine: Medicine = {
      id: candidate.medicine_id,
      brand_name: candidate.brand_name,
      generic_name: candidate.generic_name,
      source_display_name: candidate.strength,
    };

    handleAddMedicine(medicine);
  }

  function handleClearMedicines() {
    dispatch(clearMedicines());
    overlap.resetResults();
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <SiteHeader />

      <HeroSection />

      <section
        id="medicine-checker"
        className="mx-auto w-[calc(100%-2rem)] max-w-290 scroll-mt-24 pb-12 sm:w-[calc(100%-3rem)] sm:pb-16"
      >
        <div className="mb-7">
          <p className="text-[10px] font-extrabold tracking-[1.6px] text-emerald-700">
            MEDICINE SAFETY WORKSPACE
          </p>

          <h2 className="mt-2 text-2xl font-extrabold tracking-tight text-emerald-950 sm:text-3xl">
            Check your medicines
          </h2>

          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-500 sm:text-base">
            Search the medicine database or upload a package image to identify
            possible ingredient overlaps.
          </p>
        </div>

        {/* OCR image upload */}
        <div className="space-y-5">
          <OCRUpload
            previewUrl={ocr.ocrPreviewUrl}
            extracting={ocr.ocrLoading}
            onFileSelect={ocr.handleOCRFileChange}
            onExtract={() => void ocr.processOCR()}
            error={ocr.ocrError}
          />

          {ocr.ocrMessage && (
            <p
              className="rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm leading-6 text-emerald-800"
              role="status"
            >
              {ocr.ocrMessage}
            </p>
          )}
        </div>

        {/* Review and edit extracted OCR text */}
        {ocr.ocrText && (
          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <label
              htmlFor="ocr-extracted-text"
              className="mb-3 block text-sm font-bold text-slate-800"
            >
              Review extracted text
            </label>

            <textarea
              id="ocr-extracted-text"
              className="min-h-32 w-full resize-y rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
              rows={5}
              value={ocr.ocrText}
              onChange={(event) => ocr.setOcrText(event.target.value)}
              placeholder="Extracted medicine text appears here..."
            />

            <button
              type="button"
              className="mt-4 inline-flex min-h-11 items-center justify-center rounded-lg border border-emerald-200 bg-white px-4 py-2 text-sm font-bold text-emerald-800 transition hover:bg-emerald-50 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() => void ocr.rematchEditedOCRText()}
              disabled={ocr.ocrLoading || !ocr.ocrText.trim()}
            >
              {ocr.ocrLoading
                ? "Matching medicines..."
                : "Match edited text"}
            </button>
          </section>
        )}

        {/* OCR matcher candidates */}
        {ocr.matcherComparison && (
          <section className="mt-6">
            <MatcherComparison
              comparison={ocr.matcherComparison}
              selectedMedicineIds={selectedMedicineIds}
              onSelectCandidate={handleAddOCRCandidate}
              selectedCount={selectedMedicines.length}
            />
          </section>
        )}

        {/* Manual medicine search */}
        <div className="mt-6">
          <MedicineSearch
            query={search.query}
            onQueryChange={search.updateQuery}
            results={search.searchResults}
            onSelect={handleAddMedicine}
            selectedMedicineIds={selectedMedicineIds}
            searching={search.searching}
            error={search.searchError}
            maxMedicines={5}
          />
        </div>

        {/* Selected medicines */}
        <section className="mt-6">
          <SelectedMedicines
            medicines={selectedMedicines}
            onRemove={handleRemoveMedicine}
            maxMedicines={5}
          />

          <div className="mt-5 flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
            <button
              type="button"
              className="inline-flex min-h-11 items-center justify-center rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-600 transition hover:border-red-200 hover:bg-red-50 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={handleClearMedicines}
              disabled={selectedMedicines.length === 0}
            >
              Clear all
            </button>

            <button
              type="button"
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-emerald-700 px-5 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-emerald-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none"
              onClick={() =>
                void overlap.checkOverlap(selectedMedicines)
              }
              disabled={!canCheck || overlap.checking}
            >
              {overlap.checking && (
                <span
                  aria-hidden="true"
                  className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
                />
              )}
              {overlap.checking
                ? "Checking ingredients..."
                : "Check ingredient overlap"}
            </button>
          </div>

          {!canCheck && selectedMedicines.length > 0 && (
            <p className="mt-3 text-sm leading-6 text-slate-500">
              Add at least one more medicine to start the comparison.
            </p>
          )}

          {overlap.checkError && (
            <p
              className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-800"
              role="alert"
            >
              {overlap.checkError}
            </p>
          )}
        </section>

        {/* Overlap results and AI explanation */}
        {overlap.result && (
          <section
            id="overlap-results"
            className="mt-8 scroll-mt-24 space-y-5"
          >
            <IngredientResults
              result={overlap.result}
              selected={selectedMedicines}
              aiExplanation={overlap.aiExplanation}
              aiLoading={overlap.aiLoading}
              aiError={overlap.aiError}
            />
          </section>
        )}
      </section>

      <SiteFooter />
    </main>
  );
}