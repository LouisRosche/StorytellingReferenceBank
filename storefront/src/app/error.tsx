"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="max-w-2xl mx-auto px-4 py-20 text-center">
      <span className="text-5xl block mb-6" aria-hidden="true">⚠️</span>
      <h1 className="font-display text-2xl font-bold text-gray-900">
        Something went wrong
      </h1>
      <p className="text-gray-600 mt-4">
        We hit an unexpected error. Please try again, or contact support if the
        problem persists.
      </p>
      {error.digest && (
        <p className="text-xs text-gray-400 mt-2">
          Error ref: {error.digest}
        </p>
      )}
      <div className="mt-8 flex justify-center gap-4">
        <button onClick={reset} className="btn-primary">
          Try Again
        </button>
        <a href="/" className="btn-secondary">
          Back to Library
        </a>
      </div>
    </div>
  );
}
