import { NextRequest, NextResponse } from "next/server";
import { stripe, generateDownloadToken } from "@/lib/stripe";
import { getStorybook } from "@/lib/storybooks";

export async function POST(request: NextRequest) {
  const body = await request.text();
  const signature = request.headers.get("stripe-signature");

  if (!signature) {
    return NextResponse.json(
      { error: "Missing stripe-signature header" },
      { status: 400 }
    );
  }

  let event;
  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Webhook verification failed";
    console.error("Webhook signature verification failed:", message);
    return NextResponse.json({ error: message }, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object;
      const { slug, format, narratorId } = session.metadata || {};

      if (!slug || !format) {
        console.error("Missing metadata in checkout session:", session.id);
        break;
      }

      const book = getStorybook(slug);
      if (!book) {
        console.error("Book not found for slug:", slug);
        break;
      }

      // Generate signed download tokens
      const purchaseId = session.id;
      const tokens: Record<string, string> = {};

      if (format === "ebook" || format === "bundle") {
        tokens.ebook = generateDownloadToken(purchaseId, slug, "ebook");
      }
      if (format === "audiobook" || format === "bundle") {
        tokens.audiobook = generateDownloadToken(
          purchaseId,
          slug,
          "audiobook"
        );
      }

      // In production: send email with download links, store purchase in DB.
      // For now, log the fulfillment data.
      console.log("=== PURCHASE FULFILLED ===");
      console.log("Session:", purchaseId);
      console.log("Book:", book.title);
      console.log("Format:", format);
      console.log("Narrator:", narratorId || "default");
      console.log("Customer email:", session.customer_details?.email);
      console.log("Download tokens:", tokens);

      // Build download URLs for email
      const siteUrl =
        process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
      const downloadLinks = Object.entries(tokens).map(([fmt, token]) => ({
        format: fmt,
        url: `${siteUrl}/api/download?token=${token}`,
      }));
      console.log("Download links:", downloadLinks);

      break;
    }

    default:
      console.log("Unhandled event type:", event.type);
  }

  return NextResponse.json({ received: true });
}
