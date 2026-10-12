/**
 * Razorpay → Cloudflare Worker (signature verification + signed PDF downloads)
 * → Google Apps Script (Gmail email delivery).
 *
 * Required bindings/secrets are documented in README.md. Keep all secret values
 * server-side; never place them in HTML or this file.
 */

const encoder = new TextEncoder();

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
  });
}

function toHex(bytes) {
  return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, "0")).join("");
}

function base64Url(bytes) {
  let binary = "";
  for (const b of new Uint8Array(bytes)) binary += String.fromCharCode(b);
  return btoa(binary).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

function fromBase64Url(value) {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64 + "=".repeat((4 - base64.length % 4) % 4);
  const binary = atob(padded);
  return Uint8Array.from(binary, c => c.charCodeAt(0));
}

async function hmacHex(secret, message) {
  const key = await crypto.subtle.importKey(
    "raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  return toHex(await crypto.subtle.sign("HMAC", key, encoder.encode(message)));
}

async function hmacBase64Url(secret, message) {
  const key = await crypto.subtle.importKey(
    "raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  return base64Url(await crypto.subtle.sign("HMAC", key, encoder.encode(message)));
}

function constantTimeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function emailIsValid(value) {
  return typeof value === "string" &&
    value.length <= 254 &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function allowedDescription(payment, env) {
  const description = String(payment.description || "").trim().toLowerCase();
  const allowed = String(env.ALLOWED_PAYMENT_DESCRIPTIONS || "")
    .split("|").map(x => x.trim().toLowerCase()).filter(Boolean);
  // A matching description is required in addition to INR amount; this avoids
  // emailing the product for unrelated payments of the same value.
  return !!description && allowed.some(s => description.includes(s));
}

async function createDownloadToken(payment, env) {
  const ttl = Math.min(Math.max(Number(env.DOWNLOAD_TTL_SECONDS || 604800), 3600), 2592000);
  const payload = {
    v: 1,
    product: "adhunik-bharat-itihas-pdf",
    paymentId: String(payment.id),
    email: String(payment.email).toLowerCase(),
    exp: Math.floor(Date.now() / 1000) + ttl
  };
  const body = base64Url(encoder.encode(JSON.stringify(payload)));
  const signature = await hmacBase64Url(env.DOWNLOAD_SIGNING_SECRET, body);
  return body + "." + signature;
}

async function verifyDownloadToken(token, env) {
  if (!token || token.length > 3000) return null;
  const parts = token.split(".");
  if (parts.length !== 2) return null;
  const expected = await hmacBase64Url(env.DOWNLOAD_SIGNING_SECRET, parts[0]);
  if (!constantTimeEqual(parts[1], expected)) return null;
  try {
    const payload = JSON.parse(new TextDecoder().decode(fromBase64Url(parts[0])));
    if (payload.v !== 1 ||
        payload.product !== "adhunik-bharat-itihas-pdf" ||
        typeof payload.paymentId !== "string" ||
        !/^pay_[A-Za-z0-9]+$/.test(payload.paymentId) ||
        !emailIsValid(payload.email) ||
        !Number.isInteger(payload.exp) ||
        payload.exp <= Math.floor(Date.now() / 1000)) return null;
    return payload;
  } catch (_) {
    return null;
  }
}

async function handleWebhook(request, env) {
  if (request.method !== "POST") return json({ ok: false, error: "POST only" }, 405);
  if (!env.RAZORPAY_WEBHOOK_SECRET || !env.DOWNLOAD_SIGNING_SECRET ||
      !env.APPS_SCRIPT_URL || !env.INTERNAL_SHARED_SECRET || !env.PUBLIC_DOWNLOAD_BASE) {
    console.error("Missing required Worker configuration.");
    return json({ ok: false, error: "Server configuration incomplete" }, 500);
  }

  // Signature must be computed over the exact raw body, before JSON parsing.
  const rawBody = await request.text();
  const received = request.headers.get("x-razorpay-signature") || "";
  const expected = await hmacHex(env.RAZORPAY_WEBHOOK_SECRET, rawBody);
  if (!constantTimeEqual(received.toLowerCase(), expected)) {
    return json({ ok: false, error: "Invalid webhook signature" }, 401);
  }

  let event;
  try { event = JSON.parse(rawBody); }
  catch (_) { return json({ ok: false, error: "Invalid JSON" }, 400); }

  if (event.event !== "payment.captured") return json({ ok: true, ignored: "event not used" });

  const payment = event.payload && event.payload.payment && event.payload.payment.entity;
  if (!payment || payment.status !== "captured" || payment.captured !== true) {
    return json({ ok: true, ignored: "payment not captured" });
  }
  if (payment.currency !== "INR" || ![900, 9900].includes(Number(payment.amount))) {
    return json({ ok: true, ignored: "not one of the configured PDF prices" });
  }
  if (!allowedDescription(payment, env)) {
    console.warn("Captured payment ignored: description did not match configured product. Payment ID:", payment.id);
    return json({ ok: true, ignored: "payment description does not match PDF product" });
  }
  if (!/^pay_[A-Za-z0-9]+$/.test(String(payment.id || "")) || !emailIsValid(payment.email)) {
    console.warn("Captured product payment missing a valid payment ID or customer email.");
    return json({ ok: true, ignored: "payment ID/email missing or invalid" });
  }

  const token = await createDownloadToken(payment, env);
  const base = String(env.PUBLIC_DOWNLOAD_BASE);
  if (!base.startsWith("https://") || !base.endsWith("/download?token=")) {
    console.error("PUBLIC_DOWNLOAD_BASE must look like https://your-worker-domain/download?token=");
    return json({ ok: false, error: "Download URL configuration invalid" }, 500);
  }
  const downloadUrl = base + encodeURIComponent(token);
  const emailPayload = {
    internalSecret: env.INTERNAL_SHARED_SECRET,
    action: "send_pdf_delivery",
    paymentId: String(payment.id),
    email: String(payment.email).trim().toLowerCase(),
    amountPaise: Number(payment.amount),
    currency: payment.currency,
    productCode: "adhunik-bharat-itihas-pdf",
    productName: "सम्पूर्ण आधुनिक भारत का इतिहास PDF",
    downloadUrl: downloadUrl,
    expiresAt: JSON.parse(new TextDecoder().decode(fromBase64Url(token.split(".")[0]))).exp,
    description: String(payment.description || "")
  };

  let response;
  let responseText;
  try {
    response = await fetch(env.APPS_SCRIPT_URL, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(emailPayload),
      redirect: "follow"
    });
    responseText = await response.text();
  } catch (err) {
    console.error("Gmail delivery endpoint request failed:", String(err));
    return json({ ok: false, error: "Email endpoint unreachable; webhook retry may be used" }, 500);
  }

  let result;
  try { result = JSON.parse(responseText); }
  catch (_) { result = null; }

  // Apps Script often responds through a Google redirect. Check its JSON body,
  // not only HTTP status, because Apps Script application errors can return 200.
  if (!response.ok || !result || result.ok !== true) {
    console.error("Email service returned an error:", response.status, responseText.slice(0, 500));
    return json({ ok: false, error: "Email service did not confirm delivery" }, 500);
  }
  return json({ ok: true, emailed: true, duplicate: !!result.duplicate });
}

async function handleDownload(request, env) {
  if (request.method !== "GET") return new Response("Method not allowed", { status: 405 });
  if (!env.PDF_BUCKET || !env.PDF_OBJECT_KEY || !env.DOWNLOAD_SIGNING_SECRET) {
    return new Response("Download service is not configured yet.", {
      status: 503, headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" }
    });
  }
  const url = new URL(request.url);
  const payload = await verifyDownloadToken(url.searchParams.get("token"), env);
  if (!payload) {
    return new Response("यह download link अमान्य या समाप्त हो चुका है। सहायता के लिए email2omkara@gmail.com पर संपर्क करें।", {
      status: 403,
      headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store", "x-robots-tag": "noindex, nofollow" }
    });
  }

  const object = await env.PDF_BUCKET.get(env.PDF_OBJECT_KEY);
  if (!object) {
    console.error("Configured PDF object not found in R2:", env.PDF_OBJECT_KEY);
    return new Response("PDF अभी उपलब्ध नहीं है। कृपया email2omkara@gmail.com पर संपर्क करें।", {
      status: 503, headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" }
    });
  }

  const safeFilename = "Sampoorna-Adhunik-Bharat-Itihas-Omkar-Sir.pdf";
  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set("content-type", "application/pdf");
  headers.set("content-disposition", 'attachment; filename="' + safeFilename + '"');
  headers.set("cache-control", "private, no-store, max-age=0");
  headers.set("x-robots-tag", "noindex, nofollow");
  headers.set("x-content-type-options", "nosniff");
  headers.set("content-length", String(object.size));
  return new Response(object.body, { headers });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/webhook") return handleWebhook(request, env);
    if (url.pathname === "/download") return handleDownload(request, env);
    return new Response("Omkar Sir PDF delivery service", {
      status: 200,
      headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" }
    });
  }
};
