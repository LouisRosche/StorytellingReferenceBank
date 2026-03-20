import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest } from "next/server";

// Mock stripe module
vi.mock("@/lib/stripe", () => ({
  stripe: {
    checkout: {
      sessions: {
        create: vi.fn().mockResolvedValue({
          url: "https://checkout.stripe.com/test-session",
        }),
      },
    },
  },
  STRIPE_WEBHOOK_SECRET: "whsec_test",
  generateDownloadToken: vi.fn().mockReturnValue("test-token"),
}));

vi.mock("@/lib/env", () => ({
  getSiteUrl: () => "http://localhost:3000",
  validateEnv: () => {},
}));

import { POST } from "./route";

function makeRequest(body: Record<string, unknown>): NextRequest {
  return new NextRequest("http://localhost:3000/api/checkout", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" },
  });
}

describe("POST /api/checkout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 400 when slug is missing", async () => {
    const res = await POST(makeRequest({ format: "ebook" }));
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toMatch(/missing/i);
  });

  it("returns 400 when format is missing", async () => {
    const res = await POST(makeRequest({ slug: "luna-the-little-cloud" }));
    expect(res.status).toBe(400);
  });

  it("returns 400 for invalid format", async () => {
    const res = await POST(makeRequest({ slug: "luna-the-little-cloud", format: "vinyl" }));
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toMatch(/invalid format/i);
  });

  it("returns 404 for nonexistent book", async () => {
    const res = await POST(makeRequest({ slug: "nonexistent-book", format: "ebook" }));
    expect(res.status).toBe(404);
  });

  it("returns 400 for invalid narrator", async () => {
    const res = await POST(makeRequest({
      slug: "luna-the-little-cloud",
      format: "audiobook",
      narratorId: "fake-narrator",
    }));
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toMatch(/invalid narrator/i);
  });

  it("creates checkout session for valid request", async () => {
    const res = await POST(makeRequest({
      slug: "luna-the-little-cloud",
      format: "ebook",
    }));
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.url).toBe("https://checkout.stripe.com/test-session");
  });

  it("accepts valid narrator", async () => {
    const res = await POST(makeRequest({
      slug: "luna-the-little-cloud",
      format: "audiobook",
      narratorId: "narrator-luna-warm",
    }));
    expect(res.status).toBe(200);
  });
});
