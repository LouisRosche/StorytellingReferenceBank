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

function writeDb(purchases: Purchase[]): void {
  ensureDbExists();
  fs.writeFileSync(DB_PATH, JSON.stringify(purchases, null, 2), "utf-8");
}

export function savePurchase(purchase: Purchase): void {
  const purchases = readDb();
  purchases.push(purchase);
  writeDb(purchases);
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
