import type { Metadata } from "next";
import { validateEnv } from "@/lib/env";
import "./globals.css";

validateEnv();

export const metadata: Metadata = {
  title: "Storybook Library — Narrated Children's Picture Books",
  description:
    "Beautiful children's storybooks with professional narration. Choose your narrator, preview audio, and buy digital editions instantly.",
  openGraph: {
    title: "Storybook Library",
    description: "Narrated children's picture books — read and listen",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
          <nav className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2">
              <span className="text-2xl">📚</span>
              <span className="font-display text-xl font-bold text-primary-800">
                Storybook Library
              </span>
            </a>
            <div className="flex items-center gap-6">
              <a
                href="/#catalog"
                className="text-sm text-gray-600 hover:text-primary-700 transition-colors"
              >
                Browse
              </a>
              <a
                href="/#narrators"
                className="text-sm text-gray-600 hover:text-primary-700 transition-colors"
              >
                Narrators
              </a>
              <a
                href="/#about"
                className="text-sm text-gray-600 hover:text-primary-700 transition-colors"
              >
                About
              </a>
            </div>
          </nav>
        </header>
        <main>{children}</main>
        <footer className="bg-gray-900 text-gray-400 mt-24">
          <div className="max-w-6xl mx-auto px-4 py-12">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div>
                <h3 className="font-display text-white text-lg mb-3">
                  Storybook Library
                </h3>
                <p className="text-sm">
                  Handcrafted children's picture books with professional
                  narration. Every story comes alive with a voice chosen just
                  for your child.
                </p>
              </div>
              <div>
                <h4 className="text-white text-sm font-medium mb-3">Shop</h4>
                <ul className="space-y-2 text-sm">
                  <li>
                    <a href="/#catalog" className="hover:text-white transition-colors">
                      All Books
                    </a>
                  </li>
                  <li>
                    <a href="/#narrators" className="hover:text-white transition-colors">
                      Meet Our Narrators
                    </a>
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="text-white text-sm font-medium mb-3">
                  Support
                </h4>
                <ul className="space-y-2 text-sm">
                  <li>
                    <a href="mailto:support@storybooklibrary.com" className="hover:text-white transition-colors">
                      Contact Us
                    </a>
                  </li>
                  <li>
                    <span>Payments secured by Stripe</span>
                  </li>
                </ul>
              </div>
            </div>
            <div className="border-t border-gray-800 mt-8 pt-8 text-center text-xs">
              &copy; {new Date().getFullYear()} Storybook Library. All rights
              reserved.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
