import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mecanum Robot Console",
  description: "No-ROS operator dashboard for the Mecanum robot",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
