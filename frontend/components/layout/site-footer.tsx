import Link from "next/link";

export default function SiteFooter() {
    return (
        <footer className="mt-16 border-t border-emerald-100 bg-white">
            <div className="mx-auto flex w-[calc(100%-2rem)] max-w-[1160px] flex-col gap-5 py-8 sm:w-[calc(100%-3rem)] sm:flex-row sm:items-center sm:justify-between">
                <Link
                    href="/"
                    className="flex w-fit items-center gap-3 rounded-lg focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-emerald-600"
                    aria-label="DoubleDose AI home"
                >
                    <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-700 text-sm font-extrabold text-white">
                        D+
                    </span>

                    <span className="text-sm font-extrabold text-emerald-950">
                        DoubleDose <span className="text-emerald-700">AI</span>
                    </span>
                </Link>

                <p className="max-w-xl text-sm leading-6 text-slate-500 sm:text-right">
                    Built to support medicine ingredient awareness. Always verify
                    medicine information with a qualified healthcare professional.
                </p>
            </div>

            <div className="border-t border-slate-100 px-4 py-3 text-center text-xs leading-5 text-slate-400">
                © {new Date().getFullYear()} DoubleDose AI. For informational purposes
                only.
            </div>
        </footer>
    );
}