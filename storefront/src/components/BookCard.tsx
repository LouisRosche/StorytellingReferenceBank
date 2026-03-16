"use client";

import type { Storybook } from "@/lib/storybooks";

export default function BookCard({ book }: { book: Storybook }) {
  return (
    <a href={`/books/${book.slug}`} className="card group block overflow-hidden">
      <div className="aspect-[3/4] bg-gradient-to-br from-primary-100 to-warm-100 relative overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center p-8">
          <div className="text-center">
            <span className="text-6xl block mb-4">
              {book.slug.includes("luna")
                ? "☁️"
                : book.slug.includes("rain")
                ? "💧"
                : "🌙"}
            </span>
            <h3 className="font-display text-lg font-bold text-gray-800 group-hover:text-primary-700 transition-colors">
              {book.title}
            </h3>
          </div>
        </div>
        {book.narrators.length > 0 && (
          <div className="absolute top-3 right-3 bg-primary-600 text-white text-xs px-2 py-1 rounded-full">
            🎧 Audio
          </div>
        )}
      </div>
      <div className="p-4">
        <p className="text-sm text-gray-500 mb-1">
          Ages {book.ageRange} &middot; {book.pageCount} pages
        </p>
        <p className="text-sm text-gray-600 line-clamp-2">{book.description}</p>
        <div className="mt-3 flex items-center justify-between">
          <span className="font-bold text-primary-700">
            ${(book.priceInCents / 100).toFixed(2)}
          </span>
          <span className="text-xs text-gray-400">
            Bundle ${(book.bundlePriceInCents / 100).toFixed(2)}
          </span>
        </div>
      </div>
    </a>
  );
}
