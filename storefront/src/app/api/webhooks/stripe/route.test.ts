import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest } from "next/server";

const mockConstructEvent = vi.fn();
const mockGenerateDownloadToken = vi.fn().mockReturnValue("tok_test123");
const mockSavePurchase = vi.fn();
const mockHasProcessedEvent = vi.fn().mockReturnValue(false);
const mockSendFulfillmentEmail = vi.fn().mockResolvedValue(true);

vi.mock("@/lib/stripe", () => ({
  stripe: {
    webhooks: {
      constructEvent: (...args: unknown[]) => mockConstructEvent(...args),
    },
  },
  STRIPE_WEBHOOK_SECRET: "whsec_test_secret",
  generateDownloadToken: (...args: unknown[]) =>
    mockGenerateDownloadToken(...args),
}));

vi.mock("@/lib/env", () => ({
  getSiteUrl: () => "http://localhost:3000",
  validateEnv: () => {},
}));

vi.mock("@/lib/storybooks", () => ({
  getStorybook: (slug: string) =>
    slug === "luna-the-little-cloud"
      ? { title: "Luna the Little Cloud", slug: "luna-the-little-cloud" }
      : undefined,
}));

vi.mock("@/lib/db", () => ({
  savePurchase: (...args: unknown[]) => mockSavePurchase(...args),
  hasProcessedEvent: (...args: unknown[]) => mockHasProcessedEvent(...args),
}));

vi.mock("@/lib/email", () => ({
  sendFulfillmentEmail: (...args: unknown[]) =>
    mockSendFulfillmentEmail(...args),
}));

// Mock crypto.randomUUID
vi.stubGlobal("crypto", { randomUUID: () => "test-uuid-1234" });

import { POST } from "./route";

function makeWebhookRequest(body: string, signature = "sig_valid"): NextRequest {
  return new NextRequest("http://localhost:3000/api/webhooks/stripe", {
    method: "POST",
    body,
    headers: {
      "Content-Type": "application/json",
      "stripe-signature": signature,
    },
  });
}

function makeCheckoutEvent(overrides: Record<string, unknown> = {}) {
  return {
    type: "checkout.session.completed",
    data: {
      object: {
        id: "cs_test_session_123",
        customer_details: { email: "customer@example.com" },
        metadata: {
          slug: "luna-the-little-cloud",
          format: "ebook",
          narratorId: "",
        },
        ...overrides,
      },
    },
  };
}

describe("POST /api/webhooks/stripe", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockHasProcessedEvent.mockReturnValue(false);
    mockSendFulfillmentEmail.mockResolvedValue(true);
    mockConstructEvent.mockReturnValue(makeCheckoutEvent());
  });

  it("returns 400 when stripe-signature header is missing", async () => {
    const req = new NextRequest("http://localhost:3000/api/webhooks/stripe", {
      method: "POST",
      body: "{}",
    });
    const res = await POST(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toMatch(/missing stripe-signature/i);
  });

  it("returns 400 when signature verification fails", async () => {
    mockConstructEvent.mockImplementation(() => {
      throw new Error("Invalid signature");
    });
    const res = await POST(makeWebhookRequest("{}", "bad_sig"));
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe("Invalid signature");
  });

  it("returns 200 for duplicate event (idempotency)", async () => {
    mockHasProcessedEvent.mockReturnValue(true);
    const res = await POST(makeWebhookRequest("{}"));
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.duplicate).toBe(true);
    expect(mockSavePurchase).not.toHaveBeenCalled();
  });

  it("returns 422 when metadata is missing slug", async () => {
    mockConstructEvent.mockReturnValue({
      type: "checkout.session.completed",
      data: {
        object: {
          id: "cs_test_no_slug",
          metadata: { format: "ebook" },
        },
      },
    });
    const res = await POST(makeWebhookRequest("{}"));
    expect(res.status).toBe(422);
    const data = await res.json();
    expect(data.error).toMatch(/missing metadata/i);
  });

  it("returns 422 when metadata is missing format", async () => {
    mockConstructEvent.mockReturnValue({
      type: "checkout.session.completed",
      data: {
        object: {
          id: "cs_test_no_format",
          metadata: { slug: "luna-the-little-cloud" },
        },
      },
    });
    const res = await POST(makeWebhookRequest("{}"));
    expect(res.status).toBe(422);
  });

  it("returns 422 when book is not found", async () => {
    mockConstructEvent.mockReturnValue({
      type: "checkout.session.completed",
      data: {
        object: {
          id: "cs_test_bad_book",
          metadata: { slug: "nonexistent-book", format: "ebook" },
        },
      },
    });
    const res = await POST(makeWebhookRequest("{}"));
    expect(res.status).toBe(422);
    const data = await res.json();
    expect(data.error).toMatch(/book not found/i);
  });

  it("processes ebook purchase and sends fulfillment email", async () => {
    const res = await POST(makeWebhookRequest("{}"));
    expect(res.status).toBe(200);
    expect(mockGenerateDownloadToken).toHaveBeenCalledWith(
      "cs_test_session_123",
      "luna-the-little-cloud",
      "ebook"
    );
    expect(mockSendFulfillmentEmail).toHaveBeenCalledWith(
      expect.objectContaining({
        to: "customer@example.com",
        bookTitle: "Luna the Little Cloud",
        format: "ebook",
      })
    );
    // Should save purchase twice — once unfulfilled, once fulfilled
    expect(mockSavePurchase).toHaveBeenCalledTimes(2);
    expect(mockSavePurchase).toHaveBeenLastCalledWith(
      expect.objectContaining({ fulfilled: true })
    );
  });

  it("generates both tokens for bundle format", async () => {
    mockConstructEvent.mockReturnValue(
      makeCheckoutEvent({
        metadata: {
          slug: "luna-the-little-cloud",
          format: "bundle",
          narratorId: "narrator-luna-warm",
        },
      })
    );
    const res = await POST(makeWebhookRequest("{}"));
    expect(res.status).toBe(200);
    expect(mockGenerateDownloadToken).toHaveBeenCalledTimes(2);
    expect(mockGenerateDownloadToken).toHaveBeenCalledWith(
      "cs_test_session_123",
      "luna-the-little-cloud",
      "ebook"
    );
    expect(mockGenerateDownloadToken).toHaveBeenCalledWith(
      "cs_test_session_123",
      "luna-the-little-cloud",
      "audiobook"
    );
  });

  it("marks purchase unfulfilled when email fails", async () => {
    mockSendFulfillmentEmail.mockResolvedValue(false);
    const res = await POST(makeWebhookRequest("{}"));
    expect(res.status).toBe(200);
    // Should only save once (unfulfilled), not update to fulfilled
    expect(mockSavePurchase).toHaveBeenCalledTimes(1);
    expect(mockSavePurchase).toHaveBeenCalledWith(
      expect.objectContaining({ fulfilled: false })
    );
  });

  it("marks purchase fulfilled when no customer email", async () => {
    mockConstructEvent.mockReturnValue(
      makeCheckoutEvent({ customer_details: {} })
    );
    const res = await POST(makeWebhookRequest("{}"));
    expect(res.status).toBe(200);
    expect(mockSendFulfillmentEmail).not.toHaveBeenCalled();
    // Should save fulfilled even without email
    expect(mockSavePurchase).toHaveBeenCalledTimes(2);
    expect(mockSavePurchase).toHaveBeenLastCalledWith(
      expect.objectContaining({ fulfilled: true })
    );
  });

  it("acknowledges unhandled event types", async () => {
    mockConstructEvent.mockReturnValue({
      type: "payment_intent.created",
      data: { object: {} },
    });
    const res = await POST(makeWebhookRequest("{}"));
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.received).toBe(true);
    expect(mockSavePurchase).not.toHaveBeenCalled();
  });

  it("handles non-Error exceptions in signature verification", async () => {
    mockConstructEvent.mockImplementation(() => {
      throw "string error";
    });
    const res = await POST(makeWebhookRequest("{}", "bad"));
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe("Invalid signature");
  });
});
