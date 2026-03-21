import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest } from "next/server";

vi.mock("@/lib/stripe", () => ({
  stripe: {},
  STRIPE_WEBHOOK_SECRET: "whsec_test",
  generateDownloadToken: vi.fn(),
  verifyDownloadToken: vi.fn(),
}));

vi.mock("@/lib/env", () => ({
  getSiteUrl: () => "http://localhost:3000",
  validateEnv: () => {},
}));

vi.mock("@/lib/storage", () => ({
  getContentFile: vi.fn(),
}));

import { GET } from "./route";
import { verifyDownloadToken } from "@/lib/stripe";
import { getContentFile } from "@/lib/storage";

const mockVerify = verifyDownloadToken as ReturnType<typeof vi.fn>;
const mockGetContent = getContentFile as ReturnType<typeof vi.fn>;

function makeRequest(token?: string): NextRequest {
  const url = token
    ? `http://localhost:3000/api/download?token=${token}`
    : "http://localhost:3000/api/download";
  return new NextRequest(url);
}

describe("GET /api/download", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 400 when token is missing", async () => {
    const res = await GET(makeRequest());
    expect(res.status).toBe(400);
  });

  it("returns 403 for invalid token", async () => {
    mockVerify.mockReturnValue(null);
    const res = await GET(makeRequest("bad-token"));
    expect(res.status).toBe(403);
    const data = await res.json();
    expect(data.error).toMatch(/invalid|expired/i);
  });

  it("returns 404 for nonexistent book", async () => {
    mockVerify.mockReturnValue({ purchaseId: "p1", slug: "nonexistent", format: "ebook" });
    const res = await GET(makeRequest("valid-token"));
    expect(res.status).toBe(404);
  });

  it("returns 202 when file not ready", async () => {
    mockVerify.mockReturnValue({ purchaseId: "p1", slug: "luna-the-little-cloud", format: "ebook" });
    mockGetContent.mockResolvedValue(null);
    const res = await GET(makeRequest("valid-token"));
    expect(res.status).toBe(202);
    const data = await res.json();
    expect(data.error).toMatch(/not yet available/i);
  });

  it("streams file with correct headers", async () => {
    mockVerify.mockReturnValue({ purchaseId: "p1", slug: "luna-the-little-cloud", format: "ebook" });
    mockGetContent.mockResolvedValue({
      buffer: Buffer.from("fake pdf content"),
      contentType: "application/pdf",
      filename: "luna-the-little-cloud.pdf",
    });
    const res = await GET(makeRequest("valid-token"));
    expect(res.status).toBe(200);
    expect(res.headers.get("Content-Type")).toBe("application/pdf");
    expect(res.headers.get("Content-Disposition")).toContain("luna-the-little-cloud.pdf");
    expect(res.headers.get("Cache-Control")).toBe("private, no-cache");
  });
});
