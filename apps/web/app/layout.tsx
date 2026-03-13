import type { Metadata } from "next";
import { Nav } from "../components/nav";
import { auth } from "../lib/auth";
import "./globals.css";

export const metadata: Metadata = {
  title: "arXiv Daily Digest",
  description: "Daily ML paper discovery with personalized ranking and feedback.",
  icons: {
    icon: "/favicon.svg",
    apple: "/apple-touch-icon.svg"
  },
  openGraph: {
    title: "arXiv Daily Digest",
    description: "Ranked daily arXiv for ML researchers. Personalized paper discovery with feedback-driven ranking.",
    type: "website",
    images: [{ url: "/og-image.svg", width: 1200, height: 630, alt: "arXiv Daily Digest" }]
  },
  twitter: {
    card: "summary_large_image",
    title: "arXiv Daily Digest",
    description: "Ranked daily arXiv for ML researchers. Personalized paper discovery with feedback-driven ranking.",
    images: ["/og-image.svg"]
  }
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
