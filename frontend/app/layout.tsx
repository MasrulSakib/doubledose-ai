
import type { Metadata } from "next";
import { Suspense } from "react";

import StoreProvider from "@/app/StoreProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "DoubleDose AI | Medicine Ingredient Checker",
  description:
    "Compare active ingredients across medicines and identify potential ingredient overlap using available medicine records.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <StoreProvider>{children}</StoreProvider>
      </body>
    </html>
  );
}
