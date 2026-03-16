# Storybook Library — Storefront

Stripe-powered children's storybook library with narrated audiobooks.

## Architecture

```
storefront/
├── src/
│   ├── app/                  # Next.js App Router pages
│   │   ├── page.tsx          # Homepage — hero, catalog, narrators
│   │   ├── books/[slug]/     # Book detail with narrator selection & purchase
│   │   ├── success/          # Post-purchase confirmation
│   │   └── api/
│   │       ├── checkout/     # Stripe Checkout session creation
│   │       ├── webhooks/stripe/ # Stripe webhook for fulfillment
│   │       └── download/     # Signed download URL verification
│   ├── components/           # React components
│   │   ├── BookCard.tsx      # Catalog card
│   │   ├── NarratorCard.tsx  # Narrator profile
│   │   ├── NarratorSelector.tsx # Narrator picker on book page
│   │   └── PurchaseButton.tsx   # Stripe checkout trigger
│   └── lib/
│       ├── storybooks.ts     # Book catalog & narrator data
│       └── stripe.ts         # Stripe client & download token signing
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
2. Get your test API keys from the dashboard
3. Set up a webhook endpoint pointing to `/api/webhooks/stripe`
4. Listen for `checkout.session.completed` events

For local development, use the Stripe CLI:
```bash
stripe listen --forward-to localhost:3000/api/webhooks/stripe
```

## Purchase Flow

1. Customer browses catalog on homepage
2. Selects a book → sees detail page with narrator options
3. Clicks purchase → Stripe Checkout session created via API
4. Completes payment on Stripe's hosted page
5. Webhook fires → generates signed download tokens (14-day expiry)
6. Customer redirected to success page with download links

## Content Pipeline

Books are sourced from the parent repo's `projects/` directory. The TTS
production pipeline (`scripts/batch_produce.py`) generates audiobook files
that are stored in cloud storage and served via signed download URLs.

## Next Steps

- [ ] Connect cloud storage (S3/R2) for file hosting
- [ ] Add email delivery via SendGrid/Resend
- [ ] Build admin dashboard for order management
- [ ] Add subscription tier for unlimited library access
- [ ] Expand catalog with new children's stories
