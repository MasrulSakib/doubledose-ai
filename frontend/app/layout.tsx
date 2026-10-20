import type { Metadata } from "next";
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
      <body>{children}</body>
    </html>
  );
}