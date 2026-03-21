import Stripe from "stripe";
import crypto from "crypto";

// --- Environment validation ---

const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY;
if (!STRIPE_SECRET_KEY) {
  throw new Error(
    "STRIPE_SECRET_KEY is not set. Copy .env.example to .env.local and add your Stripe keys."
  );
}

if (!process.env.STRIPE_WEBHOOK_SECRET) {
  throw new Error(
    "STRIPE_WEBHOOK_SECRET is not set. Run `stripe listen` and copy the webhook signing secret."
  );
}
export const STRIPE_WEBHOOK_SECRET: string = process.env.STRIPE_WEBHOOK_SECRET;

export const stripe = new Stripe(STRIPE_SECRET_KEY, {
  apiVersion: "2026-02-25.clover",
  typescript: true,
});

// --- Download token signing (HMAC-SHA256, timing-safe) ---

// Use a dedicated signing key, NOT the Stripe secret key.
// This limits blast radius: a token leak doesn't compromise the Stripe account.
const DOWNLOAD_TOKEN_SECRET = (() => {
  if (process.env.DOWNLOAD_TOKEN_SECRET) return process.env.DOWNLOAD_TOKEN_SECRET;
  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "DOWNLOAD_TOKEN_SECRET is not set. A dedicated signing key is required in production to limit blast radius of token leaks."
    );
  }
  return STRIPE_SECRET_KEY!;
})();

export function generateDownloadToken(
  purchaseId: string,
  slug: string,
  format: "ebook" | "audiobook"
): string {
  const expiresAt = Date.now() + 14 * 24 * 60 * 60 * 1000; // 14 days
  const payload = `${purchaseId}:${slug}:${format}:${expiresAt}`;
  const signature = crypto
    .createHmac("sha256", DOWNLOAD_TOKEN_SECRET)
    .update(payload)
    .digest("hex");
  return Buffer.from(
    JSON.stringify({ payload, signature, expiresAt })
  ).toString("base64url");
}

export function verifyDownloadToken(
  token: string
): { purchaseId: string; slug: string; format: "ebook" | "audiobook" } | null {
  try {
    const decoded = JSON.parse(
      Buffer.from(token, "base64url").toString("utf-8")
    );
    const { payload, signature, expiresAt } = decoded;

    if (typeof payload !== "string" || typeof signature !== "string") {
      return null;
    }

    if (Date.now() > expiresAt) return null;

    const expected = crypto
      .createHmac("sha256", DOWNLOAD_TOKEN_SECRET)
      .update(payload)
      .digest("hex");

    // Timing-safe comparison to prevent timing attacks
    const sigBuffer = Buffer.from(signature, "hex");
    const expectedBuffer = Buffer.from(expected, "hex");
    if (
      sigBuffer.length !== expectedBuffer.length ||
      !crypto.timingSafeEqual(sigBuffer, expectedBuffer)
    ) {
      return null;
    }

    const parts = payload.split(":");
    if (parts.length < 3) return null;
    const [purchaseId, slug, format] = parts;
    if (format !== "ebook" && format !== "audiobook") return null;
    // Reject slugs with path traversal characters
    if (!slug || /[\/\\]|\.\./.test(slug)) return null;
    return { purchaseId, slug, format };
  } catch {
    return null;
  }
}
