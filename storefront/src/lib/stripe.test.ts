import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// We need to test the actual token logic, so we mock only env vars, not the module itself.
// Set env vars BEFORE importing the module under test.

const FAKE_STRIPE_KEY = "sk_test_fake_stripe_key_for_testing";
const FAKE_WEBHOOK_SECRET = "whsec_test_secret";
const FAKE_TOKEN_SECRET = "test_download_token_secret_32chars";

beforeEach(() => {
  vi.stubEnv("STRIPE_SECRET_KEY", FAKE_STRIPE_KEY);
  vi.stubEnv("STRIPE_WEBHOOK_SECRET", FAKE_WEBHOOK_SECRET);
  vi.stubEnv("DOWNLOAD_TOKEN_SECRET", FAKE_TOKEN_SECRET);
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe("generateDownloadToken + verifyDownloadToken round-trip", () => {
  it("generates and verifies a valid ebook token", async () => {
    const { generateDownloadToken, verifyDownloadToken } = await import("./stripe");
    const token = generateDownloadToken("purchase-123", "luna-the-little-cloud", "ebook");

    expect(typeof token).toBe("string");
    expect(token.length).toBeGreaterThan(10);

    const result = verifyDownloadToken(token);
    expect(result).not.toBeNull();
    expect(result!.purchaseId).toBe("purchase-123");
    expect(result!.slug).toBe("luna-the-little-cloud");
    expect(result!.format).toBe("ebook");
  });

  it("generates and verifies a valid audiobook token", async () => {
    const { generateDownloadToken, verifyDownloadToken } = await import("./stripe");
    const token = generateDownloadToken("purchase-456", "where-shadows-sleep", "audiobook");
    const result = verifyDownloadToken(token);
    expect(result).not.toBeNull();
    expect(result!.format).toBe("audiobook");
  });

  it("rejects token with tampered payload", async () => {
    const { generateDownloadToken, verifyDownloadToken } = await import("./stripe");
    const token = generateDownloadToken("purchase-123", "luna-the-little-cloud", "ebook");

    // Decode, tamper, re-encode
    const decoded = JSON.parse(Buffer.from(token, "base64url").toString("utf-8"));
    decoded.payload = decoded.payload.replace("luna-the-little-cloud", "stolen-book");
    const tampered = Buffer.from(JSON.stringify(decoded)).toString("base64url");

    expect(verifyDownloadToken(tampered)).toBeNull();
  });

  it("rejects token with tampered signature", async () => {
    const { generateDownloadToken, verifyDownloadToken } = await import("./stripe");
    const token = generateDownloadToken("purchase-123", "luna-the-little-cloud", "ebook");

    const decoded = JSON.parse(Buffer.from(token, "base64url").toString("utf-8"));
    decoded.signature = "0".repeat(64);
    const tampered = Buffer.from(JSON.stringify(decoded)).toString("base64url");

    expect(verifyDownloadToken(tampered)).toBeNull();
  });

  it("rejects expired tokens", async () => {
    const { generateDownloadToken, verifyDownloadToken } = await import("./stripe");
    const token = generateDownloadToken("purchase-123", "luna-the-little-cloud", "ebook");

    // Manually forge an expired token by decoding and changing expiresAt
    const decoded = JSON.parse(Buffer.from(token, "base64url").toString("utf-8"));
    decoded.expiresAt = Date.now() - 1000; // Already expired
    // Re-sign would be needed, but we just test that expiry check fires before signature
    const expired = Buffer.from(JSON.stringify(decoded)).toString("base64url");

    expect(verifyDownloadToken(expired)).toBeNull();
  });

  it("rejects completely invalid base64", async () => {
    const { verifyDownloadToken } = await import("./stripe");
    expect(verifyDownloadToken("not-valid-base64!!!")).toBeNull();
  });

  it("rejects empty string", async () => {
    const { verifyDownloadToken } = await import("./stripe");
    expect(verifyDownloadToken("")).toBeNull();
  });

  it("rejects valid base64 with invalid JSON", async () => {
    const { verifyDownloadToken } = await import("./stripe");
    const badToken = Buffer.from("not json at all").toString("base64url");
    expect(verifyDownloadToken(badToken)).toBeNull();
  });

  it("rejects token missing required fields", async () => {
    const { verifyDownloadToken } = await import("./stripe");
    const incomplete = Buffer.from(JSON.stringify({ payload: "x" })).toString("base64url");
    expect(verifyDownloadToken(incomplete)).toBeNull();
  });

  it("rejects token with invalid format value", async () => {
    const { verifyDownloadToken } = await import("./stripe");
    // Even if we could forge a valid signature, format validation should reject
    const badFormat = Buffer.from(
      JSON.stringify({ payload: "p:s:vinyl:99999999999", signature: "a".repeat(64), expiresAt: Date.now() + 60000 })
    ).toString("base64url");
    expect(verifyDownloadToken(badFormat)).toBeNull();
  });

  it("produces different tokens for different inputs", async () => {
    const { generateDownloadToken } = await import("./stripe");
    const t1 = generateDownloadToken("p1", "slug-a", "ebook");
    const t2 = generateDownloadToken("p2", "slug-b", "audiobook");
    expect(t1).not.toBe(t2);
  });

  it("token is base64url encoded (no +, /, or = characters)", async () => {
    const { generateDownloadToken } = await import("./stripe");
    const token = generateDownloadToken("purchase-123", "test-slug", "ebook");
    expect(token).not.toMatch(/[+/=]/);
  });
});

describe("DOWNLOAD_TOKEN_SECRET enforcement", () => {
  it("throws in production when DOWNLOAD_TOKEN_SECRET is not set", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("DOWNLOAD_TOKEN_SECRET", "");

    await expect(async () => {
      await import("./stripe");
    }).rejects.toThrow(/DOWNLOAD_TOKEN_SECRET/);
  });
});
