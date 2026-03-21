import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Deckbuilder Roguelite",
  description: "A WebGL roguelite deckbuilder",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
