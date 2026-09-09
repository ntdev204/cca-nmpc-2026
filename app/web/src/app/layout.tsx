import type { Metadata } from "next";
import "./globals.css";
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";
import { KeyboardControl } from "@/components/keyboard-control";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

export const metadata: Metadata = {
  title: "Mecanum Robot Console",
  description: "HTTP operator dashboard for the Mecanum robot",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={cn("font-sans", geist.variable)}>
      <body><KeyboardControl />{children}</body>
    </html>
  );
}
