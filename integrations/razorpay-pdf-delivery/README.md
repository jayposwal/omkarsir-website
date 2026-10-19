# Paid PDF email delivery (Razorpay + Cloudflare Worker + Gmail)

Delivery for all four paid PDFs: Modern Indian History, Rajasthan History, RAS Mains Paper-II PYQ and Rajasthan Economic Survey 2025-26. Each product stays switched off until its private R2 file and Razorpay description are configured.

After payment the buyer gets the PDF two ways:
- **Website:** Razorpay redirects to `/download-<product>.html?razorpay_payment_id=…`. That page (`/pdf-delivery.js`) calls the Worker's `/verify`, which checks the payment with the Razorpay API and only then returns a signed, time-limited download link. Payments older than `VERIFY_FRESH_MINUTES` must also give the checkout email, so a leaked Payment ID alone is not enough.
- **Email:** the `payment.captured` webhook (below) sends the same kind of link by Gmail. It does not activate itself when committed: the owner must create the R2 bucket, upload the private PDF, authorize Google Apps Script, configure secrets and create the Razorpay webhook from the authenticated dashboards.

## Why a Worker is used before Apps Script

Razorpay signs the raw webhook payload in the `x-razorpay-signature` header. Apps Script web-app events document the request body and URL parameters, but do not expose arbitrary HTTP headers. The Cloudflare Worker therefore verifies the Razorpay HMAC signature before forwarding the verified payment to Apps Script. Do not set up a public Apps Script endpoint that emails download links based only on an unverified JSON payload.

## Architecture

1. Razorpay sends `payment.captured` to `/webhook`.
2. Worker verifies `x-razorpay-signature` with the webhook secret against the exact raw body.
3. Worker allows only captured INR payments whose amount and product-specific `payment.description` match the configured allow-list: Modern Indian History ₹9/₹99, or Rajasthan History ₹49.
4. Worker creates a time-limited HMAC-signed download token.
5. Worker forwards the verified purchase to the Google Apps Script emailer using a separate random shared secret.
6. Apps Script uses Gmail to send the HTML email with the prominent **⬇️ PDF Download करें** button. A Google Sheet log deduplicates duplicate webhooks by Payment ID.
7. `/verify` (website): Worker fetches the payment from `api.razorpay.com` with the key ID/secret, checks captured + INR + amount + product description, and returns a signed link.
8. Download URLs are handled by the Worker. The Worker validates token signature and expiry, then streams the matching PDF object from a private Cloudflare R2 bucket (`adhunik-bharat-itihas.pdf` or `rajasthan-history.pdf`); no public Google Drive source link is exposed.

## Files

- `worker.js`: signature verification, product filtering, signed-link generation, protected R2 downloads.
- `Code.gs`: Gmail HTML emailer and idempotency log.
- `wrangler.example.toml`: sample Worker/R2 configuration.
- `test/worker.test.mjs`: offline tests (Razorpay, R2 and Apps Script mocked).
- `/pdf-delivery.js` + `/download-*.html` (site root): the website side of `/verify`.

## Deployment checklist

### A. Private PDF storage

1. In the Cloudflare dashboard, create a private R2 bucket. Do not enable public access.
2. Upload the Modern History PDF as `adhunik-bharat-itihas.pdf` and the Rajasthan History 234-page PDF as `rajasthan-history.pdf`. Keep both objects private.
3. Keep the original Drive file private if it is no longer needed. The worker must deliver the private R2 object, not redirect to a public Drive URL.

### B. Google Apps Script

1. Visit https://script.google.com and create a standalone project named `Omkar Sir PDF Emailer`.
2. Paste `Code.gs` from this folder.
3. Select `setup` and click Run. Approve Google permission prompts. This creates a delivery-log spreadsheet and generates `INTERNAL_SHARED_SECRET`; copy the value from the execution log and store it as a Worker secret. Treat it like a password.
4. Once the Worker URL is known, open Project Settings → Script Properties and add `DOWNLOAD_BASE_URL` with the exact prefix, e.g. `https://YOUR-WORKER-DOMAIN/download?token=`.
5. Deploy → New deployment → Web app. Execute as **Me**. Set access to **Anyone** so the Worker can call it. Copy the `/exec` URL and set it as Worker secret `APPS_SCRIPT_URL`.
6. Keep the generated `INTERNAL_SHARED_SECRET` private. It authenticates calls from the Worker; do not add it to website HTML, a public repo, or a public query string.

### C. Deploy Cloudflare Worker

1. Install Wrangler and authenticate with the Cloudflare account.
2. Copy `wrangler.example.toml` to `wrangler.toml`, replace the R2 bucket name, then replace `PUBLIC_DOWNLOAD_BASE` with the final Worker URL prefix.
3. Set server-side secrets (Wrangler prompts for their values):
   - `RAZORPAY_WEBHOOK_SECRET`: a new secret created in Razorpay Webhooks settings; use the same value here.
   - `DOWNLOAD_SIGNING_SECRET`: a new random secret, different from the webhook secret.
   - `INTERNAL_SHARED_SECRET`: the value created by Apps Script `setup()`.
   - `APPS_SCRIPT_URL`: the deployed Apps Script `/exec` URL.
   - `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`: Razorpay Dashboard → Account & Settings → API Keys. Needed by `/verify`. Never put them in website HTML or this repo.
4. Deploy the Worker. Example CLI flow:

```bash
npx wrangler login
npx wrangler secret put RAZORPAY_WEBHOOK_SECRET
npx wrangler secret put DOWNLOAD_SIGNING_SECRET
npx wrangler secret put INTERNAL_SHARED_SECRET
npx wrangler secret put APPS_SCRIPT_URL
npx wrangler secret put RAZORPAY_KEY_ID
npx wrangler secret put RAZORPAY_KEY_SECRET
npx wrangler deploy --config wrangler.toml
```

5. After deployment, confirm that `PUBLIC_DOWNLOAD_BASE` and Apps Script `DOWNLOAD_BASE_URL` are identical prefixes and include `/download?token=`.
6. Confirm the R2 binding `PDF_BUCKET` is configured and `PDF_OBJECT_KEY` matches the uploaded file.

### C2. Connect the website

1. In `/pdf-delivery.js` set `WORKER_BASE` to the Worker origin (e.g. `https://omkarsir-pdf-delivery.<account>.workers.dev`) and commit. Until then the download pages show WhatsApp/email help with the buyer's Payment ID instead of a link.
2. In Razorpay Dashboard → Payment Buttons → each button → Edit → "After payment" redirect URL:
   - Modern History → `https://omkarsir.com/download-adhunik-bharat-itihas.html`
   - Rajasthan History → `https://omkarsir.com/download-rajasthan-history.html`
   - RAS Mains Paper-II → `https://omkarsir.com/download-ras-mains-paper-2-pdf.html`
   - Economic Survey → `https://omkarsir.com/download-rajasthan-arthvyavastha.html`
3. Make each button collect the buyer's **email and phone**.

### D. Razorpay webhook

1. Razorpay Dashboard → Account & Settings/Webhooks (wording can vary) → Add New Webhook.
2. URL: `https://YOUR-WORKER-DOMAIN/webhook`.
3. Enter the same newly generated webhook secret as Worker secret `RAZORPAY_WEBHOOK_SECRET`.
4. Subscribe to `payment.captured`; save.
5. Do not send the webhook to Apps Script directly: it cannot verify Razorpay's signature header.

### E. Match the correct product

The worker intentionally sends no email unless amount and product description match a product allow-list.
- Modern History: ₹9/₹49/₹99 and `ALLOWED_PAYMENT_DESCRIPTIONS`.
- Rajasthan History: ₹49 and `RAJASTHAN_HISTORY_PAYMENT_DESCRIPTIONS`.
- RAS Mains Paper-II: ₹49 and `RAS_MAINS_P2_PAYMENT_DESCRIPTIONS`.
- Economic Survey: ₹49 and `ECONOMIC_SURVEY_PAYMENT_DESCRIPTIONS` (needs its own Payment Button first).

Run the offline test suite after any change: `node integrations/razorpay-pdf-delivery/test/worker.test.mjs`.

Create a separate ₹49 Razorpay Payment Button for Rajasthan History and insert its actual ID in `rajasthan-history-pdf.html`. Then make a test purchase, inspect the verified webhook/payment description, and set `RAJASTHAN_HISTORY_PAYMENT_DESCRIPTIONS` to the exact observed text. It is deliberately empty by default, so the new product fails closed until verified. Never reuse another product's button ID or remove the description match.

### F. Test before advertising

- Make one small real purchase on each button and refund it after testing.
- Confirm the email arrives at the entered checkout email and the button downloads the PDF.
- Confirm unrelated payments, wrong amounts, and products with non-matching descriptions do not trigger a PDF email.
- Confirm the Rajasthan History ₹49 button serves the Rajasthan PDF, not the Modern History PDF.
- Replay the same webhook and confirm duplicate email is not sent.
- Alter the token, expire it, and visit the download route without a token; all must fail.
- Confirm there is no public R2 bucket URL and that the old Google Drive file is not publicly shareable.
- Monitor Apps Script execution logs and the delivery log sheet.

## Important limitations and dashboard-only work

- Razorpay's payment-button internal title cannot be changed from this repository. Log in to Razorpay Dashboard → Payment Button → open each button → Options → Edit Button, set the title to the agreed Hindi title, and save. Also inspect Button Settings / Payment Receipts so the receipt/reference text is correct. Confirm with a new test receipt because a button's internal title and customer-facing payment description may be different fields.
- Known button IDs from the site:
  - ₹9 offer: `pl_Tmq7zsNHeZibZd`
  - ₹99 price: `pl_Tmp3twDKIS6bn4`
  - ₹49 Rajasthan History button: create a new button; its ID is not available until you create it.
- Do not paste Razorpay keys, webhook secrets, Gmail passwords, or tokens into this repository or this chat.
- This flow secures the downloaded PDF via a time-limited token and private R2 bucket. The token is a bearer link until expiry; purchasers can forward it, so keep the expiry finite and use watermarking/entitlement controls if stronger anti-sharing is required.
