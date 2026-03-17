import { NextRequest, NextResponse } from "next/server";
import { stripe } from "@/lib/stripe";
import { getSiteUrl } from "@/lib/env";
import { getStorybook, narrators } from "@/lib/storybooks";

const VALID_FORMATS = ["ebook", "audiobook", "bundle"] as const;
type Format = (typeof VALID_FORMATS)[number];

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { slug, format, narratorId } = body;

    // Validate required fields
    if (!slug || !format) {
      return NextResponse.json(
        { error: "Missing slug or format" },
        { status: 400 }
      );
    }

    if (!VALID_FORMATS.includes(format as Format)) {
      return NextResponse.json(
        { error: "Invalid format. Must be ebook, audiobook, or bundle." },
        { status: 400 }
      );
    }

    const book = getStorybook(slug);
    if (!book) {
      return NextResponse.json({ error: "Book not found" }, { status: 404 });
    }

    // Validate narrator exists if provided
    if (narratorId) {
      const validNarrator = narrators.some((n) => n.id === narratorId);
      if (!validNarrator) {
        return NextResponse.json(
          { error: "Invalid narrator selection." },
          { status: 400 }
        );
      }
    }

    const priceMap: Record<string, number> = {
      ebook: book.priceInCents,
      audiobook: book.audiobookPriceInCents,
      bundle: book.bundlePriceInCents,
    };

    const formatLabels: Record<string, string> = {
      ebook: "Digital Storybook (PDF)",
      audiobook: "Narrated Audiobook",
      bundle: "Storybook + Audiobook Bundle",
    };

    const siteUrl = getSiteUrl();

    const session = await stripe.checkout.sessions.create({
      mode: "payment",
      payment_method_types: ["card"],
      line_items: [
        {
          price_data: {
            currency: "usd",
            unit_amount: priceMap[format],
            product_data: {
              name: `${book.title} — ${formatLabels[format]}`,
              description: book.description,
            },
          },
          quantity: 1,
        },
      ],
      metadata: {
        slug: book.slug,
        format,
        narratorId: narratorId || "",
      },
      success_url: `${siteUrl}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${siteUrl}/books/${slug}`,
    });

    return NextResponse.json({ url: session.url });
  } catch (err: unknown) {
    console.error("Checkout error:", err);
    return NextResponse.json(
      { error: "Failed to create checkout session. Please try again." },
      { status: 500 }
    );
  }
}
