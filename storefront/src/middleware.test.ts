/**
 * Tests for the rate-limiting middleware.
 *
 * We test the exported middleware function directly with mock NextRequest
 * objects rather than spinning up a server.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { NextRequest } from "next/server";
import { middleware } from "./middleware";
import { resetRateLimits } from "@/lib/rate-limit";

function makeRequest(
  pathname: string,
  ip: string = "192.168.1.1"
): NextRequest {
  const url = new URL(pathname, "http://localhost:3000");
  const req = new NextRequest(url, {
    headers: { "x-forwarded-for": ip },
  });
  return req;
}

beforeEach(() => {
  resetRateLimits();
});

describe("middleware", () => {
  it("passes through non-API routes", () => {
    const req = makeRequest("/books/luna");
    const res = middleware(req);
    // NextResponse.next() has no status override — it's a passthrough
    expect(res.status).not.toBe(429);
  });

  it("allows checkout requests within burst", () => {
    for (let i = 0; i < 5; i++) {
      const res = middleware(makeRequest("/api/checkout"));
      expect(res.status).not.toBe(429);
    }
  });

  it("blocks checkout after burst exhausted", () => {
    // Exhaust 5-token burst
    for (let i = 0; i < 5; i++) {
      middleware(makeRequest("/api/checkout"));
    }
    const res = middleware(makeRequest("/api/checkout"));
    expect(res.status).toBe(429);
  });

  it("returns Retry-After header on 429", async () => {
    for (let i = 0; i < 5; i++) {
      middleware(makeRequest("/api/checkout"));
    }
    const res = middleware(makeRequest("/api/checkout"));
    expect(res.headers.get("Retry-After")).toBeTruthy();
    const body = await res.json();
    expect(body.error).toContain("Too many requests");
  });

  it("isolates rate limits by IP", () => {
    // Exhaust IP-1
    for (let i = 0; i < 5; i++) {
      middleware(makeRequest("/api/checkout", "10.0.0.1"));
    }
    const blockedRes = middleware(makeRequest("/api/checkout", "10.0.0.1"));
    expect(blockedRes.status).toBe(429);

    // IP-2 should still be allowed
    const allowedRes = middleware(makeRequest("/api/checkout", "10.0.0.2"));
    expect(allowedRes.status).not.toBe(429);
  });

  it("allows download with higher burst (10)", () => {
    for (let i = 0; i < 10; i++) {
      const res = middleware(makeRequest("/api/download"));
      expect(res.status).not.toBe(429);
    }
    const blocked = middleware(makeRequest("/api/download"));
    expect(blocked.status).toBe(429);
  });

  it("uses x-real-ip fallback", () => {
    const url = new URL("/api/checkout", "http://localhost:3000");
    const req = new NextRequest(url, {
      headers: { "x-real-ip": "172.16.0.1" },
    });
    const res = middleware(req);
    expect(res.status).not.toBe(429);
  });
});
