"use client";

import { Suspense, type ReactNode } from "react";
import ClientStoreProvider from "@/components/providers/client-store-provider";

type StoreProviderProps = {
    children: ReactNode;
};

function StoreFallback() {
    return (
        <main className="min-h-screen bg-[#f8faf9] px-6 py-12">
            <div className="mx-auto max-w-6xl animate-pulse space-y-6">
                <div className="h-8 w-48 rounded-lg bg-emerald-100" />
                <div className="h-12 max-w-2xl rounded-lg bg-slate-200" />
                <div className="h-5 max-w-xl rounded-lg bg-slate-100" />
                <div className="h-64 rounded-2xl bg-white shadow-sm" />
            </div>
        </main>
    );
}

export default function StoreProvider({
    children,
}: StoreProviderProps) {
    return (
        <Suspense fallback={<StoreFallback />}>
            <ClientStoreProvider>{children}</ClientStoreProvider>
        </Suspense>
    );
}