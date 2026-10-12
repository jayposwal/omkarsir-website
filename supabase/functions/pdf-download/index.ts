import {
  createAdminClient,
  jsonResponse,
  verifyDownloadToken,
  PRODUCTS,
} from "../_shared/pdf-delivery.ts";

function plain(message: string, status: number): Response {
  return new Response(message, {
    status,
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "private, no-store, max-age=0",
      "x-robots-tag": "noindex, nofollow",
      "x-content-type-options": "nosniff",
      "referrer-policy": "no-referrer",
    },
  });
}

Deno.serve(async (request: Request): Promise<Response> => {
  if (request.method !== "GET") return plain("Method not allowed", 405);

  try {
    const url = new URL(request.url);
    const token = url.searchParams.get("token") || "";
    const claims = await verifyDownloadToken(token);
    if (!claims) {
      return plain("यह सुरक्षित download link अमान्य या समाप्त हो चुका है। सहायता के लिए email2omkara@gmail.com पर संपर्क करें।", 403);
    }

    const product = PRODUCTS.find((item) => item.code === claims.productCode);
    if (!product) return plain("यह PDF लिंक अमान्य है। सहायता के लिए email2omkara@gmail.com पर संपर्क करें।", 403);

    const supabase = createAdminClient();
    const { data: row, error: rowError } = await supabase.from("pdf_deliveries")
      .select("id,payment_id,product_code,customer_email,status,expires_at,max_downloads,download_count")
      .eq("id", claims.id)
      .maybeSingle();

    if (rowError) {
      console.error("Could not load download entitlement:", rowError.message);
      return plain("Download सेवा अभी उपलब्ध नहीं है। कृपया कुछ देर बाद प्रयास करें।", 503);
    }

    const expirySecond = row?.expires_at ? Math.floor(new Date(row.expires_at).getTime() / 1000) : 0;
    if (!row ||
        row.status !== "sent" ||
        row.payment_id !== claims.paymentId ||
        row.product_code !== claims.productCode ||
        expirySecond !== claims.exp ||
        expirySecond <= Math.floor(Date.now() / 1000)) {
      return plain("यह सुरक्षित download link अमान्य, वापस किया गया या समाप्त हो चुका है। सहायता के लिए email2omkara@gmail.com पर संपर्क करें।", 403);
    }

    // An atomic database operation prevents exceeding the configured download cap.
    const { data: allowed, error: countError } = await supabase.rpc("consume_pdf_download", {
      p_delivery_id: row.id,
    });
    if (countError) {
      console.error("Could not enforce download limit:", countError.message);
      return plain("Download सेवा अभी उपलब्ध नहीं है। कृपया कुछ देर बाद प्रयास करें।", 503);
    }
    if (allowed !== true) {
      return plain("इस लिंक की समय-सीमा समाप्त हो गई है या डाउनलोड सीमा पूरी हो गई है। सहायता के लिए email2omkara@gmail.com पर संपर्क करें।", 403);
    }

    const { data: file, error: fileError } = await supabase.storage
      .from("private-pdfs")
      .download(product.objectKey);
    if (fileError || !file) {
      console.error("Private PDF object unavailable:", product.code, fileError?.message || "object missing");
      return plain("PDF अभी उपलब्ध नहीं है। सहायता के लिए email2omkara@gmail.com पर संपर्क करें।", 503);
    }

    return new Response(file.stream(), {
      status: 200,
      headers: {
        "content-type": "application/pdf",
        "content-disposition": 'attachment; filename="' + product.filename + '"',
        "content-length": String(file.size),
        "cache-control": "private, no-store, max-age=0",
        "x-robots-tag": "noindex, nofollow",
        "x-content-type-options": "nosniff",
        "referrer-policy": "no-referrer",
      },
    });
  } catch (error) {
    console.error("PDF download failed:", String(error).slice(0, 400));
    return jsonResponse({ ok: false, error: "Download service failed" }, 503);
  }
});
