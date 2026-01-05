import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Universal Agent SDK",
  description: "AI-powered agent platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen">{children}</body>
    </html>
  );
}
