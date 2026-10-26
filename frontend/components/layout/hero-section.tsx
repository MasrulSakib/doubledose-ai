import Link from "next/link";

export default function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-b from-emerald-50/60 via-transparent to-transparent" />

      <div className="mx-auto grid min-h-[340px] w-[calc(100%-2rem)] max-w-[1160px] grid-cols-1 items-center gap-8 py-12 sm:w-[calc(100%-3rem)] md:grid-cols-[1.25fr_0.75fr] md:gap-10 md:py-16">
        <div className="animate-fade-in">
          <div className="mb-5 flex items-center gap-2.5 text-[10px] font-extrabold tracking-[.16em] text-emerald-700 uppercase">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            Smarter medicine safety
          </div>

          <h1 className="text-4xl font-extrabold leading-[1.08] tracking-tight text-slate-900 sm:text-5xl lg:text-[3.4rem]">
            Know what&apos;s
            <br />
            <span className="bg-gradient-to-r from-emerald-600 to-emerald-800 bg-clip-text text-transparent">
              inside your medicines.
            </span>
          </h1>

          <p className="mt-5 max-w-[480px] text-[15px] leading-7 text-slate-500">
            Compare medicine ingredients, identify potential overlaps, and
            understand the results with AI-assisted explanations.
          </p>

          <div className="mt-7 flex flex-wrap gap-x-6 gap-y-3 text-xs font-semibold text-slate-800">
            <span className="flex items-center gap-2">
              <span className="grid h-5 w-5 place-items-center rounded-full bg-emerald-100 text-emerald-700 text-[11px]">
                ✓
              </span>
              Ingredient awareness
            </span>
            <span className="flex items-center gap-2">
              <span className="grid h-5 w-5 place-items-center rounded-full bg-emerald-100 text-emerald-700 text-[11px]">
                ✓
              </span>
              AI-assisted explanations
            </span>
          </div>

          <div className="mt-8">
            <Link
              href="#medicine-checker"
              className="group inline-flex min-h-12 items-center justify-center gap-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-700 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-emerald-600/25 transition-all hover:-translate-y-0.5 hover:shadow-xl hover:shadow-emerald-600/30"
            >
              Check medicines
              <span aria-hidden="true" className="transition-transform group-hover:translate-x-0.5">→</span>
            </Link>
          </div>
        </div>

        <div
          className="relative hidden min-h-[260px] items-center justify-center isolate md:flex"
          aria-hidden="true"
        >
          <div className="absolute -z-10 h-60 w-60 rounded-full bg-gradient-to-br from-emerald-100/80 to-emerald-50/40 blur-sm" />

          <div className="absolute h-44 w-72 rotate-[-32deg] rounded-[50%] border border-emerald-200/60" />
          <div className="absolute h-44 w-72 rotate-[32deg] rounded-[50%] border border-emerald-200/60" />

          <span className="absolute right-12 top-5 text-3xl font-medium text-emerald-400 animate-pulse-dot">+</span>
          <span className="absolute bottom-6 left-6 text-2xl font-medium text-emerald-400 animate-pulse-dot" style={{ animationDelay: "1s" }}>+</span>
          <span className="absolute left-12 top-9 h-3 w-3 rounded-full bg-emerald-300/60" />
          <span className="absolute bottom-12 right-6 h-2 w-2 rounded-full bg-emerald-300/60" />

          <div className="animate-float w-52 min-h-[185px] rounded-2xl border border-white/60 bg-white/90 p-7 shadow-2xl shadow-emerald-900/10 backdrop-blur-sm">
            <div className="mb-6 flex h-8 w-20 -rotate-[35deg] overflow-hidden rounded-full border-2 border-emerald-600">
              <span className="w-1/2 bg-emerald-200" />
              <span className="w-1/2 border-l-2 border-emerald-600 bg-white" />
            </div>

            <div className="mb-2 h-1.5 w-full rounded-full bg-emerald-100" />
            <div className="h-1.5 w-[62%] rounded-full bg-emerald-100" />

            <div className="mt-5 flex items-center gap-2 rounded-lg bg-emerald-50 p-2 text-[10px] font-bold text-emerald-800">
              <span className="grid h-4 w-4 place-items-center rounded-full bg-emerald-600 text-white text-[8px]">
                ✓
              </span>
              Ingredient review
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}