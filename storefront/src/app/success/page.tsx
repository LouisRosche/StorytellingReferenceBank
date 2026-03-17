"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function SuccessContent() {
  const params = useSearchParams();
  const sessionId = params.get("session_id");

  return (
    <div className="max-w-2xl mx-auto px-4 py-20 text-center">
      <span className="text-6xl block mb-6">🎉</span>
      <h1 className="font-display text-3xl font-bold text-gray-900">
        Thank you for your purchase!
      </h1>
      <p className="text-gray-600 mt-4 leading-relaxed">
        Your storybook is ready. Check your email for download links — they're
        valid for 14 days. You can re-download anytime by contacting support
        with your order ID.
      </p>
      {sessionId && (
        <p className="text-xs text-gray-400 mt-6">Order ref: {sessionId}</p>
      )}
      <div className="mt-8 flex justify-center gap-4">
        <a href="/" className="btn-primary">
          Browse More Stories
        </a>
      </div>
    </div>
  );
}

export default function SuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-2xl mx-auto px-4 py-20 text-center">
          <p>Loading...</p>
        </div>
      }
    >
      <SuccessContent />
    </Suspense>
  );
}
