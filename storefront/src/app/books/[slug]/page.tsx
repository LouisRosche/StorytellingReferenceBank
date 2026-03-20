import { notFound } from "next/navigation";
import { storybooks } from "@/lib/storybooks";
import BookDetailClient from "@/components/BookDetailClient";

export function generateStaticParams() {
  return storybooks.map((book) => ({ slug: book.slug }));
}

export default async function BookPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const book = storybooks.find((b) => b.slug === slug);

  if (!book) {
    notFound();
  }

  return <BookDetailClient book={book} />;
}
