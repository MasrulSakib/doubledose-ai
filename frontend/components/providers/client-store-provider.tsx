
"use client";

import { useState, type ReactNode } from "react";
import { Provider } from "react-redux";

import { makeStore } from "@/lib/store";
import type { AppStore } from "@/lib/store";

type ClientStoreProviderProps = {
    children: ReactNode;
};

export default function ClientStoreProvider({
    children,
}: ClientStoreProviderProps) {
    const [store] = useState<AppStore>(() => makeStore());

    return <Provider store={store}>{children}</Provider>;
}
