"use client";

import { useState } from "react";

interface PurchaseButtonProps {
  slug: string;
  format: "ebook" | "audiobook" | "bundle";
  narratorId?: string;
  label: string;
  priceInCents: number;
  className?: string;
}

export default function PurchaseButton({
  slug,
  format,
  narratorId,
  label,
  priceInCents,
  className = "btn-primary",
}: PurchaseButtonProps) {
  const [loading, setLoading] = useState(false);

  async function handlePurchase() {
    setLoading(true);
    try {
      const response = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug, format, narratorId }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        alert(data?.error || `Checkout failed (${response.status}). Please try again.`);
        return;
      }

      const data = await response.json();

      if (data.url) {
        window.location.href = data.url;
      } else {
        alert("Something went wrong. Please try again.");
      }
    } catch {
      alert("Network error. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handlePurchase}
      disabled={loading}
      aria-label={`Purchase ${label} for $${(priceInCents / 100).toFixed(2)}`}
      className={className}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg
            className="animate-spin h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          Processing...
        </span>
      ) : (
        <span>
          {label} — ${(priceInCents / 100).toFixed(2)}
        </span>
      )}
    </button>
  );
}
