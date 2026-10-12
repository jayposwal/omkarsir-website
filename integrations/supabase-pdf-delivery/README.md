# Secure PDF delivery — Razorpay + Supabase Edge Functions + Resend

This implementation is designed for the existing Omkar Sir static website. It does not become active just because these files are committed. The Supabase project, private PDF bucket, secrets, sender domain, Razorpay webhook, and test payment must be configured before using it with real customers.

## What this does

1. Razorpay sends a \`payment.captured\` webhook to the Edge Function.
2. The function validates \`X-Razorpay-Signature\` using HMAC-SHA256 over the exact raw request body before parsing the payload.
3. It accepts only a captured INR payment with the configured price **and** a product-description match.
4. The payment ID is stored as a unique key. Duplicate webhook events do not create a new entitlement or a different token.
5. A cryptographically signed, buyer-specific download URL is sent to the email captured by Razorpay. It expires after 7 days by default and is limited to 5 downloads by default.
6. The URL can download only the matching file from a private Supabase Storage bucket. Altered, expired, refunded, or over-limit links fail.
7. Email is sent through Resend. The payment ID is used as Resend's idempotency key, so webhook retries are safer.
8. The \`refund.processed\` event changes an existing entitlement to \`refunded\` and disables future downloads.

**A private, time-limited link is a bearer link while it is valid.** A buyer can forward it to another person before expiry. Expiry, private storage, and a download cap reduce exposure but cannot make forwarding impossible. The link is not a permanent account-bound login.

## Files

- \`supabase/functions/razorpay-pdf-webhook/index.ts\`: verified webhook, product matching, delivery record and email.
- \`supabase/functions/pdf-download/index.ts\`: validates the token and streams a file from private Storage.
- \`supabase/functions/_shared/pdf-delivery.ts\`: product allow-list, HMAC/token and email helpers.
- \`supabase/migrations/20261012000000_secure_pdf_delivery.sql\`: database table, private bucket and atomic RPC functions.
- \`supabase/config.toml\`: allows the two public endpoints to be called without a Supabase user JWT; the webhook signature/token validation are the authentication boundary.

## Before deployment

### 1. Create or select your Supabase project

Create a project in the Supabase Dashboard if you do not already have one. Copy the project reference from its URL. Keep the project secret/service-role key server-side only.

From the repository root, link the CLI to your project:

    npx supabase login
    npx supabase link --project-ref YOUR_PROJECT_REF

### 2. Create the table and private bucket

Apply the migration:

    npx supabase db push

The migration creates a private bucket named \`private-pdfs\`. Confirm it is **Private**, not Public, in Storage settings. Upload each purchased PDF with the exact object key:

| Product | Private bucket object key |
|---|---|
| RAS Mains Paper-II PDF | \`ras-mains-paper-2-pdf.pdf\` |
| सम्पूर्ण आधुनिक भारत का इतिहास PDF | \`adhunik-bharat-itihas.pdf\` |

Upload only the final original PDFs you want to sell. These files must not be served from a public Drive link or public storage bucket. Set the old Google Drive file-sharing permission to **Restricted** after verifying the new delivery is working.

### 3. Configure Resend email

Create a Resend account and verify a sender domain you control. Use a sender address on that verified domain (not the Resend demo sender) for live orders.

The function sends mail to the email address in the Razorpay payment entity. In the Payment Button's checkout settings, make the buyer email field required. If Razorpay has no valid email, the function will not issue a link.

### 4. Set server-side secrets

Create a new, unique secret for download tokens:

    openssl rand -hex 32

In the Supabase Dashboard → Edge Functions → Secrets, add these values (never commit the values to Git):

- \`RAZORPAY_WEBHOOK_SECRET\`: a new webhook secret you create in Razorpay Webhooks settings.
- \`PDF_DOWNLOAD_TOKEN_SECRET\`: the random value generated above (at least 32 characters).
- \`RESEND_API_KEY\`: your Resend API key.
- \`RESEND_FROM_EMAIL\`: e.g. \`New India Education <pdf@YOUR-VERIFIED-DOMAIN>\`.
- \`PDF_DOWNLOAD_BASE_URL\`: exactly \`https://YOUR_PROJECT_REF.supabase.co/functions/v1/pdf-download?token=\`.
- \`PDF_DOWNLOAD_TTL_SECONDS\`: optional; default \`604800\` (7 days), maximum supported is 30 days.
- \`PDF_MAX_DOWNLOADS\`: optional; default \`5\`, maximum supported is 25.

Supabase provides \`SUPABASE_URL\` and a server-side key to Edge Functions. The code reads the legacy \`SUPABASE_SERVICE_ROLE_KEY\` where available and falls back to the default key in \`SUPABASE_SECRET_KEYS\`. Do not put any Supabase service key in website HTML or email.

### 5. Check the product allow-list against real Razorpay payloads

The product name must match the payment's captured \`description\` as well as its exact amount:

- RAS Paper-II: INR ₹49 (4900 paise), description containing \`RAS Mains Paper-II\`, \`RAS Mains Paper II\`, or \`RAS Mains Paper-2\`.
- Modern Indian History: INR ₹9 or ₹99, description containing \`Adhunik Itihas\`, \`Modern Indian History\`, or \`सम्पूर्ण आधुनिक भारत का इतिहास\`.

These matchers are intentionally fail-closed. If Razorpay emits a different description for the payment button, no email will be sent until you inspect the signed webhook sample and update \`descriptionIncludes\` in \`supabase/functions/_shared/pdf-delivery.ts\`. Do not remove description matching or rely on amount alone.

The current website button IDs include:

- RAS Mains Paper-II: \`pl_TmyJkDLHXDE2N3\`
- Modern History: \`pl_Tmzqpr6RIRGU0K\`

Check the actual configured price and title/description in Razorpay Dashboard. The source code cannot see or change Payment Button dashboard settings.

### 6. Deploy the Edge Functions

From the repository root:

    npx supabase functions deploy razorpay-pdf-webhook --no-verify-jwt
    npx supabase functions deploy pdf-download --no-verify-jwt

JWT verification is disabled for these endpoints because Razorpay and buyers do not log in to Supabase. The webhook endpoint authenticates Razorpay with the webhook HMAC signature; the download endpoint authenticates access with the signed expiring token and the database entitlement. Do not use these functions as a general public database API.

### 7. Configure the Razorpay webhook

In Razorpay Dashboard → Account & Settings → Webhooks, add:

- URL: \`https://YOUR_PROJECT_REF.supabase.co/functions/v1/razorpay-pdf-webhook\`
- Secret: the exact same value stored as \`RAZORPAY_WEBHOOK_SECRET\`
- Events: \`payment.captured\` and \`refund.processed\`

Do not use the customer-facing return/redirect page as proof of payment. The webhook is the source of truth for delivery.

If an older Cloudflare Worker webhook is already configured for these products, do not leave two active webhooks sending the same PDF emails unless that duplication is intentional. Disable the old delivery webhook after the Supabase test succeeds.

### 8. Keep the post-payment page safe

Razorpay Payment Button redirects are configured in its Dashboard, not in HTML. Keep the current return URL if desired, but it must be an informational page only. It must not display a public Drive URL. The repository's RAS return page is updated to tell buyers to check their email instead of exposing the PDF.

### 9. Test before live use

Use Razorpay test mode first. Check all of these:

- Correct signed test webhook creates one delivery record for the right product and amount.
- The email goes to the email entered at checkout and the button downloads the matching PDF.
- Invalid/missing webhook signatures produce HTTP 401 and no delivery record.
- Failed/uncaptured or unrelated payments produce no email.
- Replaying a captured event does not send repeated mail or create a new token.
- A token with one character changed fails; expired tokens fail; after 5 downloads (default) more attempts fail.
- A processed refund disables the existing link.
- RAS and History downloads serve files from the private bucket; public Drive links and public Storage URLs are not present.
- If the email provider is temporarily unavailable, Razorpay receives a non-2xx response and can retry the webhook.

Only after test mode passes should you configure the live webhook secret and run a small live payment/refund.

## Current activation status

These are source files and deployment instructions only. This repository integration cannot deploy to your Supabase account, verify a sender domain, upload your private PDFs, or create the Razorpay webhook without authorized dashboard access. **Do not announce automatic delivery as active until the required dashboard setup and the tests above are complete.**
