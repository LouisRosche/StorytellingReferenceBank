import { describe, it, expect } from "vitest";
import { storybooks, narrators, getStorybook, getFeaturedStorybooks, getStorybooksByTheme } from "./storybooks";

describe("storybooks catalog", () => {
  it("has at least one storybook", () => {
    expect(storybooks.length).toBeGreaterThan(0);
  });

  it("all books have required fields", () => {
    for (const book of storybooks) {
      expect(book.slug).toBeTruthy();
      expect(book.title).toBeTruthy();
      expect(book.priceInCents).toBeGreaterThan(0);
      expect(book.audiobookPriceInCents).toBeGreaterThan(0);
      expect(book.bundlePriceInCents).toBeGreaterThan(0);
      expect(book.bundlePriceInCents).toBeLessThan(book.priceInCents + book.audiobookPriceInCents);
    }
  });

  it("all narrators have required fields", () => {
    for (const n of narrators) {
      expect(n.id).toBeTruthy();
      expect(n.name).toBeTruthy();
      expect(n.tags.length).toBeGreaterThan(0);
    }
  });

  it("getStorybook returns correct book", () => {
    const book = getStorybook("luna-the-little-cloud");
    expect(book).toBeDefined();
    expect(book!.title).toBe("Luna the Little Cloud");
  });

  it("getStorybook returns undefined for invalid slug", () => {
    expect(getStorybook("nonexistent")).toBeUndefined();
  });

  it("getFeaturedStorybooks returns only featured", () => {
    const featured = getFeaturedStorybooks();
    expect(featured.length).toBeGreaterThan(0);
    expect(featured.every((b) => b.featured)).toBe(true);
  });

  it("getStorybooksByTheme filters correctly", () => {
    const courage = getStorybooksByTheme("courage");
    expect(courage.length).toBeGreaterThan(0);
    expect(courage.every((b) => b.themes.some((t) => t.includes("courage")))).toBe(true);
  });
});
