import Link from "next/link";

export default function HeroSection() {
    return (
        <section className="mx-auto grid min-h-[350px] w-[calc(100%-2rem)] max-w-[1160px] grid-cols-1 items-center gap-8 py-10 sm:w-[calc(100%-3rem)] md:grid-cols-[1.25fr_0.75fr] md:gap-9 md:py-14">
            <div>
                <div className="mb-5 flex items-center gap-2 text-[10px] font-extrabold tracking-[1.6px] text-emerald-700">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    SMARTER MEDICINE SAFETY
                </div>

                <h1 className="text-4xl font-extrabold leading-[1.1] tracking-tight text-emerald-950 sm:text-5xl lg:text-[55px]">
                    Know what&apos;s
                    <br />
                    <span className="text-emerald-700">
                        inside your medicines.
                    </span>
                </h1>

                <p className="mt-5 max-w-[485px] text-sm leading-7 text-slate-500 sm:text-[15px]">
                    Compare medicine ingredients, identify potential overlaps, and
                    understand the results with AI-assisted explanations.
                </p>

                <div className="mt-6 flex flex-wrap gap-x-5 gap-y-3 text-xs font-semibold text-emerald-950">
                    <span className="flex items-center gap-2">
                        <span className="grid h-[18px] w-[18px] place-items-center rounded-full bg-emerald-100 text-emerald-700">
                            ✓
                        </span>
                        Ingredient awareness
                    </span>

                    <span className="flex items-center gap-2">
                        <span className="grid h-[18px] w-[18px] place-items-center rounded-full bg-emerald-100 text-emerald-700">
                            ✓
                        </span>
                        AI-assisted explanations
                    </span>
                </div>

                <div className="mt-6">
                    <Link
                        href="#medicine-checker"
                        className="inline-flex min-h-12 items-center justify-center gap-3 rounded-lg bg-emerald-700 px-5 py-3 text-sm font-bold text-white transition hover:-translate-y-0.5 hover:bg-emerald-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600"
                    >
                        Check medicines
                        <span aria-hidden="true">→</span>
                    </Link>
                </div>
            </div>

            <div
                className="relative hidden min-h-[260px] items-center justify-center isolate md:flex"
                aria-hidden="true"
            >
                <div className="absolute -z-10 h-[245px] w-[245px] rounded-full bg-emerald-100/70" />

                <div className="absolute h-[180px] w-[300px] rotate-[-32deg] rounded-[50%] border border-emerald-200" />
                <div className="absolute h-[180px] w-[300px] rotate-[32deg] rounded-[50%] border border-emerald-200" />

                <span className="absolute right-12 top-5 text-3xl font-medium text-emerald-500">
                    +
                </span>
                <span className="absolute bottom-6 left-6 text-2xl font-medium text-emerald-500">
                    +
                </span>
                <span className="absolute left-12 top-9 h-3 w-3 rounded-full bg-emerald-300" />
                <span className="absolute bottom-12 right-6 h-2 w-2 rounded-full bg-emerald-300" />

                <div className="w-[205px] min-h-[185px] rotate-[-5deg] rounded-[19px] border border-slate-100 bg-white/95 p-7 shadow-[0_18px_55px_rgba(34,92,60,0.12)]">
                    <div className="mb-6 flex h-[33px] w-20 -rotate-[35deg] overflow-hidden rounded-full border-2 border-emerald-600">
                        <span className="w-1/2 bg-emerald-200" />
                        <span className="w-1/2 border-l-2 border-emerald-600 bg-white" />
                    </div>

                    <div className="mb-2 h-1.5 w-full rounded-full bg-emerald-100" />
                    <div className="h-1.5 w-[62%] rounded-full bg-emerald-100" />

                    <div className="mt-5 flex items-center gap-2 rounded-lg bg-emerald-50 p-2 text-[10px] font-bold text-emerald-800">
                        <span className="grid h-4 w-4 place-items-center rounded-full bg-emerald-600 text-white">
                            ✓
                        </span>
                        Ingredient review
                    </div>
                </div>
            </div>
        </section>
    );
}