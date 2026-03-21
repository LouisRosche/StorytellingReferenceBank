import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import fs from "fs";
import path from "path";

// Mock stripe to prevent env var validation errors on import
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

import type { Purchase } from "./db";

const TEST_DB_DIR = path.join(process.cwd(), "data");
const TEST_DB_PATH = path.join(TEST_DB_DIR, "purchases.json");

function makePurchase(overrides: Partial<Purchase> = {}): Purchase {
  return {
    id: "test-purchase-1",
    stripeSessionId: "cs_test_session_1",
    email: "test@example.com",
    slug: "luna-the-little-cloud",
    format: "ebook",
    narratorId: "",
    downloadTokens: { ebook: "token-abc" },
    createdAt: new Date().toISOString(),
    fulfilled: false,
    ...overrides,
  };
}

describe("db.ts", () => {
  let originalData: string | null = null;

  beforeEach(() => {
    // Back up existing DB if present
    if (fs.existsSync(TEST_DB_PATH)) {
      originalData = fs.readFileSync(TEST_DB_PATH, "utf-8");
    }
    // Start with empty DB
    if (!fs.existsSync(TEST_DB_DIR)) {
      fs.mkdirSync(TEST_DB_DIR, { recursive: true });
    }
    fs.writeFileSync(TEST_DB_PATH, "[]", "utf-8");
  });

  afterEach(() => {
    // Restore original DB
    if (originalData !== null) {
      fs.writeFileSync(TEST_DB_PATH, originalData, "utf-8");
    } else if (fs.existsSync(TEST_DB_PATH)) {
      fs.writeFileSync(TEST_DB_PATH, "[]", "utf-8");
    }
  });

  it("savePurchase creates a new purchase", async () => {
    const { savePurchase } = await import("./db");
    const p = makePurchase();
    savePurchase(p);

    const data = JSON.parse(fs.readFileSync(TEST_DB_PATH, "utf-8"));
    expect(data).toHaveLength(1);
    expect(data[0].id).toBe("test-purchase-1");
  });

  it("savePurchase upserts existing purchase by id", async () => {
    const { savePurchase } = await import("./db");
    const p = makePurchase();
    savePurchase(p);
    savePurchase({ ...p, fulfilled: true });

    const data = JSON.parse(fs.readFileSync(TEST_DB_PATH, "utf-8"));
    expect(data).toHaveLength(1);
    expect(data[0].fulfilled).toBe(true);
  });

  it("savePurchase handles multiple distinct purchases", async () => {
    const { savePurchase } = await import("./db");
    savePurchase(makePurchase({ id: "p1", stripeSessionId: "cs_1" }));
    savePurchase(makePurchase({ id: "p2", stripeSessionId: "cs_2" }));

    const data = JSON.parse(fs.readFileSync(TEST_DB_PATH, "utf-8"));
    expect(data).toHaveLength(2);
  });

  it("findPurchaseBySessionId returns matching purchase", async () => {
    const { savePurchase, findPurchaseBySessionId } = await import("./db");
    savePurchase(makePurchase());

    const found = findPurchaseBySessionId("cs_test_session_1");
    expect(found).toBeDefined();
    expect(found!.slug).toBe("luna-the-little-cloud");
  });

  it("findPurchaseBySessionId returns undefined for no match", async () => {
    const { findPurchaseBySessionId } = await import("./db");
    expect(findPurchaseBySessionId("nonexistent")).toBeUndefined();
  });

  it("findPurchasesByEmail is case-insensitive", async () => {
    const { savePurchase, findPurchasesByEmail } = await import("./db");
    savePurchase(makePurchase({ email: "User@Example.COM" }));

    const results = findPurchasesByEmail("user@example.com");
    expect(results).toHaveLength(1);
  });

  it("findPurchasesByEmail returns empty array for no match", async () => {
    const { findPurchasesByEmail } = await import("./db");
    expect(findPurchasesByEmail("nobody@nowhere.com")).toEqual([]);
  });

  it("hasProcessedEvent returns true for existing session", async () => {
    const { savePurchase, hasProcessedEvent } = await import("./db");
    savePurchase(makePurchase());

    expect(hasProcessedEvent("cs_test_session_1")).toBe(true);
  });

  it("hasProcessedEvent returns false for unknown session", async () => {
    const { hasProcessedEvent } = await import("./db");
    expect(hasProcessedEvent("cs_unknown")).toBe(false);
  });

  it("savePurchaseIfNew returns true and persists on first insert", async () => {
    const { savePurchaseIfNew } = await import("./db");
    const p = makePurchase();
    const result = savePurchaseIfNew(p);

    expect(result).toBe(true);
    const data = JSON.parse(fs.readFileSync(TEST_DB_PATH, "utf-8"));
    expect(data).toHaveLength(1);
    expect(data[0].stripeSessionId).toBe("cs_test_session_1");
  });

  it("savePurchaseIfNew returns false and does not duplicate on same stripeSessionId", async () => {
    const { savePurchaseIfNew } = await import("./db");
    const p1 = makePurchase({ id: "p1" });
    const p2 = makePurchase({ id: "p2" }); // same stripeSessionId, different id

    expect(savePurchaseIfNew(p1)).toBe(true);
    expect(savePurchaseIfNew(p2)).toBe(false);

    const data = JSON.parse(fs.readFileSync(TEST_DB_PATH, "utf-8"));
    expect(data).toHaveLength(1);
    expect(data[0].id).toBe("p1"); // only the first was persisted
  });

  it("savePurchaseIfNew allows different stripeSessionIds", async () => {
    const { savePurchaseIfNew } = await import("./db");
    const p1 = makePurchase({ id: "p1", stripeSessionId: "cs_1" });
    const p2 = makePurchase({ id: "p2", stripeSessionId: "cs_2" });

    expect(savePurchaseIfNew(p1)).toBe(true);
    expect(savePurchaseIfNew(p2)).toBe(true);

    const data = JSON.parse(fs.readFileSync(TEST_DB_PATH, "utf-8"));
    expect(data).toHaveLength(2);
  });
});
