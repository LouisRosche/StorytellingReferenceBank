# Commercial Production Checklist

Complete checklist for producing audiobooks for commercial sale.

---

## Pre-Production

### Rights and Legal

- [ ] **Copyright clear**: You own the text or have production rights
- [ ] **Voice rights documented**: Own voice, licensed voices, or AI-generated
- [ ] **Music/sound effects licensed**: If using any (most audiobooks don't)
- [ ] **ISBN obtained**: Required for most distribution (separate from print ISBN)
- [ ] **Business entity**: Consider LLC for liability and tax purposes

### Technical Setup

**Full setup guide**: `docs/PRODUCTION-SETUP.md` · **Pipeline**: `scripts/batch_produce.py`

- [ ] **TTS model installed**: Higgs V2 or equivalent
- [ ] **Audio processing chain verified**: Post-processing produces ACX-compliant output
- [ ] **Backup system**: Project files backed up (cloud + local)
- [ ] **Version control**: Git repo for manuscript and production files

### Content Preparation

- [ ] **Final manuscript**: No more text edits after production starts
- [ ] **TTS-ready formatting**: Speaker attributions explicit, pronunciation guides complete
- [ ] **Chapter structure**: Clear breaks, front/back matter separated
- [ ] **Pronunciation guide**: All unusual names/terms documented

---

## Production

### Audio Generation

- [ ] **Persona finalized**: Test passages approved before full generation
- [ ] **Multi-speaker map verified**: If applicable, all character voices assigned
- [ ] **Chapter-by-chapter generation**: Don't generate entire book at once
- [ ] **Progress tracking**: Log completed chapters, any issues

### Quality Control (Per Chapter)

- [ ] **Listen completely**: No skimming
- [ ] **Check against text**: Words match, nothing hallucinated
- [ ] **Note problems**: Mispronunciations, artifacts, pacing issues
- [ ] **Re-generate problem sections**: Don't ship known issues

### Post-Processing

- [ ] **Noise reduction**: Background noise below -60 dB
- [ ] **Normalization**: RMS between -23 dB and -18 dB
- [ ] **Peak limiting**: No peaks above -3 dB
- [ ] **Room tone**: 0.5-1 second head, 1-5 seconds tail
- [ ] **Format conversion**: MP3 192 kbps CBR, 44.1 kHz, mono

---

## ACX/Audible Specific

**Full technical specs**: `@audiobook-specs/acx-requirements.md`

**Validation**: `scripts/acx_validator.py`

### File Requirements

- [ ] **Opening credits**: Separate file, spoken (title, author, narrator)
- [ ] **Closing credits**: Separate file, spoken (copyright, production info)
- [ ] **Chapter files**: Named sequentially (Chapter_01.mp3, etc.)
- [ ] **Retail sample**: 1-5 minute sample for preview

### Content Requirements

- [ ] **Consistent narrator**: Same voice throughout (or documented multi-narrator)
- [ ] **No long silences**: Max 3 seconds
- [ ] **No extraneous sounds**: No mouth clicks, breaths, room noise
- [ ] **Correct pronunciation**: Names, places verified

### Common Rejection Reasons

| Reason | Prevention |
|--------|------------|
| RMS out of range | Use ACX validator before upload |
| Inconsistent volume | Chapter-level normalization |
| Room noise/echo | Clean source, noise reduction |
| Mouth clicks | De-clicking in post-processing |
| Mispronunciations | Pronunciation guide, QC listen |
| Missing opening/closing | Checklist compliance |

---

## Self-Publishing Platforms

### Comparison

| Platform | Revenue Share | DRM | Notes |
|----------|---------------|-----|-------|
| **ACX/Audible** | 25-40% | Required | Largest market, exclusive options |
| **Findaway Voices** | 80% | Optional | Wide distribution, no exclusivity |
| **Author's Republic** | 70% | Optional | Direct to 50+ retailers |
| **Google Play Books** | 52% | Optional | Direct upload option |
| **Kobo** | 45% | Optional | Growing platform |
| **Direct (your site)** | ~97% (minus Stripe) | None | Full control, build audience |

### Recommendation for Monetization

**Hybrid approach:**
1. **Direct sales** (your site via Stripe): Highest margin, own customer relationship
2. **Wide distribution** (Findaway): Reach all platforms without exclusivity
3. **Avoid ACX exclusivity** unless you need their marketing

---

## Direct Sales Setup

### Technical Stack

```
Your Website (GitHub Pages / Vercel / Netlify)
├── Landing page (marketing)
├── Product pages (individual audiobooks)
├── Checkout (Stripe)
└── Delivery (SendOwl / Gumroad / custom)

Audio Hosting
├── Cloudflare R2 (cheap, fast)
├── Backblaze B2 (cheap)
└── AWS S3 (reliable, more expensive)
```

### Stripe Integration

```javascript
// Simple Stripe Checkout integration
const stripe = Stripe('pk_live_xxx');

document.getElementById('buy-button').addEventListener('click', async () => {
  const { error } = await stripe.redirectToCheckout({
    lineItems: [{ price: 'price_xxx', quantity: 1 }],
    mode: 'payment',
    successUrl: 'https://yoursite.com/success',
    cancelUrl: 'https://yoursite.com/cancel',
  });
});
```

### Subscription Model

For a catalog of audiobooks:

| Tier | Price | Access | Platform |
|------|-------|--------|----------|
| Per-book | $9.99-24.99 | Single book, lifetime | Stripe one-time |
| Subscription | $9.99/month | Full catalog | Stripe recurring |
| Membership | $99/year | Full catalog + early access | Stripe recurring |

---

## Metadata and Marketing

### Required Metadata

- [ ] **Title**: Exact match to book
- [ ] **Author**: As appears on book
- [ ] **Narrator**: Your name or "AI Narration" (platform dependent)
- [ ] **Runtime**: Total duration (calculate after production)
- [ ] **Description**: Marketing copy, 150-300 words
- [ ] **Categories**: BISAC codes / platform categories
- [ ] **Keywords**: 7 relevant search terms
- [ ] **Cover**: 2400x2400 minimum (square for audio)

### AI Narration Disclosure

Some platforms require/recommend disclosure that narration is AI-generated. Current approaches:

- **Audible/ACX**: "Virtual Voice" program has specific requirements
- **Others**: "Narrated using AI voice technology" in credits
- **Direct sales**: Your choice, recommend transparency

### Sample Quality

Your retail sample sells the book. Ensure it:
- [ ] Hooks immediately (don't start with "Chapter One...")
- [ ] Demonstrates voice quality
- [ ] Represents the book's tone
- [ ] Is 1-5 minutes (3 minutes optimal)
- [ ] Ends at a compelling moment

---

## Financial Tracking

### Per-Project Budget Template

| Category | Estimated | Actual |
|----------|-----------|--------|
| TTS compute (electricity) | $X | |
| ISBN | $125 (or bulk rate) | |
| Cover design | $0-500 | |
| Marketing | $X | |
| Platform fees | % of sales | |
| **Total investment** | | |

### Revenue Tracking

```
projects/
└── project-name/
    └── business/
        ├── budget.csv
        ├── sales-log.csv
        └── royalty-statements/
```

### Break-Even Calculation

```
Break-even units = Total investment / (Price × Your share)

Example:
- Investment: $200 (ISBN + cover)
- Price: $14.99
- Your share: 70% (Findaway)
- Break-even: $200 / ($14.99 × 0.70) = 19 copies
```

---

## Launch Checklist

### Week Before

- [ ] Final QC listen complete
- [ ] All files uploaded to platform(s)
- [ ] Metadata complete and verified
- [ ] Cover finalized
- [ ] Sample created and uploaded
- [ ] Landing page live
- [ ] Email list notified (if applicable)

### Launch Day

- [ ] Verify live on all platforms
- [ ] Social media announcement
- [ ] Email announcement
- [ ] Check purchase flow works
- [ ] Monitor for issues

### Post-Launch

- [ ] Track sales daily (first week)
- [ ] Respond to any reviews
- [ ] Adjust marketing based on data
- [ ] Plan next release

---

## Archive Structure

For each completed project:

```
projects/
└── project-name/
    ├── drafts/                    # Manuscript versions
    ├── story-bible/               # Characters, world
    ├── personas/                  # Voice configurations
    ├── production/
    │   ├── raw/                   # TTS output
    │   ├── processed/             # Post-processed
    │   └── final/                 # Release files
    ├── marketing/
    │   ├── cover/
    │   ├── sample/
    │   └── copy/
    ├── business/
    │   ├── contracts/
    │   ├── budget.csv
    │   └── sales/
    └── README.md                  # Project summary
```
