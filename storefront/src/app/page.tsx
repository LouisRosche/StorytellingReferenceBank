import BookCard from "@/components/BookCard";
import NarratorCard from "@/components/NarratorCard";
import { storybooks, narrators } from "@/lib/storybooks";

export default function HomePage() {
  const featured = storybooks.filter((b) => b.featured);
  const allBooks = storybooks;

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-warm-50" />
        <div className="relative max-w-6xl mx-auto px-4 py-20 md:py-32">
          <div className="max-w-2xl">
            <h1 className="font-display text-4xl md:text-6xl font-bold text-gray-900 leading-tight">
              Stories that read
              <span className="text-primary-600"> themselves</span>
            </h1>
            <p className="mt-6 text-lg text-gray-600 leading-relaxed">
              Beautiful children's picture books with professional narration.
              Choose a narrator your child loves, preview the audio, and get
              instant digital delivery.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <a href="#catalog" className="btn-primary">
                Browse Books
              </a>
              <a href="#narrators" className="btn-secondary">
                Meet Our Narrators
              </a>
            </div>
          </div>
          <div className="absolute right-0 top-1/2 -translate-y-1/2 opacity-10 text-[20rem] pointer-events-none select-none" aria-hidden="true">
            📖
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="font-display text-2xl font-bold text-center text-gray-900 mb-12">
          How It Works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            {
              icon: "📚",
              title: "Pick a Story",
              desc: "Browse our curated library of children's picture books, crafted for ages 3–8.",
            },
            {
              icon: "🎙️",
              title: "Choose a Narrator",
              desc: "Select from professional voices — warm, playful, or gentle — matched to each story.",
            },
            {
              icon: "🎧",
              title: "Read & Listen",
              desc: "Get instant access to the ebook, audiobook, or both. Download and enjoy anywhere.",
            },
          ].map((step, i) => (
            <div key={i} className="text-center">
              <span className="text-4xl block mb-4" aria-hidden="true">{step.icon}</span>
              <h3 className="font-display text-lg font-bold text-gray-900">
                {step.title}
              </h3>
              <p className="text-sm text-gray-600 mt-2">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Featured */}
      {featured.length > 0 && (
        <section className="max-w-6xl mx-auto px-4 py-16">
          <h2 className="font-display text-2xl font-bold text-gray-900 mb-8">
            Featured Stories
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {featured.map((book) => (
              <BookCard key={book.slug} book={book} />
            ))}
          </div>
        </section>
      )}

      {/* Full catalog */}
      <section id="catalog" className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="font-display text-2xl font-bold text-gray-900 mb-8">
          All Books
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {allBooks.map((book) => (
            <BookCard key={book.slug} book={book} />
          ))}
        </div>
      </section>

      {/* Narrators */}
      <section
        id="narrators"
        className="bg-gradient-to-b from-white to-primary-50 py-16"
      >
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="font-display text-2xl font-bold text-gray-900 mb-3">
            Meet Our Narrators
          </h2>
          <p className="text-gray-600 mb-8 max-w-xl">
            Every voice in our library is crafted with care — designed for
            warmth, clarity, and the kind of expression that makes bedtime
            stories magical.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {narrators.map((n) => (
              <NarratorCard key={n.id} narrator={n} />
            ))}
          </div>
        </div>
      </section>

      {/* About */}
      <section id="about" className="max-w-6xl mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="font-display text-2xl font-bold text-gray-900 mb-4">
            Why Storybook Library?
          </h2>
          <p className="text-gray-600 leading-relaxed">
            We believe every child deserves stories that spark wonder. Our books
            are written with care, illustrated with love, and narrated by voices
            that bring characters to life. Each audiobook is produced using our
            professional narration pipeline — the same technology used to create
            ACX-compliant audiobooks for major platforms.
          </p>
          <div className="mt-8 grid grid-cols-3 gap-4 text-center">
            <div>
              <span className="font-display text-3xl font-bold text-primary-600">
                {storybooks.length}
              </span>
              <p className="text-xs text-gray-500 mt-1">Stories</p>
            </div>
            <div>
              <span className="font-display text-3xl font-bold text-primary-600">
                {narrators.length}
              </span>
              <p className="text-xs text-gray-500 mt-1">Narrators</p>
            </div>
            <div>
              <span className="font-display text-3xl font-bold text-primary-600">
                3–8
              </span>
              <p className="text-xs text-gray-500 mt-1">Ages</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
