import Stripe from "stripe";

if (!process.env.STRIPE_SECRET_KEY) {
  throw new Error(
    "STRIPE_SECRET_KEY is not set. Copy .env.example to .env.local and add your Stripe keys."
  );
}

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY, {
  apiVersion: "2026-02-25.clover",
  typescript: true,
});

/**
 * Generate a time-limited signed download URL.
 * In production this would use S3 presigned URLs or similar.
 * For now, it generates a HMAC-signed token with expiry.
 */
export function generateDownloadToken(
  purchaseId: string,
  slug: string,
  format: "ebook" | "audiobook"
): string {
  const crypto = require("crypto");
  const expiresAt = Date.now() + 14 * 24 * 60 * 60 * 1000; // 14 days
  const payload = `${purchaseId}:${slug}:${format}:${expiresAt}`;
  const secret = process.env.STRIPE_SECRET_KEY || "fallback-secret";
  const signature = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("hex");
  return Buffer.from(JSON.stringify({ payload, signature, expiresAt })).toString(
    "base64url"
  );
}

/**
 * Verify a download token is valid and not expired.
 */
export function verifyDownloadToken(
  token: string
): { purchaseId: string; slug: string; format: string } | null {
  try {
    const crypto = require("crypto");
    const decoded = JSON.parse(
      Buffer.from(token, "base64url").toString("utf-8")
    );
    const { payload, signature, expiresAt } = decoded;

    if (Date.now() > expiresAt) return null;

    const secret = process.env.STRIPE_SECRET_KEY || "fallback-secret";
    const expected = crypto
      .createHmac("sha256", secret)
      .update(payload)
      .digest("hex");

    if (signature !== expected) return null;

    const [purchaseId, slug, format] = payload.split(":");
    return { purchaseId, slug, format };
  } catch {
    return null;
  }
}
