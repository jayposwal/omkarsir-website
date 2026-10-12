# Paid PDF: Conversion Tracking & Secure Delivery Plan

Repository: jayposwal/omkarsir-website  
Product page: /adhunik-bharat-itihas-pdf.html  
Delivery page: /download-adhunik-bharat-itihas.html

## What was changed on branch `fix/pdf-tracking-and-delivery`

The product page now captures common attribution parameters in sessionStorage and emits GA4 `view_item`, `page_view`, and an estimated `begin_checkout` event when a click is detected within the Razorpay purchase-button area. This is preliminary browser-side tracking, not proof of payment.

The page also includes a guarded `window.niedPaidPdfTracking.sendVerifiedPurchase(payment)` helper. It emits GA4 `purchase` only when called with `verified: true`, a valid paymentId, and a price value. Do not call this from a query parameter, a URL redirect alone, or any client-supplied payment state.

## Required setup before production

1. Confirm the GA4 property is G-WCK16L4WZX and that GA4 is installed on the checkout/success pages where possible.
2. In GA4 Admin, mark the `purchase` event as a key event; confirm ecommerce purchase event fields in DebugView and Realtime.
3. Add the relevant Meta Pixel ID in Meta Events Manager and Google Ads conversion ID/label in their respective dashboards. IDs must come from the account owner; never invent placeholders or store access tokens in frontend source.
4. Configure cross-domain / payment attribution where supported by the actual Razorpay payment-button flow. Since Razorpay-hosted checkout may not expose a browser success callback to this static page, do not treat click or thank-you-page view as a purchase.
5. The robust way to emit purchase and secure fulfillment is a backend endpoint receiving a Razorpay webhook, verifying the webhook signature using a server-side secret, checking payment status, amount, currency and product, deduplicating by payment ID, and only then recording the paid order.
6. Store the PDF in private object storage or protected server storage. Serve it only after a server-side order entitlement check, preferably by issuing a short-lived signed URL after verified payment. Do not put the source PDF URL or server secrets into HTML/JavaScript.
7. The existing static delivery page is not an access-control boundary. A payment ID displayed in a query string can be forged and the existence of a `?payment_id=...` is not payment proof. Replace static Drive links only after protected storage + verification endpoint are deployed and tested.
8. Run a real low-value test payment and refund it. Check failed payment, successful payment, refresh, direct visit to delivery URL, duplicate webhook, invalid signature, and another user's order ID.

## Current limitation

This repository is a static website in the inspected files; no backend, webhook handler, serverless functions, or private storage configuration was found in the inspected paths. For that reason, this branch does **not** pretend to make the delivery secure. Secure delivery requires configuring a server-side service/hosting environment and the actual Razorpay webhook secret, which must stay server-side.

## Events intended for GA4

- `view_item`: product page view
- `begin_checkout`: click detected around the embedded payment button (diagnostic only; may be approximate)
- `purchase`: ONLY from a verified payment backend / trusted success channel; never from the landing-page click or success URL alone

Useful attribution fields to retain (respect consent and applicable privacy rules): `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `gclid`, `gbraid`, `wbraid`, `fbclid`.
