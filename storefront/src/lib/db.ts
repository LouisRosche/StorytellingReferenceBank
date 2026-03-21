import fs from "fs";
import path from "path";

/**
 * Lightweight JSON-file purchase database.
 * No external dependencies — just the filesystem.
 *
 * In production, replace with Supabase/Postgres/Turso.
 * This is sufficient for launch with low volume.
 */

export interface Purchase {
  id: string;
  stripeSessionId: string;
  email: string;
  slug: string;
  format: string;
  narratorId: string;
  downloadTokens: Record<string, string>;
  createdAt: string;
  fulfilled: boolean;
}

const DB_PATH = path.join(process.cwd(), "data", "purchases.json");

function ensureDbExists(): void {
  const dir = path.dirname(DB_PATH);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  if (!fs.existsSync(DB_PATH)) {
    fs.writeFileSync(DB_PATH, "[]", "utf-8");
  }
}

function readDb(): Purchase[] {
  ensureDbExists();
  const raw = fs.readFileSync(DB_PATH, "utf-8");
  return JSON.parse(raw);
}

const LOCK_PATH = DB_PATH + ".lock";
const LOCK_STALE_MS = 30_000; // 30 seconds — any lock older than this is considered stale

function acquireLock(maxRetries = 10, retryDelayMs = 50): void {
  for (let i = 0; i < maxRetries; i++) {
    try {
      fs.writeFileSync(LOCK_PATH, JSON.stringify({ pid: process.pid, ts: Date.now() }), {
        flag: "wx",
      });
      return;
    } catch {
      // Lock file exists — check if it's stale (holder crashed)
      if (isLockStale()) {
        try {
          fs.unlinkSync(LOCK_PATH);
          continue; // retry immediately after clearing stale lock
        } catch {
          // Another process cleared it first — retry normally
        }
      }
      // Non-spinning sync sleep via Atomics.wait
      try {
        const buf = new Int32Array(new SharedArrayBuffer(4));
        Atomics.wait(buf, 0, 0, retryDelayMs);
      } catch {
        // SharedArrayBuffer unavailable (e.g. missing COOP/COEP headers) —
        // fall back to a Date.now() busy-wait as last resort
        const end = Date.now() + retryDelayMs;
        while (Date.now() < end) { /* spin */ }
      }
    }
  }
  throw new Error("Could not acquire database lock");
}

/** A lock is stale if it's older than LOCK_STALE_MS or its holder PID is dead. */
function isLockStale(): boolean {
  try {
    const raw = fs.readFileSync(LOCK_PATH, "utf-8");
    const lock = JSON.parse(raw);
    // Time-based: if the lock is older than the threshold, it's stale
    if (typeof lock.ts === "number" && Date.now() - lock.ts > LOCK_STALE_MS) {
      return true;
    }
    // PID-based: check if the holder process is still alive
    if (typeof lock.pid === "number") {
      try {
        process.kill(lock.pid, 0); // signal 0 = existence check, no actual signal
        return false; // process is alive
      } catch {
        return true; // process is dead
      }
    }
    return false;
  } catch {
    return false; // can't read lock — let normal retry handle it
  }
}

function releaseLock(): void {
  try {
    fs.unlinkSync(LOCK_PATH);
  } catch {
    // Lock already released
  }
}

function writeDb(purchases: Purchase[]): void {
  ensureDbExists();
  fs.writeFileSync(DB_PATH, JSON.stringify(purchases, null, 2), "utf-8");
}

export function savePurchase(purchase: Purchase): void {
  acquireLock();
  try {
    const purchases = readDb();
    const existingIndex = purchases.findIndex((p) => p.id === purchase.id);
    if (existingIndex >= 0) {
      purchases[existingIndex] = purchase;
    } else {
      purchases.push(purchase);
    }
    writeDb(purchases);
  } finally {
    releaseLock();
  }
}

export function findPurchaseBySessionId(
  sessionId: string
): Purchase | undefined {
  return readDb().find((p) => p.stripeSessionId === sessionId);
}

export function findPurchasesByEmail(email: string): Purchase[] {
  return readDb().filter(
    (p) => p.email.toLowerCase() === email.toLowerCase()
  );
}

export function hasProcessedEvent(stripeSessionId: string): boolean {
  return readDb().some((p) => p.stripeSessionId === stripeSessionId);
}

/**
 * Atomically check-and-insert: returns true if the purchase was saved,
 * false if a record with the same stripeSessionId already exists.
 * Holds the lock across both the read and the write to prevent TOCTOU races
 * (e.g. concurrent Stripe webhook retries).
 */
export function savePurchaseIfNew(purchase: Purchase): boolean {
  acquireLock();
  try {
    const purchases = readDb();
    if (purchases.some((p) => p.stripeSessionId === purchase.stripeSessionId)) {
      return false; // duplicate
    }
    purchases.push(purchase);
    writeDb(purchases);
    return true;
  } finally {
    releaseLock();
  }
}
