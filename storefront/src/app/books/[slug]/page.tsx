"use client";

import { useState } from "react";
import { storybooks } from "@/lib/storybooks";
import type { Narrator, Storybook } from "@/lib/storybooks";
import NarratorSelector from "@/components/NarratorSelector";
import PurchaseButton from "@/components/PurchaseButton";
import { useParams } from "next/navigation";

function BookDetail({ book }: { book: Storybook }) {
  const [selectedNarrator, setSelectedNarrator] = useState<Narrator | null>(
    book.narrators[0] || null
  );

  return (
    <div className="max-w-6xl mx-auto px-4 py-12">
      <a
        href="/"
        className="text-sm text-primary-600 hover:text-primary-800 mb-8 inline-block"
      >
        &larr; Back to Library
      </a>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mt-4">
        {/* Cover / Visual */}
        <div className="aspect-[3/4] bg-gradient-to-br from-primary-100 to-warm-100 rounded-2xl flex items-center justify-center">
          <div className="text-center p-12">
            <span className="text-8xl block mb-6">
              {book.slug.includes("luna")
                ? "☁️"
                : book.slug.includes("rain")
                ? "💧"
                : "🌙"}
            </span>
            <h1 className="font-display text-3xl font-bold text-gray-800">
              {book.title}
            </h1>
            {book.subtitle && (
              <p className="text-gray-600 mt-2 italic">{book.subtitle}</p>
            )}
          </div>
        </div>

        {/* Details */}
        <div className="space-y-8">
          <div>
            <h1 className="font-display text-3xl font-bold text-gray-900">
              {book.title}
            </h1>
            {book.subtitle && (
              <p className="text-lg text-gray-500 mt-1">{book.subtitle}</p>
            )}
            <p className="text-sm text-gray-400 mt-2">
              By {book.author} &middot; Ages {book.ageRange} &middot;{" "}
              {book.pageCount} pages &middot; {book.wordCount} words
            </p>
          </div>

          <div className="prose prose-gray max-w-none">
            {book.longDescription.split("\n\n").map((para, i) => (
              <p key={i} className="text-gray-700 leading-relaxed">
                {para}
              </p>
            ))}
          </div>

          {/* Themes */}
          <div className="flex flex-wrap gap-2">
            {book.themes.map((theme) => (
              <span
                key={theme}
                className="text-xs bg-warm-100 text-warm-500 px-3 py-1 rounded-full font-medium"
              >
                {theme}
              </span>
            ))}
          </div>

          {/* Narrator selection */}
          {book.narrators.length > 0 && (
            <NarratorSelector
              narrators={book.narrators}
              selected={selectedNarrator?.id}
              onSelect={setSelectedNarrator}
            />
          )}

          {/* Purchase options */}
          <div className="space-y-3">
            <h3 className="font-display text-lg font-semibold text-gray-900">
              Get This Book
            </h3>
            <div className="grid gap-3">
              <PurchaseButton
                slug={book.slug}
                format="ebook"
                label="Digital Storybook (PDF)"
                priceInCents={book.priceInCents}
              />
              <PurchaseButton
                slug={book.slug}
                format="audiobook"
                narratorId={selectedNarrator?.id}
                label={`Audiobook${
                  selectedNarrator ? ` — narrated by ${selectedNarrator.name}` : ""
                }`}
                priceInCents={book.audiobookPriceInCents}
                className="btn-secondary"
              />
              <PurchaseButton
                slug={book.slug}
                format="bundle"
                narratorId={selectedNarrator?.id}
                label={`Bundle (Book + Audio${
                  selectedNarrator ? ` by ${selectedNarrator.name}` : ""
                })`}
                priceInCents={book.bundlePriceInCents}
                className="btn-primary bg-gradient-to-r from-primary-600 to-primary-500"
              />
            </div>
            <p className="text-xs text-gray-400 text-center mt-2">
              Secure checkout powered by Stripe. Instant digital delivery.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function BookPage() {
  const params = useParams();
  const slug = params.slug as string;
  const book = storybooks.find((b) => b.slug === slug);

  if (!book) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-20 text-center">
        <h1 className="font-display text-2xl font-bold text-gray-900">
          Book not found
        </h1>
        <a href="/" className="text-primary-600 mt-4 inline-block">
          &larr; Back to Library
        </a>
      </div>
    );
  }

  return <BookDetail book={book} />;
}
