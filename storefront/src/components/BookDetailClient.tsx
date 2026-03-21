"use client";

import { useState } from "react";
import type { Narrator, Storybook } from "@/lib/storybooks";
import NarratorSelector from "@/components/NarratorSelector";
import AudioPreview from "@/components/AudioPreview";
import PurchaseButton from "@/components/PurchaseButton";

export default function BookDetailClient({ book }: { book: Storybook }) {
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
        {/* Cover */}
        <div className="aspect-[3/4] rounded-2xl overflow-hidden shadow-lg">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={book.coverImage}
            alt={`Cover of ${book.title}`}
            className="w-full h-full object-cover"
          />
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

          {/* Narrator selection + audio preview */}
          {book.narrators.length > 0 && (
            <div className="space-y-4">
              <NarratorSelector
                narrators={book.narrators}
                selected={selectedNarrator?.id}
                onSelect={setSelectedNarrator}
              />
              {selectedNarrator && (
                <AudioPreview narrator={selectedNarrator} />
              )}
            </div>
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
