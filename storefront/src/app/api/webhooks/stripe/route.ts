import { NextRequest, NextResponse } from "next/server";
import { stripe, STRIPE_WEBHOOK_SECRET, generateDownloadToken } from "@/lib/stripe";
import { getSiteUrl } from "@/lib/env";
import { getStorybook } from "@/lib/storybooks";
import { savePurchase, hasProcessedEvent } from "@/lib/db";
import { sendFulfillmentEmail } from "@/lib/email";

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
      STRIPE_WEBHOOK_SECRET
    );
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : "Webhook verification failed";
    console.error("Webhook signature verification failed:", message);
    return NextResponse.json({ error: message }, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object;

      // Idempotency: skip if we've already processed this session
      if (hasProcessedEvent(session.id)) {
        console.log("Skipping duplicate event for session:", session.id);
        return NextResponse.json({ received: true, duplicate: true });
      }

      const metadata = session.metadata || {};
      const { slug, format, narratorId } = metadata;

      if (!slug || !format) {
        console.error(
          "Missing required metadata in checkout session:",
          session.id,
          metadata
        );
        return NextResponse.json(
          { error: "Missing metadata (slug or format)" },
          { status: 422 }
        );
      }

      const book = getStorybook(slug);
      if (!book) {
        console.error("Book not found for slug:", slug);
        return NextResponse.json(
          { error: `Book not found: ${slug}` },
          { status: 422 }
        );
      }

      const customerEmail = session.customer_details?.email || "";

      // Generate signed download tokens (14-day expiry)
      const tokens: Record<string, string> = {};
      if (format === "ebook" || format === "bundle") {
        tokens.ebook = generateDownloadToken(session.id, slug, "ebook");
      }
      if (format === "audiobook" || format === "bundle") {
        tokens.audiobook = generateDownloadToken(session.id, slug, "audiobook");
      }

      // Build download URLs
      const siteUrl = getSiteUrl();
      const downloadLinks = Object.entries(tokens).map(([fmt, token]) => ({
        format: fmt,
        url: `${siteUrl}/api/download?token=${token}`,
      }));

      // Persist purchase
      savePurchase({
        id: crypto.randomUUID(),
        stripeSessionId: session.id,
        email: customerEmail,
        slug,
        format,
        narratorId: narratorId || "",
        downloadTokens: tokens,
        createdAt: new Date().toISOString(),
        fulfilled: true,
      });

      // Send fulfillment email
      if (customerEmail) {
        await sendFulfillmentEmail({
          to: customerEmail,
          bookTitle: book.title,
          format,
          downloadLinks,
        });
      } else {
        console.warn("No customer email for session:", session.id);
      }

      console.log("Purchase fulfilled:", {
        session: session.id,
        book: book.title,
        format,
        narrator: narratorId || "default",
        email: customerEmail,
      });

      break;
    }

    default:
      // Acknowledge unhandled events without error
      break;
  }

  return NextResponse.json({ received: true });
}
