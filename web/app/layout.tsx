import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SaveUp",
  description: "Goal based savings platform"
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}