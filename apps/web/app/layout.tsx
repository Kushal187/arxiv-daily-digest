import type { Metadata } from "next";
import { Nav } from "../components/nav";
import { auth } from "../lib/auth";
import "./globals.css";

export const metadata: Metadata = {
  title: "arXiv Daily Digest",
  description: "Daily ML paper discovery with personalized ranking and feedback."
};

export default async function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await auth();

  return (
    <html lang="en">
      <body>
        <div className="shell">
          <Nav session={session} />
          {children}
        </div>
      </body>
    </html>
  );
}
