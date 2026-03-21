import { NextRequest, NextResponse } from "next/server";
import { rateLimit } from "@/lib/rate-limit";

/** Rate limit config per route prefix. */
const ROUTE_LIMITS: Record<string, { maxTokens: number; refillRate: number }> = {
  "/api/checkout": { maxTokens: 5, refillRate: 0.5 },   // 5 burst, 1 per 2s
  "/api/download": { maxTokens: 10, refillRate: 1 },    // 10 burst, 1 per s
};

function getClientIp(request: NextRequest): string {
  return (
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    request.headers.get("x-real-ip") ||
    "unknown"
  );
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Find matching rate limit config
  const matchedPrefix = Object.keys(ROUTE_LIMITS).find((prefix) =>
    pathname.startsWith(prefix)
  );

  if (!matchedPrefix) {
    return NextResponse.next();
  }

  const ip = getClientIp(request);
  const key = `${matchedPrefix}:${ip}`;
  const config = ROUTE_LIMITS[matchedPrefix];
  const { allowed, retryAfterSeconds } = rateLimit(key, config);

  if (!allowed) {
    return NextResponse.json(
      { error: "Too many requests. Please try again later." },
      {
        status: 429,
        headers: { "Retry-After": retryAfterSeconds.toString() },
      }
    );
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/api/checkout/:path*", "/api/download/:path*"],
};
