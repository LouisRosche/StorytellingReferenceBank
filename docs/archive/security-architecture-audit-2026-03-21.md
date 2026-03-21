# Adversarial Security Architecture Audit

**Date**: 2026-03-21
**Scope**: Full codebase — storefront (Next.js/Stripe), Python production pipeline, student portal
**Branch**: `main` @ `d235cfe`
**Methodology**: Red-team adversarial analysis with static analysis, control-flow tracing, and exploit scenario construction

---

## Executive Summary

The codebase demonstrates competent security hygiene in several areas — Stripe webhook verification, HMAC token signing with timing-safe comparison, PBKDF2 hashing, and path traversal protection. However, **6 critical and high-severity architectural flaws** exist that would allow an adversary to bypass access controls, poison application state, exfiltrate customer PII, or deny service. The root causes are not superficial bugs but **structural design decisions** that must be addressed before production deployment.

---

## Findings

### FINDING 1: Path Traversal in Local Content Storage via Token Payload Injection

**Severity**: Critical
**Location**: `storefront/src/lib/storage.ts:55`, `storefront/src/app/api/download/route.ts:27,43`

#### Architectural Root Cause

The `slug` value embedded in download tokens is trusted without sanitization when constructing filesystem paths. The `verifyDownloadToken` function at `storefront/src/lib/stripe.ts:85-89` splits the payload by `:` and returns the `slug` verbatim. This slug is then passed to `getFromLocalStorage` which uses `path.join()` — a function that **resolves** `..` sequences:

```typescript
// storage.ts:55 — slug is attacker-controlled via token payload
const filePath = path.join(CONTENT_DIR, slug, `${format}.${ext}`);
```

#### Exploit Trace

1. Attacker purchases a book, receiving a valid download token.
2. Attacker decodes the base64url token, extracts the HMAC signing structure.
3. If the attacker obtains `DOWNLOAD_TOKEN_SECRET` (via config leak, log exposure, or dev-mode fallback to Stripe key), they forge a token with `slug` = `../../etc` and `format` = `ebook`.
4. `path.join(CONTENT_DIR, "../../etc", "ebook.pdf")` resolves to an arbitrary path on the filesystem.
5. The server reads and streams the file contents via the download endpoint.

**Compounding factor**: In development mode, `DOWNLOAD_TOKEN_SECRET` falls back to `STRIPE_SECRET_KEY` (`stripe.ts:36`). If a developer's `.env.local` leaks (common in CI logs, error pages), both the Stripe account and the signing key are compromised simultaneously — the exact blast-radius separation the code comments claim to prevent.

#### Structural Remediation

```typescript
// storage.ts — add slug sanitization before path construction
function sanitizeSlug(slug: string): string | null {
  // Only allow alphanumeric, hyphens, underscores
  if (!/^[a-zA-Z0-9_-]+$/.test(slug)) return null;
  return slug;
}

export async function getContentFile(
  slug: string,
  format: string
): Promise<StorageFile | null> {
  const safeSlug = sanitizeSlug(slug);
  if (!safeSlug) return null;
  // ... rest of function
}
```

Also add to `verifyDownloadToken`:
```typescript
if (slug.includes('..') || slug.includes('/') || slug.includes('\\')) return null;
```

---

### FINDING 2: Database Race Condition — Read-Modify-Write Without Atomicity

**Severity**: Critical
**Location**: `storefront/src/lib/db.ts:36-39,70-78,80-88`

#### Architectural Root Cause

The `savePurchase` function performs a non-atomic read-modify-write cycle. `readDb()` (line 81) reads the full JSON file, then `writeDb()` (line 88) overwrites it. The lock is only held during `writeFileSync` (lines 72-77), **not during the read**. Two concurrent webhook deliveries can:

```
Thread A: readDb() → [purchase1, purchase2]
Thread B: readDb() → [purchase1, purchase2]    // same stale snapshot
Thread A: push(purchase3) → writeDb([purchase1, purchase2, purchase3])
Thread B: push(purchase4) → writeDb([purchase1, purchase2, purchase4])  // purchase3 LOST
```

The `acquireLock` function itself has a **busy-wait spin loop** (lines 53-56) that blocks the Node.js event loop, causing cascading latency under concurrent webhook load. This is the worst possible implementation for a single-threaded runtime: it prevents the very I/O operations it's trying to coordinate.

#### Exploit Trace

1. Stripe retries a webhook due to timeout (caused by the busy-wait blocking the event loop).
2. Two concurrent POST handlers both call `readDb()` before either acquires the lock.
3. The second write silently drops the first purchase record.
4. Customer receives email with download links, but their purchase record no longer exists in the database.
5. Future lookup via `findPurchaseBySessionId` returns `undefined`.

#### Structural Remediation

```typescript
// db.ts — atomic read-modify-write with lock around entire operation
export function savePurchase(purchase: Purchase): void {
  acquireLock();
  try {
    ensureDbExists();
    const raw = fs.readFileSync(DB_PATH, "utf-8");
    const purchases: Purchase[] = JSON.parse(raw);
    const existingIndex = purchases.findIndex((p) => p.id === purchase.id);
    if (existingIndex >= 0) {
      purchases[existingIndex] = purchase;
    } else {
      purchases.push(purchase);
    }
    fs.writeFileSync(DB_PATH, JSON.stringify(purchases, null, 2), "utf-8");
  } finally {
    releaseLock();
  }
}

// Replace busy-wait with async retry using setTimeout,
// or better: use SQLite (better-sqlite3) for actual ACID guarantees.
```

---

### FINDING 3: Rate Limiter Bypass via IP Header Spoofing

**Severity**: High
**Location**: `storefront/src/middleware.ts:10-16`, `storefront/src/lib/rate-limit.ts:20`

#### Architectural Root Cause

Two compounding failures:

1. **Untrusted IP source**: `getClientIp` trusts `x-forwarded-for` and `x-real-ip` headers unconditionally. Any HTTP client can set these headers to arbitrary values, creating a fresh rate-limit bucket per request.

2. **In-memory state**: The token-bucket Map exists only in the current process. Serverless deployments (Vercel) spin up new instances per request — each with an empty Map. The rate limiter is **structurally incapable** of limiting anything in the target deployment environment.

#### Exploit Trace

```bash
# Bypass via header spoofing — each request gets a fresh bucket
for i in $(seq 1 1000); do
  curl -H "X-Forwarded-For: 10.0.0.$i" https://target/api/checkout \
    -d '{"slug":"book","format":"ebook"}'
done
```

Even without spoofing, on Vercel/serverless, every cold start resets all buckets.

#### Structural Remediation

For Vercel: use `@vercel/edge-config` or Upstash Redis rate limiting.
For self-hosted: use Redis-backed rate limiter.
For immediate fix: validate IP against trusted proxy configuration:

```typescript
function getClientIp(request: NextRequest): string {
  // Only trust x-forwarded-for from known reverse proxies
  // In Vercel, the platform sets this correctly — but validate
  const xff = request.headers.get("x-forwarded-for");
  if (xff) {
    // Take the LAST entry (closest to the server), not the first (client-controlled)
    const ips = xff.split(",").map(s => s.trim());
    return ips[ips.length - 1] || "unknown";
  }
  return request.ip || "unknown";
}
```

---

### FINDING 4: Customer PII Stored Unencrypted in Plaintext JSON

**Severity**: High
**Location**: `storefront/src/lib/db.ts:12-22,24,74`

#### Architectural Root Cause

Customer email addresses and HMAC download tokens are written in cleartext to `data/purchases.json` on the filesystem. This file:

- Is readable by any process running as the same user.
- Persists indefinitely with no rotation or cleanup.
- Contains download tokens that grant 14-day file access — effectively session credentials stored at rest.
- Has no encryption, no access logging, no audit trail.

The `data/` directory is in `.gitignore` for the storefront but lives on the deployment filesystem. A single directory traversal, LFI, or misconfigured backup pipeline exposes every customer's email and active download credentials.

#### Exploit Trace

1. Attacker exploits Finding 1 (path traversal) with a forged token containing `slug` = `../../data/purchases`.
2. Server reads `data/purchases.json` and streams it as a download.
3. Attacker obtains all customer emails and valid download tokens.
4. Attacker uses stolen tokens to download all purchased content.

#### Structural Remediation

Replace filesystem JSON with SQLite (`better-sqlite3`) with column-level encryption for PII fields. At minimum:
- Encrypt email addresses at rest using a separate `DB_ENCRYPTION_KEY`.
- Do not store download tokens in the database — they are derivable from the purchase ID and signing key; store only purchase metadata.
- Add file-access audit logging.

---

### FINDING 5: Student Portal Access Code System — Complete Client-Side Bypass

**Severity**: High
**Location**: `student-portal/index.html:1446-1447,1109-1138`, `scripts/manage_student_codes.py:29-40,60-64`

#### Architectural Root Cause

The student portal is a static HTML page with **zero server-side enforcement**. The access code check is pure client-side JavaScript gated by a `sessionStorage` flag. Three independent bypass vectors exist:

**Bypass A — SessionStorage injection** (5 seconds):
```javascript
sessionStorage.setItem('srb_unlocked', '1');
location.reload();
```

**Bypass B — Brute-force all codes** (~10 minutes):
The code space is `24 adjectives × 24 nouns × 9000 digits = 5,184,000` combinations (~19.5 bits of entropy). With PBKDF2 at 100K iterations, a modern GPU can test ~10K hashes/second. Total time: ~9 minutes to recover all 8 active codes from the public `codes.json`.

**Bypass C — Direct content access**:
All library content is served as static markdown from the public GitHub Pages deployment. Direct URL access bypasses the portal entirely.

The `DEPLOY.md` acknowledges this is intentional ("access code protects the UX, not the content"), but the architecture still presents these codes as "access control" to end users, creating a false sense of security.

#### Structural Remediation

If content must be protected:
- Move to a server-rendered portal with session-based authentication.
- Serve content through an authenticated API, not static files.
- Increase code entropy: expand word lists to 200+ items each, use 6-digit suffix (~26 bits minimum).

If content is intentionally public (current design):
- Remove the access code system entirely and use a simple landing page.
- Or: clearly document to stakeholders that the code is a UX convenience, not a security boundary. Remove any language suggesting "protection."

---

### FINDING 6: Missing Content-Security-Policy Header

**Severity**: Medium
**Location**: `storefront/next.config.js:4-20`

#### Architectural Root Cause

The security headers are well-configured (HSTS, X-Frame-Options DENY, nosniff, Permissions-Policy) but **Content-Security-Policy is absent**. Without CSP, any XSS vulnerability — even a future one introduced by a dependency update — has unrestricted access to exfiltrate data, inject scripts, or redirect to phishing pages.

For a storefront handling Stripe payments, CSP is not optional. A single reflected XSS could steal checkout sessions or inject fake payment forms.

#### Structural Remediation

```javascript
// next.config.js — add CSP header
{
  key: "Content-Security-Policy",
  value: [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://js.stripe.com",
    "frame-src https://js.stripe.com",
    "connect-src 'self' https://api.stripe.com",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join("; "),
},
```

---

### FINDING 7: S3/R2 Storage Authentication via Bearer Token Instead of Request Signing

**Severity**: Medium
**Location**: `storefront/src/lib/storage.ts:82-90`

#### Architectural Root Cause

Cloud storage fetches use a static `Authorization: Bearer` header instead of AWS SigV4 request signing. This means:

1. The bearer token is sent in plaintext HTTP headers on every request. If HTTPS terminates at a load balancer or CDN edge, the token traverses internal networks in the clear.
2. The token cannot be scoped to specific objects or operations — it's a skeleton key for the entire bucket.
3. No request expiration — replayed requests are valid indefinitely.
4. The comment on line 85 acknowledges this: "For private S3, use AWS SDK with signed requests" — but the code doesn't implement it.

#### Structural Remediation

Use `@aws-sdk/client-s3` with `GetObjectCommand` for proper SigV4-signed requests. For Cloudflare R2, use the S3-compatible API with the same SDK.

---

### FINDING 8: Webhook Double-Save Race with Email Failure

**Severity**: Medium
**Location**: `storefront/src/app/api/webhooks/stripe/route.ts:85-126`

#### Architectural Root Cause

The webhook handler saves the purchase twice: once as `fulfilled: false` (line 87-97), then again as `fulfilled: true` after email success (line 113-123). If the email call times out and Stripe retries the webhook:

1. First delivery: saves purchase (fulfilled=false), email hangs, Stripe times out.
2. Second delivery: `hasProcessedEvent` returns `true` (line 38), skips processing entirely.
3. Purchase remains `fulfilled: false` permanently — customer never receives download links.
4. No recovery mechanism exists. No admin dashboard, no retry queue, no alerting.

#### Structural Remediation

Separate fulfillment from acknowledgment:
```typescript
// Save purchase immediately as acknowledged
savePurchase({ ...purchase, fulfilled: false });

// Return 200 to Stripe immediately (prevent retries)
// Queue email asynchronously with retry logic
await queueFulfillmentEmail(purchaseId, customerEmail, downloadLinks);

// Mark fulfilled only when email actually sends (via background job)
```

---

### FINDING 9: Temporary File Predictable Path in Web Studio

**Severity**: Low
**Location**: `scripts/web_studio.py:194,444`

#### Architectural Root Cause

Audio output files are written to predictable paths (`/tmp/web_studio_output.wav`, `/tmp/clone_test.wav`). On multi-user systems, this enables:
- Symlink attacks: attacker creates a symlink at the predictable path pointing to a sensitive file; the write overwrites the target.
- Information disclosure: attacker reads the predictable path to obtain generated audio.

This is low severity because the tool is designed for local single-user operation, but the pattern is a latent vulnerability if the tool is ever exposed to multi-user environments.

#### Structural Remediation

```python
import tempfile
fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="web_studio_")
os.close(fd)
```

---

## Positive Findings (What's Done Right)

| Area | Assessment |
|------|-----------|
| Stripe webhook signature verification | Correct: `constructEvent` with raw body and signature header |
| Download token HMAC | Excellent: SHA256 HMAC with timing-safe comparison, 14-day expiry, dedicated key separation |
| Path traversal in Python scripts | Solid: `_is_safe_path()` with `resolve().relative_to()` pattern |
| No subprocess/eval/exec | Clean: All Python scripts avoid shell execution and dynamic code evaluation |
| PBKDF2 hashing for student codes | Good: 100K iterations, though entropy of code space is insufficient |
| Security headers | Strong: HSTS with preload, X-Frame-Options DENY, nosniff, restrictive Permissions-Policy |
| Stripe client-side URL validation | Correct: `PurchaseButton.tsx` validates checkout URL starts with `https://checkout.stripe.com/` |
| No hardcoded secrets | Clean: All credentials use environment variables with `.env.example` templates |

---

## Risk Matrix

| # | Finding | Severity | Exploitability | Impact | Requires Auth |
|---|---------|----------|---------------|--------|---------------|
| 1 | Path traversal in storage | Critical | Medium (needs key) | File exfiltration | Token forgery |
| 2 | Database race condition | Critical | High (concurrent webhooks) | Data loss | None |
| 3 | Rate limiter bypass | High | Trivial (header spoofing) | Abuse/DoS | None |
| 4 | Unencrypted PII storage | High | Medium (LFI chain) | Data breach | Indirect |
| 5 | Student portal bypass | High | Trivial (devtools) | Content access | None |
| 6 | Missing CSP | Medium | Requires XSS chain | Session hijacking | None |
| 7 | Bearer token for S3 | Medium | Network-level | Bucket compromise | MITM |
| 8 | Webhook double-save race | Medium | Timing-dependent | Lost fulfillment | None |
| 9 | Predictable temp paths | Low | Local access needed | File overwrite | System access |

---

## Priority Remediation Order

1. **Immediate** (pre-launch blockers): Findings 1, 2, 4 — path traversal, race condition, PII storage
2. **Before production traffic**: Findings 3, 6 — rate limiter, CSP
3. **Short-term**: Findings 7, 8 — S3 signing, webhook idempotency
4. **Backlog**: Findings 5, 9 — student portal redesign, temp file hardening
