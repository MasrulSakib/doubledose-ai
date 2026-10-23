import Link from "next/link";

export default function SiteHeader() {
    return (
        <header className="sticky top-0 z-50 border-b border-emerald-100/80 bg-white/95 backdrop-blur">
            <div className="mx-auto flex min-h-[68px] w-[calc(100%-2rem)] max-w-[1160px] items-center justify-between gap-4 sm:w-[calc(100%-3rem)]">
                <Link
                    href="/"
                    aria-label="DoubleDose AI home"
                    className="inline-flex min-w-0 items-center gap-3 rounded-lg focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-emerald-600"
                >
                    <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-emerald-700 text-lg font-extrabold tracking-tight text-white shadow-sm">
                        D<span className="text-emerald-200">+</span>
                    </span>

                    <span className="whitespace-nowrap text-lg font-extrabold tracking-tight text-emerald-950 sm:text-xl">
                        DoubleDose<span className="text-emerald-700"> AI</span>
                    </span>
                </Link>

                <div className="flex shrink-0 items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800 sm:text-sm">
                    <span
                        aria-hidden="true"
                        className="h-2 w-2 rounded-full bg-emerald-500"
                    />
                    <span>Ingredient checker</span>
                </div>
            </div>
        </header>
    );
}