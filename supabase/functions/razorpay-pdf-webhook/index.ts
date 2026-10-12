import {
  createAdminClient,
  createDownloadToken,
  findProduct,
  getDownloadBaseUrl,
  getEnv,
  hmacHex,
  jsonResponse,
  makeEmailHtml,
  validEmail,
  validPaymentId,
  constantTimeEqual,
  type DeliveryRow,
} from "../_shared/pdf-delivery.ts";

Deno.serve(async (request: Request): Promise<Response> => {
  if (request.method !== "POST") return jsonResponse({ ok: false, error: "POST only" }, 405);

  try {
    const webhookSecret = getEnv("RAZORPAY_WEBHOOK_SECRET");
    const resendKey = getEnv("RESEND_API_KEY");
    const emailFrom = getEnv("RESEND_FROM_EMAIL");
    const downloadBaseUrl = getDownloadBaseUrl();
    const tokenSecret = getEnv("PDF_DOWNLOAD_TOKEN_SECRET");
    if (webhookSecret.length < 16 || tokenSecret.length < 32) {
      throw new Error("Webhook/token secret is too short");
    }

    // Verify signature on the exact raw bytes before parsing or trusting JSON.
    const rawBody = await request.text();
    if (rawBody.length > 1024 * 1024) return jsonResponse({ ok: false, error: "Payload too large" }, 413);
    const receivedSignature = request.headers.get("x-razorpay-signature") || "";
    const expectedSignature = await hmacHex(webhookSecret, rawBody);
    if (!receivedSignature || !constantTimeEqual(receivedSignature.toLowerCase(), expectedSignature)) {
      return jsonResponse({ ok: false, error: "Invalid webhook signature" }, 401);
    }

    let event: Record<string, any>;
    try {
      event = JSON.parse(rawBody);
    } catch (_) {
      return jsonResponse({ ok: false, error: "Invalid JSON" }, 400);
    }

    const supabase = createAdminClient();

    // On a confirmed refund, immediately revoke any existing delivery URL.
    if (event.event === "refund.processed") {
      const refund = event.payload?.refund?.entity;
      const paymentId = refund?.payment_id;
      if (validPaymentId(paymentId)) {
        const { error } = await supabase.from("pdf_deliveries")
          .update({ status: "refunded", refunded_at: new Date().toISOString(), updated_at: new Date().toISOString() })
          .eq("payment_id", paymentId);
        if (error) {
          console.error("Could not revoke refunded delivery:", error.message);
          return jsonResponse({ ok: false, error: "Refund revocation could not be recorded" }, 500);
        }
      }
      return jsonResponse({ ok: true, refundProcessed: true });
    }

    if (event.event !== "payment.captured") {
      return jsonResponse({ ok: true, ignored: "event not used" });
    }

    const payment = event.payload?.payment?.entity;
    if (!payment || payment.status !== "captured" || payment.captured !== true) {
      return jsonResponse({ ok: true, ignored: "payment is not captured" });
    }

    const paymentId = payment.id;
    const email = typeof payment.email === "string" ? payment.email.trim().toLowerCase() : "";
    if (!validPaymentId(paymentId) || !validEmail(email)) {
      // A missing checkout email must not result in a public/guessable download.
      console.error("Captured payment has no valid payment ID/email; check Razorpay checkout email settings.");
      return jsonResponse({ ok: true, ignored: "valid payment ID/email required" });
    }

    const product = findProduct(payment as Record<string, unknown>);
    if (!product) {
      console.warn("Captured payment did not match a configured PDF product. No delivery issued.");
      return jsonResponse({ ok: true, ignored: "no matching configured PDF product" });
    }

    const amountPaise = Number(payment.amount);
    const description = String(payment.description || "").trim().slice(0, 250);
    const ttlValue = Number(Deno.env.get("PDF_DOWNLOAD_TTL_SECONDS") || "604800");
    const ttlSeconds = Number.isInteger(ttlValue) ? Math.min(Math.max(ttlValue, 3600), 2592000) : 604800;
    const maxValue = Number(Deno.env.get("PDF_MAX_DOWNLOADS") || "5");
    const maxDownloads = Number.isInteger(maxValue) ? Math.min(Math.max(maxValue, 1), 25) : 5;
    const expiresAtForInsert = new Date(Date.now() + ttlSeconds * 1000).toISOString();

    // Unique payment_id provides webhook idempotency. A repeated event reuses
    // the existing row/expiry so the emailed token remains exactly the same.
    const { error: insertError } = await supabase.from("pdf_deliveries").upsert({
      payment_id: paymentId,
      product_code: product.code,
      customer_email: email,
      amount_paise: amountPaise,
      currency: "INR",
      payment_description: description,
      status: "pending",
      expires_at: expiresAtForInsert,
      max_downloads: maxDownloads,
      download_count: 0,
      updated_at: new Date().toISOString(),
    }, { onConflict: "payment_id", ignoreDuplicates: true });
    if (insertError) {
      console.error("Could not persist captured payment:", insertError.message);
      return jsonResponse({ ok: false, error: "Could not record delivery" }, 500);
    }

    const { data: rowData, error: rowError } = await supabase.from("pdf_deliveries")
      .select("id,payment_id,product_code,customer_email,amount_paise,currency,payment_description,status,expires_at,max_downloads,download_count,email_attempts,updated_at,emailed_at")
      .eq("payment_id", paymentId)
      .maybeSingle();
    if (rowError || !rowData) {
      console.error("Could not load saved delivery:", rowError?.message || "row missing");
      return jsonResponse({ ok: false, error: "Could not load delivery record" }, 500);
    }

    const row = rowData as DeliveryRow;
    if (row.product_code !== product.code ||
        row.amount_paise !== amountPaise ||
        row.customer_email.toLowerCase() !== email) {
      console.error("Existing payment record did not match this webhook's product details.");
      return jsonResponse({ ok: true, ignored: "saved payment record mismatch" });
    }
    if (row.status === "refunded") return jsonResponse({ ok: true, ignored: "payment refunded" });
    if (row.status === "sent") return jsonResponse({ ok: true, emailed: true, duplicate: true });

    const { data: claimed, error: claimError } = await supabase.rpc("claim_pdf_delivery_email", {
      p_delivery_id: row.id,
    });
    if (claimError) {
      console.error("Could not claim email delivery:", claimError.message);
      return jsonResponse({ ok: false, error: "Could not claim email delivery" }, 500);
    }
    if (claimed !== true) {
      const { data: latest } = await supabase.from("pdf_deliveries")
        .select("status").eq("id", row.id).maybeSingle();
      if (latest?.status === "sent") return jsonResponse({ ok: true, emailed: true, duplicate: true });
      // Ask Razorpay to retry if another invocation is sending or recovering this event.
      return jsonResponse({ ok: false, error: "Delivery is being processed; retry webhook" }, 503);
    }

    const token = await createDownloadToken(row);
    const downloadUrl = downloadBaseUrl + token;
    const emailContent = makeEmailHtml(product, downloadUrl, row.expires_at, row.max_downloads);

    let resendResponse: Response;
    let resendText = "";
    try {
      resendResponse = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          "authorization": "Bearer " + resendKey,
          "content-type": "application/json",
          // If sending succeeded but the database update timed out, a webhook retry
          // reuses this key and the same URL instead of sending a duplicate email.
          "Idempotency-Key": "pdf-delivery-" + paymentId,
        },
        body: JSON.stringify({
          from: emailFrom,
          to: [row.customer_email],
          reply_to: "email2omkara@gmail.com",
          subject: "आपकी PDF तैयार है — " + product.name + " | Omkar Sir",
          html: emailContent.html,
          text: emailContent.text,
        }),
      });
      resendText = await resendResponse.text();
    } catch (error) {
      await supabase.from("pdf_deliveries").update({
        status: "email_failed",
        last_error: "Resend request failed: " + String(error).slice(0, 300),
        updated_at: new Date().toISOString(),
      }).eq("id", row.id);
      return jsonResponse({ ok: false, error: "Email provider unreachable; webhook retry requested" }, 502);
    }

    if (!resendResponse.ok) {
      console.error("Resend returned non-success status:", resendResponse.status, resendText.slice(0, 300));
      await supabase.from("pdf_deliveries").update({
        status: "email_failed",
        last_error: "Resend HTTP " + resendResponse.status,
        updated_at: new Date().toISOString(),
      }).eq("id", row.id);
      return jsonResponse({ ok: false, error: "Email provider rejected delivery; webhook retry requested" }, 502);
    }

    const { error: finishError } = await supabase.from("pdf_deliveries").update({
      status: "sent",
      emailed_at: new Date().toISOString(),
      last_error: null,
      updated_at: new Date().toISOString(),
    }).eq("id", row.id);
    if (finishError) {
      console.error("Email was accepted but status update failed:", finishError.message);
      // A retry uses the Resend idempotency key and the same stable download URL.
      return jsonResponse({ ok: false, error: "Email sent but status could not be saved; retry requested" }, 500);
    }

    return jsonResponse({ ok: true, emailed: true, product: product.code });
  } catch (error) {
    console.error("Razorpay PDF webhook failed:", String(error).slice(0, 500));
    return jsonResponse({ ok: false, error: "Webhook processing failed" }, 500);
  }
});
