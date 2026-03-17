import { getSiteUrl } from "./env";

/**
 * Email delivery for purchase fulfillment.
 *
 * Supports two modes:
 * 1. Resend API (production) — set RESEND_API_KEY in .env.local
 * 2. Console logging (development) — prints email content to stdout
 */

interface DownloadLink {
  format: string;
  url: string;
}

interface FulfillmentEmail {
  to: string;
  bookTitle: string;
  format: string;
  downloadLinks: DownloadLink[];
}

export async function sendFulfillmentEmail(
  email: FulfillmentEmail
): Promise<boolean> {
  const resendKey = process.env.RESEND_API_KEY;

  const body = buildEmailBody(email);

  if (resendKey) {
    return sendViaResend(resendKey, email.to, email.bookTitle, body);
  }

  // Development fallback: log to console
  console.log("\n========== FULFILLMENT EMAIL ==========");
  console.log(`To: ${email.to}`);
  console.log(`Subject: Your copy of "${email.bookTitle}" is ready!`);
  console.log("Body:");
  console.log(body);
  console.log("========================================\n");
  return true;
}

function buildEmailBody(email: FulfillmentEmail): string {
  const links = email.downloadLinks
    .map((l) => `  ${l.format.toUpperCase()}: ${l.url}`)
    .join("\n");

  return `Hi there!

Thank you for purchasing "${email.bookTitle}"!

Your download links are ready (valid for 14 days):

${links}

If you have any trouble downloading, reply to this email and we'll help you out.

Happy reading!
— The Storybook Library Team`;
}

async function sendViaResend(
  apiKey: string,
  to: string,
  bookTitle: string,
  body: string
): Promise<boolean> {
  try {
    const fromEmail =
      process.env.RESEND_FROM_EMAIL || "orders@storybooklibrary.com";
    const response = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: `Storybook Library <${fromEmail}>`,
        to: [to],
        subject: `Your copy of "${bookTitle}" is ready!`,
        text: body,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      console.error("Resend API error:", err);
      return false;
    }

    return true;
  } catch (err) {
    console.error("Failed to send email via Resend:", err);
    return false;
  }
}
