import { describe, it, expect, vi, afterEach } from "vitest";

// Don't import at top level — we need env vars set first
afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe("validateEnv", () => {
  it("throws when STRIPE_SECRET_KEY is missing", async () => {
    vi.stubEnv("STRIPE_SECRET_KEY", "");
    vi.stubEnv("STRIPE_WEBHOOK_SECRET", "whsec_test");

    const { validateEnv } = await import("./env");
    expect(() => validateEnv()).toThrow(/STRIPE_SECRET_KEY/);
  });

  it("throws when STRIPE_WEBHOOK_SECRET is missing", async () => {
    vi.stubEnv("STRIPE_SECRET_KEY", "sk_test_123");
    vi.stubEnv("STRIPE_WEBHOOK_SECRET", "");

    const { validateEnv } = await import("./env");
    expect(() => validateEnv()).toThrow(/STRIPE_WEBHOOK_SECRET/);
  });

  it("succeeds when all required vars are set", async () => {
    vi.stubEnv("STRIPE_SECRET_KEY", "sk_test_123");
    vi.stubEnv("STRIPE_WEBHOOK_SECRET", "whsec_test");
    vi.stubEnv("NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY", "pk_test_123");
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "http://example.com");

    const { validateEnv } = await import("./env");
    expect(() => validateEnv()).not.toThrow();
  });

  it("warns but does not throw when recommended vars are missing", async () => {
    vi.stubEnv("STRIPE_SECRET_KEY", "sk_test_123");
    vi.stubEnv("STRIPE_WEBHOOK_SECRET", "whsec_test");
    vi.stubEnv("NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY", "");
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "");

    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const { validateEnv } = await import("./env");
    expect(() => validateEnv()).not.toThrow();
    expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining("NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY"));
    warnSpy.mockRestore();
  });
});

describe("getSiteUrl", () => {
  it("returns env var when set", async () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "https://my-store.com");
    const { getSiteUrl } = await import("./env");
    expect(getSiteUrl()).toBe("https://my-store.com");
  });

  it("falls back to localhost when not set", async () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "");
    const { getSiteUrl } = await import("./env");
    expect(getSiteUrl()).toBe("http://localhost:3000");
  });
});
