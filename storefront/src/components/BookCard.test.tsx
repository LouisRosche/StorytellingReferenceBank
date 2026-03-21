import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import BookCard from "./BookCard";
import type { Storybook } from "@/lib/storybooks";

const mockBook: Storybook = {
  slug: "test-book",
  title: "Test Book",
  subtitle: "A test subtitle",
  author: "Test Author",
  ageRange: "3-6",
  pageCount: 32,
  wordCount: 400,
  description: "A test description",
  longDescription: "A longer test description",
  coverImage: "/covers/test.svg",
  priceInCents: 499,
  audiobookPriceInCents: 699,
  bundlePriceInCents: 899,
  narrators: [],
  themes: ["test"],
  featured: true,
  previewPages: 4,
};

describe("BookCard", () => {
  it("renders book title and price", () => {
    render(<BookCard book={mockBook} />);
    expect(screen.getByText("Test Book")).toBeInTheDocument();
    expect(screen.getByText("$4.99")).toBeInTheDocument();
  });

  it("renders cover image with alt text", () => {
    render(<BookCard book={mockBook} />);
    const img = screen.getByAltText("Cover of Test Book");
    expect(img).toBeInTheDocument();
  });

  it("links to book detail page", () => {
    render(<BookCard book={mockBook} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/books/test-book");
  });

  it("shows audio badge when narrators exist", () => {
    const bookWithNarrators = {
      ...mockBook,
      narrators: [{ id: "n1", name: "Test", description: "Test narrator", personaFile: "test.json", tags: ["warm"] }],
    };
    render(<BookCard book={bookWithNarrators} />);
    expect(screen.getByText(/Audio/)).toBeInTheDocument();
  });

  it("hides audio badge when no narrators", () => {
    render(<BookCard book={mockBook} />);
    expect(screen.queryByText(/Audio/)).not.toBeInTheDocument();
  });
});
