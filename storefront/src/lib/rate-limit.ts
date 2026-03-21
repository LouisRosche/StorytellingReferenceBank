/**
 * Simple in-memory token-bucket rate limiter.
 *
 * Not suitable for multi-instance deployments — use Redis or an edge
 * rate-limiter (Vercel, Cloudflare) in production.
 */

interface TokenBucket {
  tokens: number;
  lastRefill: number;
}

interface RateLimitConfig {
  /** Maximum tokens (burst size) */
  maxTokens: number;
  /** Tokens added per second */
  refillRate: number;
}

const buckets = new Map<string, TokenBucket>();

const CLEANUP_INTERVAL_MS = 60_000;
const BUCKET_TTL_MS = 300_000; // 5 minutes

let lastCleanup = Date.now();

function cleanup() {
  const now = Date.now();
  if (now - lastCleanup < CLEANUP_INTERVAL_MS) return;
  lastCleanup = now;
  buckets.forEach((bucket, key) => {
    if (now - bucket.lastRefill > BUCKET_TTL_MS) {
      buckets.delete(key);
    }
  });
}

export function rateLimit(
  key: string,
  config: RateLimitConfig = { maxTokens: 10, refillRate: 1 }
): { allowed: boolean; retryAfterSeconds: number } {
  cleanup();

  const now = Date.now();
  let bucket = buckets.get(key);

  if (!bucket) {
    bucket = { tokens: config.maxTokens, lastRefill: now };
    buckets.set(key, bucket);
  }

  // Refill tokens based on elapsed time
  const elapsed = (now - bucket.lastRefill) / 1000;
  bucket.tokens = Math.min(
    config.maxTokens,
    bucket.tokens + elapsed * config.refillRate
  );
  bucket.lastRefill = now;

  if (bucket.tokens >= 1) {
    bucket.tokens -= 1;
    return { allowed: true, retryAfterSeconds: 0 };
  }

  const retryAfterSeconds = Math.ceil((1 - bucket.tokens) / config.refillRate);
  return { allowed: false, retryAfterSeconds };
}

/** Reset all buckets (for testing). */
export function resetRateLimits(): void {
  buckets.clear();
}
