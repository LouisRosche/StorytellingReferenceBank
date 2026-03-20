import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import BookDetailClient from "./BookDetailClient";
import type { Storybook } from "@/lib/storybooks";

const mockNarrator = {
  id: "narrator-test",
  name: "Sunny",
  description: "Warm voice",
  personaFile: "test.json",
  sampleUrl: "/samples/test.mp3",
  tags: ["warm", "soothing"],
};

const mockBook: Storybook = {
  slug: "test-book",
  title: "Test Book",
  subtitle: "A test subtitle",
  author: "Test Author",
  ageRange: "3-6",
  pageCount: 32,
  wordCount: 400,
  description: "A test description",
  longDescription: "First paragraph.\n\nSecond paragraph.",
  coverImage: "/covers/test.svg",
  priceInCents: 499,
  audiobookPriceInCents: 699,
  bundlePriceInCents: 899,
  narrators: [mockNarrator],
  themes: ["courage", "friendship"],
  featured: true,
  previewPages: 4,
  stripePriceIds: { ebook: "p1", audiobook: "p2", bundle: "p3" },
};

describe("BookDetailClient", () => {
  it("renders book title and subtitle", () => {
    render(<BookDetailClient book={mockBook} />);
    expect(screen.getByText("Test Book")).toBeInTheDocument();
    expect(screen.getByText("A test subtitle")).toBeInTheDocument();
  });

  it("renders author and metadata", () => {
    render(<BookDetailClient book={mockBook} />);
    expect(screen.getByText(/By Test Author/)).toBeInTheDocument();
    expect(screen.getByText(/32 pages/)).toBeInTheDocument();
    expect(screen.getByText(/400 words/)).toBeInTheDocument();
  });

  it("renders cover image with alt text", () => {
    render(<BookDetailClient book={mockBook} />);
    const img = screen.getByAltText("Cover of Test Book");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "/covers/test.svg");
  });

  it("renders long description as separate paragraphs", () => {
    render(<BookDetailClient book={mockBook} />);
    expect(screen.getByText("First paragraph.")).toBeInTheDocument();
    expect(screen.getByText("Second paragraph.")).toBeInTheDocument();
  });

  it("renders theme badges", () => {
    render(<BookDetailClient book={mockBook} />);
    expect(screen.getByText("courage")).toBeInTheDocument();
    expect(screen.getByText("friendship")).toBeInTheDocument();
  });

  it("renders purchase buttons for all formats", () => {
    render(<BookDetailClient book={mockBook} />);
    expect(screen.getByText(/Digital Storybook/)).toBeInTheDocument();
    expect(screen.getByText(/Audiobook/)).toBeInTheDocument();
    expect(screen.getByText(/Bundle/)).toBeInTheDocument();
  });

  it("renders back to library link", () => {
    render(<BookDetailClient book={mockBook} />);
    const link = screen.getByText(/Back to Library/);
    expect(link).toHaveAttribute("href", "/");
  });

  it("hides narrator section when no narrators", () => {
    const bookNoNarrators = { ...mockBook, narrators: [] };
    render(<BookDetailClient book={bookNoNarrators} />);
    expect(screen.queryByText("Sunny")).not.toBeInTheDocument();
  });

  it("hides subtitle when not provided", () => {
    const bookNoSubtitle = { ...mockBook, subtitle: undefined };
    render(<BookDetailClient book={bookNoSubtitle} />);
    expect(screen.queryByText("A test subtitle")).not.toBeInTheDocument();
  });
});
