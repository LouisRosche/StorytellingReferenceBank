import { describe, it, expect, beforeEach } from "vitest";
import { rateLimit, resetRateLimits } from "./rate-limit";

beforeEach(() => {
  resetRateLimits();
});

describe("rateLimit", () => {
  it("allows requests within limit", () => {
    const config = { maxTokens: 3, refillRate: 1 };
    expect(rateLimit("test-a", config).allowed).toBe(true);
    expect(rateLimit("test-a", config).allowed).toBe(true);
    expect(rateLimit("test-a", config).allowed).toBe(true);
  });

  it("blocks after burst is exhausted", () => {
    const config = { maxTokens: 2, refillRate: 1 };
    rateLimit("test-b", config);
    rateLimit("test-b", config);
    const result = rateLimit("test-b", config);
    expect(result.allowed).toBe(false);
    expect(result.retryAfterSeconds).toBeGreaterThan(0);
  });

  it("isolates keys from each other", () => {
    const config = { maxTokens: 1, refillRate: 1 };
    rateLimit("key-1", config);
    // key-1 is now exhausted, but key-2 should still work
    expect(rateLimit("key-2", config).allowed).toBe(true);
  });

  it("uses default config when none provided", () => {
    // Default is 10 tokens — should allow first request
    expect(rateLimit("test-default").allowed).toBe(true);
  });

  it("returns retry-after when blocked", () => {
    const config = { maxTokens: 1, refillRate: 0.5 }; // refill 1 per 2s
    rateLimit("test-retry", config);
    const result = rateLimit("test-retry", config);
    expect(result.allowed).toBe(false);
    expect(result.retryAfterSeconds).toBe(2);
  });
});
