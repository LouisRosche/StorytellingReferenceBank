import { NextRequest, NextResponse } from "next/server";
import { verifyDownloadToken } from "@/lib/stripe";

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get("token");

  if (!token) {
    return NextResponse.json(
      { error: "Missing download token" },
      { status: 400 }
    );
  }

  const verified = verifyDownloadToken(token);
  if (!verified) {
    return NextResponse.json(
      { error: "Invalid or expired download link. Contact support for a new link." },
      { status: 403 }
    );
  }

  const { slug, format } = verified;

  // In production: stream the file from S3/cloud storage.
  // For now: return a placeholder response showing the link is valid.
  return NextResponse.json({
    message: "Download verified",
    slug,
    format,
    note: "In production, this endpoint streams the purchased file from cloud storage. " +
          "Connect to S3 or similar to serve actual ebook PDFs and audiobook MP3s.",
  });
}
