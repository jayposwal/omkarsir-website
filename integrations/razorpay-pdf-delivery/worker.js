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

function descriptionMatches(payment, configuredDescriptions) {
  const description = String(payment.description || "").trim().toLowerCase();
  const allowed = String(configuredDescriptions || "")
    .split("|").map(x => x.trim().toLowerCase()).filter(Boolean);
  return !!description && allowed.some(s => description.includes(s));
}

// Every sellable PDF. A product is live only when its description allow-list
// and R2 object key are configured; otherwise it fails closed (no email, no download).
// Amounts can be overridden per product with a comma-separated paise list.
const PRODUCTS = [
  {
    code: "adhunik-bharat-itihas-pdf",
    name: "सम्पूर्ण आधुनिक भारत का इतिहास PDF",
    description: "20 अध्याय · 537 पृष्ठ · PDF",
    filename: "Sampoorna-Adhunik-Bharat-Itihas-Omkar-Sir.pdf",
    descriptionsEnv: "ALLOWED_PAYMENT_DESCRIPTIONS",
    objectKeyEnv: "PDF_OBJECT_KEY",
    amountsEnv: "ADHUNIK_AMOUNTS_PAISE",
    defaultAmounts: [900, 4900, 9900]
  },
  {
    code: "rajasthan-arthvyavastha-pdf",
    name: "सम्पूर्ण राजस्थान आर्थिक समीक्षा 2025-26 एवं बजट PDF",
    description: "15 अध्याय · 253 पृष्ठ · PDF",
    filename: "Rajasthan-Arthik-Samiksha-2025-26-Omkar-Sir.pdf",
    descriptionsEnv: "ECONOMIC_SURVEY_PAYMENT_DESCRIPTIONS",
    objectKeyEnv: "ECONOMIC_SURVEY_PDF_OBJECT_KEY",
    amountsEnv: "ECONOMIC_SURVEY_AMOUNTS_PAISE",
    defaultAmounts: [4900]
  },
  {
    code: "rajasthan-history-pdf",
    name: "सम्पूर्ण राजस्थान इतिहास PDF",
    description: "16 अध्याय · 234 पृष्ठ · PDF",
    filename: "Sampoorna-Rajasthan-History-Omkar-Sir.pdf",
    descriptionsEnv: "RAJASTHAN_HISTORY_PAYMENT_DESCRIPTIONS",
    objectKeyEnv: "RAJASTHAN_HISTORY_PDF_OBJECT_KEY",
    amountsEnv: "RAJASTHAN_HISTORY_AMOUNTS_PAISE",
    defaultAmounts: [4900]
  },
  {
    code: "ras-mains-paper-2-pdf",
    name: "RAS Mains Paper-II PYQ PDF",
    description: "258 प्रश्न · 131 पृष्ठ · PDF",
    filename: "RAS-Mains-Paper-II-PYQ-Omkar-Sir.pdf",
    descriptionsEnv: "RAS_MAINS_P2_PAYMENT_DESCRIPTIONS",
    objectKeyEnv: "RAS_MAINS_P2_PDF_OBJECT_KEY",
    amountsEnv: "RAS_MAINS_P2_AMOUNTS_PAISE",
    defaultAmounts: [4900]
  }
];

function productByCode(code) {
  return PRODUCTS.find(p => p.code === code) || null;
}

function productAmounts(product, env) {
  const configured = String(env[product.amountsEnv] || "").split(",")
    .map(x => Number(x.trim())).filter(n => Number.isInteger(n) && n > 0);
  return configured.length ? configured : product.defaultAmounts;
}

function matchConfiguredProduct(payment, env) {
  const amount = Number(payment.amount);
  for (const product of PRODUCTS) {
    if (productAmounts(product, env).includes(amount) &&
        descriptionMatches(payment, env[product.descriptionsEnv])) {
      return { ...product, objectKey: String(env[product.objectKeyEnv] || "") };
    }
  }
  return null;
}

async function createDownloadToken(payment, env, productCode) {
  const ttl = Math.min(Math.max(Number(env.DOWNLOAD_TTL_SECONDS || 604800), 3600), 2592000);
  const payload = {
    v: 1,
    product: productCode,
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
        !productByCode(payload.product) ||
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
  if (payment.currency !== "INR") {
    return json({ ok: true, ignored: "currency is not INR" });
  }
  const product = matchConfiguredProduct(payment, env);
  if (!product) {
    console.warn("Captured payment ignored: amount/description did not match a configured PDF product. Payment ID:", payment.id);
    return json({ ok: true, ignored: "payment does not match a configured PDF product" });
  }
  if (!/^pay_[A-Za-z0-9]+$/.test(String(payment.id || "")) || !emailIsValid(payment.email)) {
    console.warn("Captured product payment missing a valid payment ID or customer email.");
    return json({ ok: true, ignored: "payment ID/email missing or invalid" });
  }

  const token = await createDownloadToken(payment, env, product.code);
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
    productCode: product.code,
    productName: product.name,
    productDescription: product.description,
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

// Website delivery: the thank-you page sends the Razorpay payment ID it was
// redirected with. The Worker asks Razorpay's API (server-side, with the key
// secret) whether that payment is really captured for this product, and only
// then returns a signed, time-limited download link. A payment ID alone is not
// trusted for old payments: after VERIFY_FRESH_MINUTES the buyer's checkout
// email must also match.
function corsHeaders(request, env) {
  const origin = request.headers.get("origin") || "";
  const allowed = String(env.ALLOWED_ORIGINS || "https://omkarsir.com,https://www.omkarsir.com")
    .split(",").map(x => x.trim()).filter(Boolean);
  const headers = { "vary": "origin" };
  if (allowed.includes(origin)) {
    headers["access-control-allow-origin"] = origin;
    headers["access-control-allow-methods"] = "GET, OPTIONS";
  }
  return headers;
}

function verifyJson(request, env, data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-robots-tag": "noindex, nofollow",
      ...corsHeaders(request, env)
    }
  });
}

function maskEmail(email) {
  const [user, domain] = String(email).split("@");
  if (!domain) return "";
  return user.slice(0, 2) + "***@" + domain;
}

async function handleVerify(request, env) {
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders(request, env) });
  if (request.method !== "GET") return verifyJson(request, env, { ok: false, error: "method" }, 405);
  if (!env.RAZORPAY_KEY_ID || !env.RAZORPAY_KEY_SECRET || !env.DOWNLOAD_SIGNING_SECRET || !env.PUBLIC_DOWNLOAD_BASE) {
    return verifyJson(request, env, { ok: false, error: "not_configured" }, 503);
  }

  const url = new URL(request.url);
  const paymentId = String(url.searchParams.get("payment_id") || "").trim();
  const requested = productByCode(String(url.searchParams.get("product") || ""));
  const email = String(url.searchParams.get("email") || "").trim().toLowerCase();
  if (!/^pay_[A-Za-z0-9]{6,40}$/.test(paymentId) || !requested) {
    return verifyJson(request, env, { ok: false, error: "bad_request" }, 400);
  }

  let res;
  try {
    res = await fetch("https://api.razorpay.com/v1/payments/" + encodeURIComponent(paymentId), {
      headers: { authorization: "Basic " + btoa(env.RAZORPAY_KEY_ID + ":" + env.RAZORPAY_KEY_SECRET) }
    });
  } catch (err) {
    console.error("Razorpay API unreachable:", String(err));
    return verifyJson(request, env, { ok: false, error: "gateway_unreachable" }, 502);
  }
  if (res.status === 400 || res.status === 404) return verifyJson(request, env, { ok: false, error: "not_found" }, 404);
  if (!res.ok) {
    console.error("Razorpay API error:", res.status);
    return verifyJson(request, env, { ok: false, error: "gateway_error" }, 502);
  }
  const payment = await res.json();

  if (payment.status !== "captured" || payment.currency !== "INR") {
    return verifyJson(request, env, { ok: false, error: "not_captured", status: String(payment.status || "") }, 402);
  }
  const product = matchConfiguredProduct(payment, env);
  if (!product || product.code !== requested.code) {
    return verifyJson(request, env, { ok: false, error: "wrong_product" }, 403);
  }
  if (!emailIsValid(payment.email)) {
    return verifyJson(request, env, { ok: false, error: "no_email_on_payment" }, 422);
  }
  const ageMinutes = (Date.now() / 1000 - Number(payment.created_at || 0)) / 60;
  const freshMinutes = Number(env.VERIFY_FRESH_MINUTES || 30);
  if (ageMinutes > freshMinutes && email !== String(payment.email).toLowerCase()) {
    return verifyJson(request, env, { ok: false, error: "email_required", emailHint: maskEmail(payment.email) }, 401);
  }

  const token = await createDownloadToken(payment, env, product.code);
  return verifyJson(request, env, {
    ok: true,
    product: product.code,
    productName: product.name,
    downloadUrl: String(env.PUBLIC_DOWNLOAD_BASE) + encodeURIComponent(token),
    emailHint: maskEmail(payment.email),
    amountInr: Number(payment.amount) / 100
  });
}

async function handleDownload(request, env) {
  if (request.method !== "GET") return new Response("Method not allowed", { status: 405 });
  if (!env.PDF_BUCKET || !env.DOWNLOAD_SIGNING_SECRET) {
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

  const product = productByCode(payload.product);
  const objectKey = String(env[product.objectKeyEnv] || "");
  if (!objectKey) {
    console.error("The configured PDF object key is missing for product:", payload.product);
    return new Response("इस PDF की download service अभी configure नहीं है। कृपया email2omkara@gmail.com पर संपर्क करें।", {
      status: 503, headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" }
    });
  }
  const object = await env.PDF_BUCKET.get(objectKey);
  if (!object) {
    console.error("Configured PDF object not found in R2:", objectKey);
    return new Response("PDF अभी उपलब्ध नहीं है। कृपया email2omkara@gmail.com पर संपर्क करें।", {
      status: 503, headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" }
    });
  }

  const safeFilename = product.filename;
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
    if (url.pathname === "/verify") return handleVerify(request, env);
    return new Response("Omkar Sir PDF delivery service", {
      status: 200,
      headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" }
    });
  }
};
