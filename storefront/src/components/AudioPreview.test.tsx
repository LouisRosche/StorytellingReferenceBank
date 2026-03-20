import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import AudioPreview from "./AudioPreview";
import type { Narrator } from "@/lib/storybooks";

const mockNarrator: Narrator = {
  id: "narrator-luna-warm",
  name: "Sunny",
  description: "Warm and soothing narrator",
  personaFile: "personas/narrator-luna-warm.json",
  sampleUrl: "/samples/narrator-luna-warm.mp3",
  tags: ["warm", "soothing"],
};

const narratorNoSample: Narrator = {
  ...mockNarrator,
  sampleUrl: undefined,
};

describe("AudioPreview", () => {
  it("renders nothing when narrator has no sampleUrl", () => {
    const { container } = render(<AudioPreview narrator={narratorNoSample} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders play button and preview text", () => {
    render(<AudioPreview narrator={mockNarrator} />);
    expect(screen.getByLabelText(/play sample from sunny/i)).toBeDefined();
    expect(screen.getByText(/preview sunny's voice/i)).toBeDefined();
  });

  it("audio element has aria-label", () => {
    const { container } = render(<AudioPreview narrator={mockNarrator} />);
    const audio = container.querySelector("audio");
    expect(audio).not.toBeNull();
    expect(audio!.getAttribute("aria-label")).toBe("Audio sample from Sunny");
  });

  it("audio element has correct src and preload", () => {
    const { container } = render(<AudioPreview narrator={mockNarrator} />);
    const audio = container.querySelector("audio");
    expect(audio!.getAttribute("src")).toBe("/samples/narrator-luna-warm.mp3");
    expect(audio!.getAttribute("preload")).toBe("none");
  });

  it("shows error state when audio fails to load", () => {
    const { container } = render(<AudioPreview narrator={mockNarrator} />);
    const audio = container.querySelector("audio")!;
    fireEvent.error(audio);
    expect(screen.getByText(/audio preview not yet available/i)).toBeDefined();
  });
});
