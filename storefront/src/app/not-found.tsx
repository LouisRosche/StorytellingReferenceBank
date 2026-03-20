export default function NotFound() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-20 text-center">
      <span className="text-6xl block mb-6" aria-hidden="true">📖</span>
      <h1 className="font-display text-2xl font-bold text-gray-900">
        Page not found
      </h1>
      <p className="text-gray-600 mt-4">
        The page you're looking for doesn't exist or may have moved.
      </p>
      <div className="mt-8">
        <a href="/" className="btn-primary">
          Browse Our Stories
        </a>
      </div>
    </div>
  );
}
