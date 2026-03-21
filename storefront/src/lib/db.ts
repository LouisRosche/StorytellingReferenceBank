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

function acquireLock(maxRetries = 10, retryDelayMs = 50): void {
  for (let i = 0; i < maxRetries; i++) {
    try {
      fs.writeFileSync(LOCK_PATH, String(process.pid), {
        flag: "wx",
      });
      return;
    } catch {
      // Lock file exists — another request is writing.
      // Use Atomics.wait on a shared buffer for a non-spinning sync sleep.
      const buf = new Int32Array(new SharedArrayBuffer(4));
      Atomics.wait(buf, 0, 0, retryDelayMs);
    }
  }
  throw new Error("Could not acquire database lock");
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
