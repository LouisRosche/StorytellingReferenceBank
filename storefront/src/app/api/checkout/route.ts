import { NextRequest, NextResponse } from "next/server";
import { stripe } from "@/lib/stripe";
import { getStorybook } from "@/lib/storybooks";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { slug, format, narratorId } = body;

    if (!slug || !format) {
      return NextResponse.json(
        { error: "Missing slug or format" },
        { status: 400 }
      );
    }

    const book = getStorybook(slug);
    if (!book) {
      return NextResponse.json({ error: "Book not found" }, { status: 404 });
    }

    const priceMap: Record<string, number> = {
      ebook: book.priceInCents,
      audiobook: book.audiobookPriceInCents,
      bundle: book.bundlePriceInCents,
    };

    const price = priceMap[format];
    if (!price) {
      return NextResponse.json({ error: "Invalid format" }, { status: 400 });
    }

    const formatLabels: Record<string, string> = {
      ebook: "Digital Storybook (PDF)",
      audiobook: "Narrated Audiobook",
      bundle: "Storybook + Audiobook Bundle",
    };

    const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

    const session = await stripe.checkout.sessions.create({
      mode: "payment",
      payment_method_types: ["card"],
      line_items: [
        {
          price_data: {
            currency: "usd",
            unit_amount: price,
            product_data: {
              name: `${book.title} — ${formatLabels[format]}`,
              description: book.description,
              metadata: {
                slug: book.slug,
                format,
                narratorId: narratorId || "",
              },
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
    const message = err instanceof Error ? err.message : "Internal server error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
