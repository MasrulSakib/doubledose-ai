"use client";

import Image from "next/image";
import { useRef, useState } from "react";

type OCRUploadProps = {
  previewUrl: string | null;
  extracting: boolean;
  onFileSelect: (file: File | null) => void;
  onExtract: () => void;
  error?: string | null;
};

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

export default function OCRUpload({
  previewUrl,
  extracting,
  onFileSelect,
  onExtract,
  error,
}: OCRUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState("");
  const [validationError, setValidationError] = useState("");

  function handleFileChange(file: File | null) {
    setValidationError("");
    if (extracting) return;

    if (!file) {
      setFileName("");
      onFileSelect(null);
      return;
    }

    if (!ALLOWED_TYPES.includes(file.type)) {
      setFileName("");
      setValidationError("Please select a JPEG, PNG, or WebP image.");
      if (inputRef.current) inputRef.current.value = "";
      onFileSelect(null);
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setFileName("");
      setValidationError("The image must be 10 MB or smaller.");
      if (inputRef.current) inputRef.current.value = "";
      onFileSelect(null);
      return;
    }

    setFileName(file.name);
    onFileSelect(file);
  }

  function removeFile() {
    if (extracting) return;
    setFileName("");
    setValidationError("");
    if (inputRef.current) inputRef.current.value = "";
    onFileSelect(null);
  }

  return (
    <section className="min-w-0 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
      <div className="mb-5">
        <p className="mb-2 text-[10px] font-extrabold tracking-[.14em] text-emerald-700 uppercase">
          Optional
        </p>
        <h3 className="text-base font-bold text-slate-900">
          Scan a medicine label
        </h3>
        <p className="mt-1.5 text-xs leading-5 text-slate-500">
          Upload a clear photo of a medicine package or label to extract text
          and find possible matches.
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="sr-only"
        disabled={extracting}
        aria-label="Choose a medicine label image"
        onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
      />

      {!previewUrl ? (
        <button
          type="button"
          disabled={extracting}
          onClick={() => inputRef.current?.click()}
          className="flex min-h-40 w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-emerald-200/80 bg-emerald-50/30 px-4 py-6 text-center transition hover:border-emerald-400 hover:bg-emerald-50/60 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <span className="mb-3 grid h-12 w-12 place-items-center rounded-xl bg-white text-2xl text-emerald-600 shadow-sm">
            ↑
          </span>
          <span className="text-sm font-semibold text-slate-800">
            Choose an image
          </span>
          <span className="mt-1 text-xs text-slate-500">
            JPEG, PNG, or WebP · Maximum 10 MB
          </span>
        </button>
      ) : (
        <div className="rounded-xl border border-slate-200 p-3">
          <div className="flex items-start gap-3">
            <Image
              src={previewUrl}
              alt="Preview of the selected medicine label"
              width={96}
              height={112}
              unoptimized
              className="h-28 w-24 shrink-0 rounded-lg border border-slate-200 bg-slate-50 object-contain"
            />

            <div className="min-w-0 flex-1">
              <p className="break-words text-sm font-semibold text-slate-800">
                {fileName || "Selected medicine image"}
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                Check that the label text is clear and readable before
                extracting it.
              </p>
              <button
                type="button"
                onClick={removeFile}
                disabled={extracting}
                className="mt-3 text-xs font-semibold text-red-600 transition hover:text-red-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Remove image
              </button>
            </div>
          </div>
        </div>
      )}

      {(validationError || error) && (
        <p
          role="alert"
          className="mt-3 rounded-xl border border-red-200 bg-red-50 p-3 text-xs leading-5 text-red-800"
        >
          {validationError || error}
        </p>
      )}

      <button
        type="button"
        onClick={onExtract}
        disabled={!previewUrl || extracting || Boolean(validationError)}
        aria-busy={extracting}
        className="mt-4 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-700 px-4 py-3 text-sm font-bold text-white shadow-md shadow-emerald-600/15 transition-all hover:shadow-lg hover:shadow-emerald-600/20 disabled:cursor-not-allowed disabled:bg-none disabled:bg-slate-300 disabled:shadow-none"
      >
        {extracting && (
          <span
            aria-hidden="true"
            className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
          />
        )}
        {extracting ? "Extracting text…" : "Extract medicine text"}
      </button>

      <p className="mt-3 text-[11px] leading-5 text-slate-500" role="status">
        OCR results may be inaccurate. Always verify the extracted medicine
        name and ingredients before relying on a match.
      </p>
    </section>
  );
}
