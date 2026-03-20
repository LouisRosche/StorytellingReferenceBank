import { NextRequest, NextResponse } from "next/server";
import { verifyDownloadToken } from "@/lib/stripe";
import { getContentFile } from "@/lib/storage";
import { getStorybook } from "@/lib/storybooks";

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
      {
        error:
          "Invalid or expired download link. Contact support for a new link.",
      },
      { status: 403 }
    );
  }

  const { slug, format } = verified;

  const validFormats = ["ebook", "audiobook"];
  if (!validFormats.includes(format)) {
    return NextResponse.json(
      { error: "Invalid format in download token" },
      { status: 400 }
    );
  }

  const book = getStorybook(slug);
  if (!book) {
    return NextResponse.json({ error: "Book not found" }, { status: 404 });
  }

  // Fetch the actual file from storage
  const file = await getContentFile(slug, format);

  if (!file) {
    // File not yet available — give the customer useful information
    return NextResponse.json(
      {
        error: "File not yet available",
        message:
          `Your purchase of "${book.title}" (${format}) is confirmed, ` +
          "but the file is still being prepared. Please try again in a few minutes, " +
          "or contact support if the issue persists.",
        slug,
        format,
      },
      { status: 202 }
    );
  }

  // Stream the file with proper headers
  const body = new Uint8Array(file.buffer);
  return new NextResponse(body, {
    status: 200,
    headers: {
      "Content-Type": file.contentType,
      "Content-Disposition": `attachment; filename="${file.filename}"`,
      "Content-Length": file.buffer.length.toString(),
      "Cache-Control": "private, no-cache",
    },
  });
}
