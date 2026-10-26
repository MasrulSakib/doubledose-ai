import Link from "next/link";

export default function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-emerald-100/60 bg-white/80 backdrop-blur-xl backdrop-saturate-150">
      <div className="mx-auto flex min-h-16 w-[calc(100%-2rem)] max-w-[1160px] items-center justify-between gap-4 sm:w-[calc(100%-3rem)]">
        <Link
          href="/"
          aria-label="DoubleDose AI home"
          className="inline-flex min-w-0 items-center gap-3 rounded-lg transition-opacity hover:opacity-80"
        >
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-emerald-600 to-emerald-800 text-base font-extrabold tracking-tight text-white shadow-md shadow-emerald-600/20">
            D<span className="text-emerald-200">+</span>
          </span>

          <span className="whitespace-nowrap text-lg font-extrabold tracking-tight text-slate-900 sm:text-xl">
            DoubleDose<span className="text-emerald-600"> AI</span>
          </span>
        </Link>

        <div className="flex shrink-0 items-center gap-2 rounded-full border border-emerald-200/60 bg-emerald-50/70 px-3 py-1.5 text-xs font-semibold text-emerald-800">
          <span
            aria-hidden="true"
            className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse-dot"
          />
          <span>Ingredient checker</span>
        </div>
      </div>
    </header>
  );
}