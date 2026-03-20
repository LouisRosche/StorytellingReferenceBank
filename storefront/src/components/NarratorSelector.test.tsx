import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import NarratorSelector from "./NarratorSelector";
import type { Narrator } from "@/lib/storybooks";

const narrators: Narrator[] = [
  { id: "n1", name: "Sunny", description: "Warm voice", personaFile: "n1.json", tags: ["warm"] },
  { id: "n2", name: "Claire", description: "Bright voice", personaFile: "n2.json", tags: ["bright"] },
];

describe("NarratorSelector", () => {
  it("renders all narrators", () => {
    render(<NarratorSelector narrators={narrators} onSelect={() => {}} />);
    expect(screen.getByText("Sunny")).toBeInTheDocument();
    expect(screen.getByText("Claire")).toBeInTheDocument();
  });

  it("calls onSelect when narrator clicked", () => {
    const onSelect = vi.fn();
    render(<NarratorSelector narrators={narrators} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Sunny"));
    expect(onSelect).toHaveBeenCalledWith(narrators[0]);
  });

  it("marks selected narrator as checked", () => {
    render(<NarratorSelector narrators={narrators} onSelect={() => {}} selected="n1" />);
    const radio = screen.getByRole("radio", { name: /Sunny/ });
    expect(radio).toHaveAttribute("aria-checked", "true");
  });

  it("has proper radiogroup role", () => {
    render(<NarratorSelector narrators={narrators} onSelect={() => {}} />);
    expect(screen.getByRole("radiogroup")).toBeInTheDocument();
  });
});
