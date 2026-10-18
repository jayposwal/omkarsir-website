# Automated paid-PDF delivery: implementation blueprint

Product page: `/adhunik-bharat-itihas-pdf.html`  
Current static delivery page: `/download-adhunik-bharat-itihas.html`

## Goal

After a **verified** Razorpay payment, every buyer gets the same order through three routes:

1. A protected download page opens immediately.
2. A receipt plus protected download link arrives by email.
3. A WhatsApp utility message delivers the receipt and a protected PDF/download link.

## Important security rule

Do not use the public Google Drive URL currently present in the static delivery page as the access-control mechanism. A static `?payment_id=` query parameter is not payment proof. Keep the paid PDF private and issue a short-lived link only after the server verifies a Razorpay event.

## Production flow

```
Razorpay payment captured
        │
        ▼
POST /webhooks/razorpay (server)
  • verify webhook HMAC signature
  • check payment status, ₹49 amount, INR, product ID
  • de-duplicate payment ID
  • save order + buyer email/phone
        │
   ┌────┴────────┐
   ▼             ▼
Email           WhatsApp utility template
receipt +       receipt + document / secure link
secure link
   │
   └──► browser success page → GET /orders/:paymentId/download
                                  • verifies paid entitlement
                                  • creates one-time / short-lived signed URL
                                  • downloads from private object storage
```

## Recommended stack

- **Server:** Cloudflare Worker (or a serverless function on an existing trusted host).
- **Private file:** Cloudflare R2 / S3. Never place the complete paid PDF in GitHub Pages or a public Drive URL.
- **Orders and de-duplication:** D1, Postgres, or another server-side database.
- **Email:** Resend, Postmark, or an authenticated transactional-mail provider.
- **WhatsApp:** Meta WhatsApp Cloud API with an approved **utility** template that contains the order/receipt details and a document header or a protected download button.
- **Payments:** Razorpay webhook. Use a real server-side webhook secret only; never put it into HTML, GitHub, browser JavaScript, or a query string.

## Razorpay dashboard setup

1. Configure the webhook endpoint at the server URL, separately for Test and Live mode.
2. Subscribe to the relevant successful-payment event for the live payment-button/payment-link configuration (normally `payment.captured`; use the exact event confirmed by the Razorpay integration).
3. Set a random webhook secret in the dashboard and only in the server's secret store.
4. Configure the post-payment redirect to the protected success page. The success page must call the server to verify the order; it must not trust a URL parameter by itself.
5. Ensure checkout collects buyer email and mobile number, with a clear consent line for the transactional WhatsApp delivery.

## WhatsApp template

Create and get approval for a utility template, for example:

- Header: **document** — `Modern-History-PDF.pdf`
- Body: `नमस्ते {{1}}, आपका ₹49 का भुगतान सफल रहा। Receipt: {{2}}. PDF नीचे दिए गए document/link से डाउनलोड करें।`
- Button: secure download URL, valid for a short period

If a document is sent from a URL, the backend should generate an expiring URL that Meta can fetch. The PDF must not have a permanent public URL.

## Required server checks

- Verify Razorpay webhook signature against the raw request body.
- Check status is captured/paid and expected price is exactly ₹49 (4,900 paise), INR, and correct product.
- Verify the payment-button/payment-link or server-created order belongs to this product.
- Make fulfillment idempotent: duplicate webhook retries must never send duplicate receipts/PDFs.
- Validate email and normalize phone to E.164 (India: `+91`) before sending.
- Log provider response IDs, but never log secrets or full download URLs.
- Use an expiring signed download endpoint. Refreshes should issue a new entitlement-checked link.

## Test checklist before enabling Live mode

- Successful low-value test payment: website, email and WhatsApp all arrive.
- Failed/cancelled payment: no PDF, email or WhatsApp fulfillment.
- Invalid webhook signature: rejected.
- Wrong amount/product: rejected.
- Duplicate webhook: one order and no duplicate outbound messages.
- Direct visit to delivery URL: no PDF without a verified entitlement.
- Expired link: cannot download; authorized user can request a fresh link.
- Mobile test: checkout, email link, WhatsApp document, and PDF open correctly.
- Run one real Live-mode payment after configuration and then refund it if appropriate.

## What the current site does

The current website is static GitHub Pages. It can show a download page and the Razorpay button can send a receipt, but it cannot itself verify payment, protect a full PDF, send transactional email, or send WhatsApp automatically. Those steps must be run by the server flow above.
