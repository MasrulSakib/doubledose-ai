import type { Metadata } from "next";
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
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        <StoreProvider>{children}</StoreProvider>
      </body>
    </html>
  );
}
