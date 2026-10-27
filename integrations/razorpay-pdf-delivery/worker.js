/**
 * Razorpay → Cloudflare Worker (signature verification + signed PDF downloads)
 * → Google Apps Script (Gmail email delivery).
 *
 * Product = Razorpay payment button ID (+ amount); storage = R2, Workers KV or a
 * private GitHub repo (see storageBackend).
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

// ---------------------------------------------------------------------------
// Product identification
//
// Razorpay Payment Buttons do NOT put the button title in payment.description.
// Payments made through a Payment Page / Payment Button carry an order and a
// description of the form "#<button id without the pl_ prefix>" (the format in
// Razorpay's own payment-entity samples, e.g. "#L0nS7JIyuX6Lyb"). That is not a
// documented contract, so the Worker looks for the button ID in every place it
// can legitimately appear and fails closed when nothing (or more than one
// product) matches:
//   1. payment.description equal to "#<id>" or containing "pl_<id>"
//   2. any payment.notes value containing the button ID
//   3. (optional, needs RAZORPAY_KEY_ID/SECRET) the linked order's notes/receipt
// The old title/description allow-list is kept only as a fallback, and the
// amount must always match too.
// ---------------------------------------------------------------------------
const BUTTON_ID_RE = /^pl_[A-Za-z0-9]{6,30}$/;

function productButtonIds(product, env) {
  const raw = env[product.buttonIdsEnv];
  const list = (raw === undefined || raw === null || raw === "")
    ? product.defaultButtonIds
    : String(raw).split(/[,|]/);
  return list.map(x => String(x).trim()).filter(x => BUTTON_ID_RE.test(x));
}

function referenceStrings(payment, order) {
  const out = [];
  const push = v => { if (v !== undefined && v !== null && typeof v !== "object") out.push(String(v).trim()); };
  push(payment && payment.description);
  for (const src of [payment && payment.notes, order && order.notes]) {
    if (src && typeof src === "object") for (const v of Object.values(src)) push(v);
  }
  if (order) { push(order.receipt); push(order.description); }
  return out.filter(Boolean);
}

function buttonMatches(refs, buttonIds) {
  return buttonIds.some(id => {
    const suffix = id.slice(3);
    return refs.some(r => r === "#" + suffix || r === suffix || r === id || r.includes(id) ||
      r.split(/[\s,;|]+/).includes("#" + suffix));
  });
}

// Every sellable PDF. A product is live only when it can be identified (a
// payment-button ID or a description allow-list) and its stored object key is
// configured; otherwise it fails closed (no email, no download).
// Amounts can be overridden per product with a comma-separated paise list.
const PRODUCTS = [
  {
    code: "adhunik-bharat-itihas-pdf",
    name: "सम्पूर्ण आधुनिक भारत का इतिहास PDF",
    description: "20 अध्याय · 537 पृष्ठ · PDF",
    filename: "Sampoorna-Adhunik-Bharat-Itihas-Omkar-Sir.pdf",
    buttonIdsEnv: "ADHUNIK_BUTTON_IDS",
    defaultButtonIds: ["pl_Tmzqpr6RIRGU0K"],
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
    buttonIdsEnv: "ECONOMIC_SURVEY_BUTTON_IDS",
    defaultButtonIds: [], // no Razorpay button exists yet (sales page links to the app)
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
    buttonIdsEnv: "RAJASTHAN_HISTORY_BUTTON_IDS",
    defaultButtonIds: ["pl_TpCUODSwC6kIR9"],
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
    buttonIdsEnv: "RAS_MAINS_P2_BUTTON_IDS",
    defaultButtonIds: ["pl_TmyJkDLHXDE2N3"],
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

// Returns the single product this payment belongs to, or null. If two
// products would match (e.g. an over-broad description substring) it fails
// closed rather than guessing.
function matchConfiguredProduct(payment, env, order) {
  const amount = Number(payment.amount);
  const refs = referenceStrings(payment, order);
  const byButton = [];
  const byDescription = [];
  for (const product of PRODUCTS) {
    if (!productAmounts(product, env).includes(amount)) continue;
    if (buttonMatches(refs, productButtonIds(product, env))) byButton.push(product);
    else if (descriptionMatches(payment, env[product.descriptionsEnv])) byDescription.push(product);
  }
  const hits = byButton.length ? byButton : byDescription;
  if (hits.length !== 1) {
    if (hits.length > 1) console.error("Ambiguous product match; refusing. Payment:", payment.id, hits.map(p => p.code).join(","));
    return null;
  }
  return { ...hits[0], objectKey: String(env[hits[0].objectKeyEnv] || ""), matchedBy: byButton.length ? "button" : "description" };
}

// Optional extra lookup: when a payment carries an order_id and API keys are
// configured, read the order (its notes/receipt may name the payment button).
async function fetchOrder(payment, env) {
  const orderId = String(payment.order_id || "");
  if (!/^order_[A-Za-z0-9]{6,40}$/.test(orderId) || !env.RAZORPAY_KEY_ID || !env.RAZORPAY_KEY_SECRET) return null;
  try {
    const res = await fetch("https://api.razorpay.com/v1/orders/" + encodeURIComponent(orderId), {
      headers: { authorization: "Basic " + btoa(env.RAZORPAY_KEY_ID + ":" + env.RAZORPAY_KEY_SECRET) }
    });
    return res.ok ? await res.json() : null;
  } catch (_) {
    return null;
  }
}

async function identifyProduct(payment, env) {
  const direct = matchConfiguredProduct(payment, env, null);
  if (direct) return direct;
  const order = await fetchOrder(payment, env);
  if (order) {
    const viaOrder = matchConfiguredProduct(payment, env, order);
    if (viaOrder) return viaOrder;
  }
  // Diagnostic without personal data, to configure button IDs after a test purchase.
  const notes = payment.notes && typeof payment.notes === "object" ? Object.keys(payment.notes) : [];
  console.warn("No product match. payment:", payment.id, "amount:", payment.amount,
    "description:", JSON.stringify(String(payment.description || "").slice(0, 80)),
    "notes keys:", notes.join(","), "order:", payment.order_id || "-",
    "order notes:", order && order.notes && typeof order.notes === "object" ? JSON.stringify(order.notes).slice(0, 200) : "-");
  return null;
}

// ---------------------------------------------------------------------------
// Private PDF storage backends (first configured one wins, or force with
// STORAGE_BACKEND = "r2" | "kv" | "github"):
//   r2     – R2 bucket binding PDF_BUCKET (needs a payment method on Cloudflare)
//   kv     – Workers KV binding PDF_KV, value = PDF bytes (25 MiB max per value)
//   github – private GitHub repo GITHUB_PDF_REPO ("owner/repo"), read-only
//            fine-grained token secret GITHUB_PDF_TOKEN, optional
//            GITHUB_PDF_REF (branch, default "main") and GITHUB_PDF_PATH_PREFIX.
// Each returns { body, size|null } or null when the object is missing.
// ---------------------------------------------------------------------------
function storageBackend(env) {
  const forced = String(env.STORAGE_BACKEND || "").trim().toLowerCase();
  const available = {
    r2: !!(env.PDF_BUCKET && typeof env.PDF_BUCKET.get === "function"),
    kv: !!(env.PDF_KV && typeof env.PDF_KV.get === "function"),
    github: !!(env.GITHUB_PDF_REPO && env.GITHUB_PDF_TOKEN)
  };
  if (forced) return available[forced] ? forced : null;
  return ["r2", "kv", "github"].find(b => available[b]) || null;
}

function safeObjectKey(key) {
  return typeof key === "string" && key.length > 0 && key.length <= 300 &&
    !key.split("/").some(seg => seg === "" || seg === "." || seg === "..") &&
    /^[A-Za-z0-9._\/-]+$/.test(key);
}

async function getPdfObject(env, objectKey) {
  const backend = storageBackend(env);
  if (!backend || !safeObjectKey(objectKey)) return null;

  if (backend === "r2") {
    const object = await env.PDF_BUCKET.get(objectKey);
    return object ? { body: object.body, size: object.size, backend } : null;
  }

  if (backend === "kv") {
    const { value, metadata } = await env.PDF_KV.getWithMetadata(objectKey, { type: "stream" });
    if (!value) return null;
    const size = metadata && Number.isInteger(Number(metadata.size)) ? Number(metadata.size) : null;
    return { body: value, size, backend };
  }

  // github: contents API with the raw media type serves files up to 100 MB.
  const repo = String(env.GITHUB_PDF_REPO);
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo)) return null;
  const prefix = String(env.GITHUB_PDF_PATH_PREFIX || "").replace(/^\/+|\/+$/g, "");
  const path = (prefix ? prefix + "/" : "") + objectKey;
  const ref = String(env.GITHUB_PDF_REF || "main");
  const url = "https://api.github.com/repos/" + repo + "/contents/" +
    path.split("/").map(encodeURIComponent).join("/") + "?ref=" + encodeURIComponent(ref);
  const res = await fetch(url, {
    headers: {
      authorization: "Bearer " + env.GITHUB_PDF_TOKEN,
      accept: "application/vnd.github.raw+json",
      "x-github-api-version": "2022-11-28",
      "user-agent": "omkarsir-pdf-delivery"
    },
    redirect: "follow"
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("GitHub storage HTTP " + res.status);
  const len = Number(res.headers.get("content-length"));
  return { body: res.body, size: Number.isInteger(len) && len > 0 ? len : null, backend };
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
  if (!env.RAZORPAY_WEBHOOK_SECRET || !env.DOWNLOAD_SIGNING_SECRET || !env.PUBLIC_DOWNLOAD_BASE) {
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
  const product = await identifyProduct(payment, env);
  if (!product) {
    console.warn("Captured payment ignored: amount/button/description did not match a configured PDF product. Payment ID:", payment.id);
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

  if (!env.APPS_SCRIPT_URL || !env.INTERNAL_SHARED_SECRET) {
    // Email delivery not configured yet: acknowledge so Razorpay does not keep
    // retrying/disable the webhook. Buyers still get the PDF via /verify on the site.
    console.log("Verified captured payment; email delivery not configured. Payment ID:", payment.id, "product:", product.code);
    return json({ ok: true, emailed: false, reason: "email delivery not configured" });
  }

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
  const product = await identifyProduct(payment, env);
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
  if (!storageBackend(env) || !env.DOWNLOAD_SIGNING_SECRET) {
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
  let object;
  try {
    object = await getPdfObject(env, objectKey);
  } catch (err) {
    console.error("PDF storage read failed:", String(err));
    object = null;
  }
  if (!object) {
    console.error("Configured PDF object not found in storage (" + storageBackend(env) + "):", objectKey);
    return new Response("PDF अभी उपलब्ध नहीं है। कृपया email2omkara@gmail.com पर संपर्क करें।", {
      status: 503, headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" }
    });
  }

  const headers = new Headers();
  headers.set("content-type", "application/pdf");
  headers.set("content-disposition", 'attachment; filename="' + product.filename + '"');
  headers.set("cache-control", "private, no-store, max-age=0");
  headers.set("x-robots-tag", "noindex, nofollow");
  headers.set("x-content-type-options", "nosniff");
  if (object.size) headers.set("content-length", String(object.size));
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
