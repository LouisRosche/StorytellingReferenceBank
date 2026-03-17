"use client";

import type { Storybook } from "@/lib/storybooks";

export default function BookCard({ book }: { book: Storybook }) {
  return (
    <a href={`/books/${book.slug}`} className="card group block overflow-hidden">
      <div className="aspect-[3/4] relative overflow-hidden bg-gray-50">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={book.coverImage}
          alt={`Cover of ${book.title}`}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
        />
        {book.narrators.length > 0 && (
          <div className="absolute top-3 right-3 bg-primary-600 text-white text-xs px-2 py-1 rounded-full">
            🎧 Audio
          </div>
        )}
      </div>
      <div className="p-4">
        <h3 className="font-display text-lg font-bold text-gray-800 group-hover:text-primary-700 transition-colors">
          {book.title}
        </h3>
        <p className="text-sm text-gray-500 mb-1 mt-1">
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
