import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import PurchaseButton from "./PurchaseButton";

describe("PurchaseButton", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders label and price", () => {
    render(<PurchaseButton slug="test" format="ebook" label="Digital Book" priceInCents={499} />);
    expect(screen.getByText(/Digital Book/)).toBeInTheDocument();
    expect(screen.getByText(/\$4\.99/)).toBeInTheDocument();
  });

  it("has accessible purchase label", () => {
    render(<PurchaseButton slug="test" format="ebook" label="Digital Book" priceInCents={499} />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-label", "Purchase Digital Book for $4.99");
  });

  it("shows loading state during checkout", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(() => {}));
    render(<PurchaseButton slug="test" format="ebook" label="Digital Book" priceInCents={499} />);
    fireEvent.click(screen.getByRole("button"));
    expect(await screen.findByText("Processing...")).toBeInTheDocument();
  });

  it("handles failed checkout gracefully", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ error: "Server error" }), { status: 500 }));
    vi.spyOn(globalThis, "alert").mockImplementation(() => {});
    render(<PurchaseButton slug="test" format="ebook" label="Digital Book" priceInCents={499} />);
    fireEvent.click(screen.getByRole("button"));
    await waitFor(() => {
      expect(globalThis.alert).toHaveBeenCalledWith("Server error");
    });
  });
});
