export default function Loading() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-20 text-center">
      <div
        className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600"
        role="status"
        aria-label="Loading"
      />
      <p className="text-gray-500 mt-4 text-sm">Loading...</p>
    </div>
  );
}
