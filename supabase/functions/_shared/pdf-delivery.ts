import { createClient } from "npm:@supabase/supabase-js@2";

export type PdfProduct = {
  code: string;
  name: string;
  amountPaise: number[];
  descriptionIncludes: string[];
  objectKey: string;
  filename: string;
  details: string;
};

export type DeliveryRow = {
  id: string;
  payment_id: string;
  product_code: string;
  customer_email: string;
  amount_paise: number;
  currency: string;
  payment_description: string;
  status: string;
  expires_at: string;
  max_downloads: number;
  download_count: number;
  email_attempts: number;
  updated_at: string;
  emailed_at: string | null;
};

export type DownloadClaims = {
  v: 1;
  id: string;
  paymentId: string;
  productCode: string;
  exp: number;
};

export const PRODUCTS: PdfProduct[] = [
  {
    code: "ras-mains-paper-2-pdf",
    name: "RAS Mains Paper-II PYQ PDF",
    amountPaise: [4900],
    // Match the product title/description used by the Razorpay Payment Button.
    // If the real webhook shows a different description, update this list,
    // deploy again, and test before switching to live payments.
    descriptionIncludes: [
      "ras mains paper-ii",
      "ras mains paper ii",
      "ras mains paper-2",
      "ras mains paper 2",
    ],
    objectKey: "ras-mains-paper-2-pdf.pdf",
    filename: "RAS-Mains-Paper-II-PYQ-Omkar-Sir.pdf",
    details: "258 प्रश्न · तीनों Units · 131 पृष्ठ",
  },
  {
    code: "adhunik-bharat-itihas-pdf",
    name: "सम्पूर्ण आधुनिक भारत का इतिहास PDF",
    amountPaise: [900, 9900],
    descriptionIncludes: [
      "adhunik itihas",
      "modern indian history",
      "सम्पूर्ण आधुनिक भारत का इतिहास",
    ],
    objectKey: "adhunik-bharat-itihas.pdf",
    filename: "Sampoorna-Adhunik-Bharat-Itihas-Omkar-Sir.pdf",
    details: "20 अध्याय · 537 पृष्ठ · रंगीन मानचित्र और तालिकाएँ",
  },
];

const encoder = new TextEncoder();

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });
}

export function getEnv(name: string): string {
  const value = Deno.env.get(name)?.trim();
  if (!value) throw new Error("Missing required environment variable: " + name);
  return value;
}

function getSupabaseServiceKey(): string {
  const legacy = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (legacy) return legacy;

  // Supabase is gradually exposing named secret keys to Edge Functions.
  const keysJson = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (keysJson) {
    try {
      const parsed = JSON.parse(keysJson);
      const candidate = parsed.default ?? Object.values(parsed)[0];
      if (typeof candidate === "string" && candidate.length > 0) return candidate;
    } catch (_) {
      // Keep the error generic below; never log key material.
    }
  }
  throw new Error("Supabase server key is not available to the Edge Function");
}

export function createAdminClient() {
  return createClient(getEnv("SUPABASE_URL"), getSupabaseServiceKey(), {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}

export function constantTimeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let difference = 0;
  for (let i = 0; i < a.length; i++) {
    difference |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return difference === 0;
}

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function hmacHex(secret: string, message: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(message));
  return bytesToHex(new Uint8Array(signature));
}

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

function fromBase64Url(value: string): Uint8Array {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - normalized.length % 4) % 4);
  const binary = atob(padded);
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

async function hmacBase64Url(secret: string, message: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(message));
  return base64Url(new Uint8Array(signature));
}

export function validEmail(value: unknown): value is string {
  return typeof value === "string" &&
    value.length <= 254 &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

export function validPaymentId(value: unknown): value is string {
  return typeof value === "string" && /^pay_[A-Za-z0-9]+$/.test(value);
}

export function findProduct(payment: Record<string, unknown>): PdfProduct | null {
  if (payment.currency !== "INR") return null;
  const amount = Number(payment.amount);
  if (!Number.isSafeInteger(amount)) return null;

  const description = String(payment.description || "").trim().toLowerCase();
  if (!description) return null;

  const candidates = PRODUCTS.filter((product) =>
    product.amountPaise.includes(amount) &&
    product.descriptionIncludes.some((needle) => description.includes(needle.toLowerCase()))
  );
  // Fail closed if product matcher configuration ever becomes ambiguous.
  return candidates.length === 1 ? candidates[0] : null;
}

export function getDownloadBaseUrl(): string {
  const value = getEnv("PDF_DOWNLOAD_BASE_URL");
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch (_) {
    throw new Error("PDF_DOWNLOAD_BASE_URL is not a valid URL");
  }
  if (parsed.protocol !== "https:" ||
      parsed.search !== "?token=" ||
      !parsed.pathname.endsWith("/functions/v1/pdf-download") ||
      parsed.hash) {
    throw new Error("PDF_DOWNLOAD_BASE_URL must end with /functions/v1/pdf-download?token=");
  }
  return value;
}

export async function createDownloadToken(row: DeliveryRow): Promise<string> {
  const secret = getEnv("PDF_DOWNLOAD_TOKEN_SECRET");
  if (secret.length < 32) throw new Error("PDF_DOWNLOAD_TOKEN_SECRET must be at least 32 characters");
  const claims: DownloadClaims = {
    v: 1,
    id: row.id,
    paymentId: row.payment_id,
    productCode: row.product_code,
    exp: Math.floor(new Date(row.expires_at).getTime() / 1000),
  };
  const body = base64Url(encoder.encode(JSON.stringify(claims)));
  const signature = await hmacBase64Url(secret, body);
  return body + "." + signature;
}

export async function verifyDownloadToken(token: string): Promise<DownloadClaims | null> {
  if (!token || token.length > 3000) return null;
  const parts = token.split(".");
  if (parts.length !== 2 || !parts[0] || !parts[1]) return null;
  const secret = Deno.env.get("PDF_DOWNLOAD_TOKEN_SECRET") || "";
  if (secret.length < 32) throw new Error("PDF_DOWNLOAD_TOKEN_SECRET must be at least 32 characters");

  const expected = await hmacBase64Url(secret, parts[0]);
  if (!constantTimeEqual(parts[1], expected)) return null;

  try {
    const claims = JSON.parse(new TextDecoder().decode(fromBase64Url(parts[0]))) as DownloadClaims;
    if (claims.v !== 1 ||
        typeof claims.id !== "string" ||
        !/^[0-9a-f-]{36}$/i.test(claims.id) ||
        !validPaymentId(claims.paymentId) ||
        typeof claims.productCode !== "string" ||
        !Number.isInteger(claims.exp) ||
        claims.exp <= Math.floor(Date.now() / 1000)) return null;
    return claims;
  } catch (_) {
    return null;
  }
}

export function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[character] || character));
}

export function makeEmailHtml(
  product: PdfProduct,
  downloadUrl: string,
  expiresAt: string,
  maxDownloads: number,
): { html: string; text: string } {
  const safeName = escapeHtml(product.name);
  const safeDetails = escapeHtml(product.details);
  const safeUrl = escapeHtml(downloadUrl);
  const exp = new Date(expiresAt);
  const expiryLabel = exp.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    dateStyle: "medium",
    timeStyle: "short",
  }) + " IST";

  const text = "नमस्ते!\n\n" + product.name +
    " की खरीद के लिए धन्यवाद। आपकी सुरक्षित PDF डाउनलोड लिंक:\n" + downloadUrl +
    "\n\nलिंक " + expiryLabel + " तक मान्य है और अधिकतम " + maxDownloads +
    " डाउनलोड की अनुमति देता है। लिंक निजी रखें।\n\nलिंक काम न करे तो email2omkara@gmail.com पर लिखें।\n\nOmkar Sir | New India Education";

  const html =
    '<div style="margin:0;padding:24px 12px;background:#f4f6fb;font-family:Arial,Helvetica,sans-serif;color:#1a2140">' +
    '<div style="max-width:600px;margin:0 auto;background:#ffffff;border:1px solid #e2e7f2;border-radius:18px;overflow:hidden">' +
    '<div style="padding:28px 24px;background:#1b2a6b;color:#ffffff">' +
    '<div style="font-size:13px;letter-spacing:.5px;color:#dfe5ff">NEW INDIA EDUCATION · OMKAR SIR</div>' +
    '<h1 style="font-size:24px;line-height:1.35;margin:12px 0 6px">आपकी PDF तैयार है! 🎉</h1>' +
    '<p style="font-size:15px;line-height:1.6;margin:0;color:#e5eaff">भुगतान के लिए धन्यवाद। नीचे दिए बटन से अपनी PDF डाउनलोड करें।</p>' +
    '</div><div style="padding:26px 24px">' +
    '<h2 style="font-size:20px;line-height:1.5;margin:0 0 8px">' + safeName + '</h2>' +
    '<p style="font-size:14px;line-height:1.8;color:#5b6385;margin:0 0 20px">' + safeDetails + '</p>' +
    '<a href="' + safeUrl + '" style="display:block;text-align:center;background:#ff6b00;color:#ffffff;text-decoration:none;font-weight:bold;font-size:19px;line-height:1.4;padding:17px 16px;border-radius:12px">⬇️ PDF Download करें</a>' +
    '<p style="font-size:13px;line-height:1.8;color:#5b6385;margin:18px 0 0">यह निजी लिंक ' + escapeHtml(expiryLabel) +
    ' तक मान्य है और अधिकतम ' + maxDownloads + ' डाउनलोड की अनुमति देता है। इसे सार्वजनिक रूप से साझा न करें।</p>' +
    '<div style="margin-top:22px;padding-top:18px;border-top:1px solid #e8eaf0;font-size:13px;line-height:1.8;color:#5b6385">बटन न खुले? इस लिंक को browser में copy करें:<br><a href="' +
    safeUrl + '" style="color:#1b2a6b;word-break:break-all">' + safeUrl +
    '</a><br><br>सहायता: <a href="mailto:email2omkara@gmail.com" style="color:#1b2a6b">email2omkara@gmail.com</a></div>' +
    '</div><div style="padding:16px 24px;background:#f8f9fc;color:#6b7280;font-size:12px;line-height:1.6">Omkar Sir · New India Education, Jaipur</div>' +
    '</div></div>';

  return { html, text };
}
