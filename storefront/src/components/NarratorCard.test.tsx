import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import NarratorCard from "./NarratorCard";
import type { Narrator } from "@/lib/storybooks";

const mockNarrator: Narrator = {
  id: "narrator-test",
  name: "Sunny",
  description: "Warm and soothing voice",
  personaFile: "test.json",
  tags: ["warm", "soothing", "bedtime"],
};

describe("NarratorCard", () => {
  it("renders narrator name and description", () => {
    render(<NarratorCard narrator={mockNarrator} />);
    expect(screen.getByText("Sunny")).toBeInTheDocument();
    expect(screen.getByText("Warm and soothing voice")).toBeInTheDocument();
  });

  it("renders all tags", () => {
    render(<NarratorCard narrator={mockNarrator} />);
    expect(screen.getByText("warm")).toBeInTheDocument();
    expect(screen.getByText("soothing")).toBeInTheDocument();
    expect(screen.getByText("bedtime")).toBeInTheDocument();
  });

  it("shows child emoji for child narrator", () => {
    const childNarrator: Narrator = {
      ...mockNarrator,
      id: "character-child-voice",
    };
    render(<NarratorCard narrator={childNarrator} />);
    // Emoji should be aria-hidden
    const emoji = screen.getByText("🧒");
    expect(emoji).toHaveAttribute("aria-hidden", "true");
  });

  it("shows microphone emoji for non-child narrator", () => {
    render(<NarratorCard narrator={mockNarrator} />);
    const emoji = screen.getByText("🎙️");
    expect(emoji).toHaveAttribute("aria-hidden", "true");
  });

  it("has accessible card structure", () => {
    render(<NarratorCard narrator={mockNarrator} />);
    // Card should have an article role for semantic grouping
    expect(screen.getByRole("article")).toBeInTheDocument();
  });
});
