/**
 * Runtime environment validation.
 * Import this in layout.tsx or any server entry point to fail fast on missing config.
 */

export function validateEnv() {
  const required = [
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
  ];

  const recommended = [
    "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY",
    "NEXT_PUBLIC_SITE_URL",
  ];

  const missing = required.filter((key) => !process.env[key]);
  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missing.join(", ")}. ` +
        "Copy .env.example to .env.local and fill in your values."
    );
  }

  const warnings = recommended.filter((key) => !process.env[key]);
  if (warnings.length > 0) {
    console.warn(
      `[storefront] Missing recommended env vars: ${warnings.join(", ")}. ` +
        "Some features may not work correctly."
    );
  }
}

export function getSiteUrl(): string {
  const url = process.env.NEXT_PUBLIC_SITE_URL;
  if (!url) {
    console.warn(
      "[storefront] NEXT_PUBLIC_SITE_URL not set, falling back to localhost"
    );
    return "http://localhost:3000";
  }
  return url;
}
