# Storybook Library — Storefront

Stripe-powered children's storybook library with narrated audiobooks.

## Architecture

```
storefront/
├── src/
│   ├── app/                     # Next.js App Router
│   │   ├── page.tsx             # Homepage — hero, catalog, narrators
│   │   ├── books/[slug]/        # Book detail with narrator selection & purchase
│   │   ├── success/             # Post-purchase confirmation
│   │   └── api/
│   │       ├── checkout/        # Stripe Checkout session creation
│   │       ├── webhooks/stripe/ # Webhook: fulfillment, persistence, email
│   │       └── download/        # Signed download — streams from storage
│   ├── components/
│   │   ├── BookCard.tsx         # Catalog card with SVG cover
│   │   ├── NarratorCard.tsx     # Narrator profile
│   │   ├── NarratorSelector.tsx # Narrator picker (ARIA radiogroup)
│   │   ├── AudioPreview.tsx     # Narrator voice sample player
│   │   └── PurchaseButton.tsx   # Stripe checkout trigger
│   └── lib/
│       ├── storybooks.ts        # Book catalog & narrator data
│       ├── stripe.ts            # Stripe client, HMAC token signing (timing-safe)
│       ├── db.ts                # JSON file purchase database
│       ├── email.ts             # Fulfillment email (Resend or console)
│       ├── storage.ts           # Content delivery (local FS or S3/R2)
│       └── env.ts               # Runtime environment validation
├── public/
│   ├── covers/                  # SVG cover art for each book
│   └── samples/                 # Narrator audio preview samples
├── content/                     # Local file storage (gitignored)
│   └── {slug}/                  # ebook.pdf, audiobook.mp3 per book
└── data/                        # Purchase database (gitignored)
```

## Setup

```bash
cd storefront
cp .env.example .env.local   # Add your Stripe keys
npm install
npm run dev                   # http://localhost:3000
```

## Stripe Configuration

1. Create a [Stripe account](https://dashboard.stripe.com)
2. Get API keys from the dashboard
3. Install the [Stripe CLI](https://stripe.com/docs/stripe-cli)
4. Forward webhooks locally:
   ```bash
   stripe listen --forward-to localhost:3000/api/webhooks/stripe
   ```
5. Copy the webhook signing secret to `.env.local`

## Purchase Flow

1. Customer browses catalog, selects a book
2. Picks a narrator, previews audio sample
3. Clicks purchase → Stripe Checkout session created (dynamic pricing)
4. Completes payment on Stripe's hosted page
5. Webhook fires → purchase saved to DB, download tokens generated (HMAC-SHA256, 14-day expiry)
6. Fulfillment email sent via Resend (or logged to console in dev)
7. Customer clicks download link → file streamed from storage

## Content Pipeline

1. Write manuscript in `projects/{name}/drafts/`
2. Configure personas in `projects/{name}/personas/`
3. Generate audiobook: `python scripts/batch_produce.py`
4. Place output in `storefront/content/{slug}/audiobook.mp3`
5. Create ebook PDF → `storefront/content/{slug}/ebook.pdf`

## Security

- HMAC tokens use `crypto.timingSafeEqual()` to prevent timing attacks
- No fallback secrets — app crashes on missing env vars (fail-fast)
- Webhook signature verification via Stripe SDK
- Idempotent webhook processing (duplicate events skipped)
- Signed download URLs expire after 14 days
- Purchase database provides audit trail
