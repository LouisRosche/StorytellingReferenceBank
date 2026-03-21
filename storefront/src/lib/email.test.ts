import { describe, it, expect, vi, beforeEach } from "vitest";

describe("email", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
    delete process.env.RESEND_API_KEY;
    delete process.env.RESEND_FROM_EMAIL;
  });

  describe("sendFulfillmentEmail - development (console)", () => {
    it("logs email to console when no RESEND_API_KEY", async () => {
      const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => {});
      const { sendFulfillmentEmail } = await import("./email");
      const result = await sendFulfillmentEmail({
        to: "test@example.com",
        bookTitle: "Test Book",
        format: "ebook",
        downloadLinks: [
          { format: "ebook", url: "http://localhost:3000/api/download?token=abc" },
        ],
      });
      expect(result).toBe(true);
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("FULFILLMENT EMAIL")
      );
      consoleSpy.mockRestore();
    });

    it("includes download links in email body", async () => {
      const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => {});
      const { sendFulfillmentEmail } = await import("./email");
      await sendFulfillmentEmail({
        to: "test@example.com",
        bookTitle: "Test Book",
        format: "bundle",
        downloadLinks: [
          { format: "ebook", url: "http://localhost/dl?t=1" },
          { format: "audiobook", url: "http://localhost/dl?t=2" },
        ],
      });
      const bodyCall = consoleSpy.mock.calls.find(
        (call) => typeof call[0] === "string" && call[0].includes("EBOOK:")
      );
      expect(bodyCall).toBeDefined();
      consoleSpy.mockRestore();
    });
  });

  describe("sendFulfillmentEmail - production (Resend)", () => {
    it("sends email via Resend API", async () => {
      process.env.RESEND_API_KEY = "re_test_key";
      const mockResponse = { ok: true, json: () => Promise.resolve({}) };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockResponse));

      const { sendFulfillmentEmail } = await import("./email");
      const result = await sendFulfillmentEmail({
        to: "buyer@example.com",
        bookTitle: "Luna",
        format: "ebook",
        downloadLinks: [{ format: "ebook", url: "http://example.com/dl" }],
      });
      expect(result).toBe(true);
      expect(fetch).toHaveBeenCalledWith(
        "https://api.resend.com/emails",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            Authorization: "Bearer re_test_key",
          }),
        })
      );
    });

    it("returns false when Resend API returns error", async () => {
      process.env.RESEND_API_KEY = "re_test_key";
      const mockResponse = {
        ok: false,
        text: () => Promise.resolve("rate limited"),
      };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockResponse));

      const { sendFulfillmentEmail } = await import("./email");
      const result = await sendFulfillmentEmail({
        to: "buyer@example.com",
        bookTitle: "Luna",
        format: "ebook",
        downloadLinks: [],
      });
      expect(result).toBe(false);
    });

    it("returns false on network error", async () => {
      process.env.RESEND_API_KEY = "re_test_key";
      vi.stubGlobal(
        "fetch",
        vi.fn().mockRejectedValue(new Error("Connection refused"))
      );

      const { sendFulfillmentEmail } = await import("./email");
      const result = await sendFulfillmentEmail({
        to: "buyer@example.com",
        bookTitle: "Luna",
        format: "ebook",
        downloadLinks: [],
      });
      expect(result).toBe(false);
    });

    it("uses custom from email when set", async () => {
      process.env.RESEND_API_KEY = "re_test_key";
      process.env.RESEND_FROM_EMAIL = "custom@mystore.com";
      const mockResponse = { ok: true };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockResponse));

      const { sendFulfillmentEmail } = await import("./email");
      await sendFulfillmentEmail({
        to: "buyer@example.com",
        bookTitle: "Luna",
        format: "ebook",
        downloadLinks: [],
      });

      const fetchCall = vi.mocked(fetch).mock.calls[0];
      const body = JSON.parse(fetchCall[1]!.body as string);
      expect(body.from).toContain("custom@mystore.com");
    });
  });
});
