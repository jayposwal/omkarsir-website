/**
 * Omkar Sir PDF email sender.
 *
 * The Apps Script web app is NOT the Razorpay webhook receiver. A Cloudflare
 * Worker verifies x-razorpay-signature first, then forwards only verified
 * purchase data to this script with INTERNAL_SHARED_SECRET.
 */

function setup() {
  var props = PropertiesService.getScriptProperties();
  var secret = props.getProperty('INTERNAL_SHARED_SECRET');
  if (!secret) {
    secret = Utilities.getUuid().replace(/-/g, '') +
             Utilities.getUuid().replace(/-/g, '') +
             Utilities.getUuid().replace(/-/g, '');
    props.setProperty('INTERNAL_SHARED_SECRET', secret);
  }

  var sheetId = props.getProperty('DELIVERY_LOG_SHEET_ID');
  var ss;
  if (!sheetId) {
    ss = SpreadsheetApp.create('Omkar Sir — PDF Delivery Log');
    sheetId = ss.getId();
    props.setProperty('DELIVERY_LOG_SHEET_ID', sheetId);
  } else {
    ss = SpreadsheetApp.openById(sheetId);
  }

  var sheet = ss.getSheets()[0];
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(['Payment ID', 'Email', 'Amount INR', 'Product', 'Status', 'Updated At', 'Description']);
    sheet.setFrozenRows(1);
  }

  Logger.log('Delivery log spreadsheet: ' + ss.getUrl());
  Logger.log('Copy this INTERNAL_SHARED_SECRET into the Cloudflare Worker secret of the same name: ' + secret);
  Logger.log('After Worker deployment, set DOWNLOAD_BASE_URL to: https://YOUR-WORKER-DOMAIN/download?token=');
  Logger.log('Next: Deploy > New deployment > Web app; execute as you; access: Anyone.');
}

function doGet() {
  return ContentService
    .createTextOutput(JSON.stringify({ service: 'Omkar Sir PDF mailer', ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  var payload;
  try {
    if (!e || !e.postData || !e.postData.contents) return output_({ ok: false, error: 'Missing request body' });
    payload = JSON.parse(e.postData.contents);
  } catch (err) {
    return output_({ ok: false, error: 'Invalid JSON' });
  }

  var props = PropertiesService.getScriptProperties();
  var savedSecret = props.getProperty('INTERNAL_SHARED_SECRET') || '';
  if (!savedSecret || !constantTimeEqual_(String(payload.internalSecret || ''), savedSecret)) {
    return output_({ ok: false, error: 'Unauthorized' });
  }

  if (payload.action !== 'send_pdf_delivery' ||
      payload.productCode !== 'adhunik-bharat-itihas-pdf' ||
      payload.currency !== 'INR' ||
      !/^pay_[A-Za-z0-9]+$/.test(String(payload.paymentId || '')) ||
      !emailIsValid_(String(payload.email || '')) ||
      ![900, 9900].includes(Number(payload.amountPaise))) {
    return output_({ ok: false, error: 'Invalid purchase payload' });
  }

  var base = props.getProperty('DOWNLOAD_BASE_URL') || '';
  var downloadUrl = String(payload.downloadUrl || '');
  if (!base || downloadUrl.indexOf(base) !== 0 || base.indexOf('https://') !== 0 ||
      downloadUrl.length > 4000 || !Number.isFinite(Number(payload.expiresAt)) ||
      Number(payload.expiresAt) <= Math.floor(Date.now() / 1000)) {
    return output_({ ok: false, error: 'Download URL not configured or invalid' });
  }

  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);
    var sheetId = props.getProperty('DELIVERY_LOG_SHEET_ID');
    if (!sheetId) return output_({ ok: false, error: 'Run setup() first' });
    var sheet = SpreadsheetApp.openById(sheetId).getSheets()[0];
    var lastRow = sheet.getLastRow();
    var row = 0;
    if (lastRow >= 2) {
      var cell = sheet.getRange(2, 1, lastRow - 1, 1)
        .createTextFinder(String(payload.paymentId))
        .matchEntireCell(true)
        .findNext();
      if (cell) row = cell.getRow();
    }

    if (row && String(sheet.getRange(row, 5).getValue()) === 'SENT') {
      return output_({ ok: true, duplicate: true });
    }

    var amountInr = Number(payload.amountPaise) / 100;
    var values = [
      String(payload.paymentId),
      String(payload.email).trim().toLowerCase(),
      amountInr,
      'सम्पूर्ण आधुनिक भारत का इतिहास PDF',
      'PENDING',
      new Date(),
      String(payload.description || '').slice(0, 250)
    ];
    if (row) {
      sheet.getRange(row, 1, 1, values.length).setValues([values]);
    } else {
      sheet.appendRow(values);
      row = sheet.getLastRow();
    }

    var subject = 'आपकी PDF तैयार है — सम्पूर्ण आधुनिक भारत का इतिहास | Omkar Sir';
    var plainBody =
      'नमस्ते!\n\nआपकी खरीद के लिए धन्यवाद। आपकी PDF डाउनलोड करने के लिए नीचे दिया लिंक खोलें:\n' +
      downloadUrl + '\n\nयह download link समय-सीमित है। समस्या हो तो email2omkara@gmail.com पर संपर्क करें।\n\nOmkar Sir | New India Education';

    var htmlBody =
      '<div style="margin:0;padding:24px 12px;background:#f4f6fb;font-family:Arial,Helvetica,sans-serif;color:#1a2140">' +
      '<div style="max-width:600px;margin:0 auto;background:#ffffff;border:1px solid #e2e7f2;border-radius:18px;overflow:hidden">' +
      '<div style="padding:28px 24px;background:#1b2a6b;color:#ffffff">' +
      '<div style="font-size:13px;letter-spacing:.5px;color:#dfe5ff">NEW INDIA EDUCATION · OMKAR SIR</div>' +
      '<h1 style="font-size:24px;line-height:1.35;margin:12px 0 6px">आपकी PDF तैयार है! 🎉</h1>' +
      '<p style="font-size:15px;line-height:1.6;margin:0;color:#e5eaff">भुगतान के लिए धन्यवाद। नीचे दिए बटन से अपनी PDF डाउनलोड करें।</p>' +
      '</div>' +
      '<div style="padding:26px 24px">' +
      '<h2 style="font-size:20px;line-height:1.5;margin:0 0 8px">सम्पूर्ण आधुनिक भारत का इतिहास</h2>' +
      '<p style="font-size:14px;line-height:1.8;color:#5b6385;margin:0 0 20px">20 अध्याय · 537 पृष्ठ · रंगीन मानचित्र और तालिकाएँ · RAS Pre + Mains एवं State PSC के लिए</p>' +
      '<a href="' + escapeHtml_(downloadUrl) + '" style="display:block;text-align:center;background:#ff6b00;color:#ffffff;text-decoration:none;font-weight:bold;font-size:19px;line-height:1.4;padding:17px 16px;border-radius:12px">⬇️ PDF Download करें</a>' +
      '<p style="font-size:12px;line-height:1.7;color:#6b7280;margin:16px 0 0">सुरक्षा के लिए यह download link सीमित समय तक काम करेगा। इसे अपने निजी अध्ययन के लिए इस्तेमाल करें; आगे साझा न करें।</p>' +
      '<div style="margin-top:22px;padding-top:18px;border-top:1px solid #e8eaf0;font-size:13px;line-height:1.8;color:#5b6385">बटन न खुले? इस लिंक को browser में copy करें:<br><a href="' + escapeHtml_(downloadUrl) + '" style="color:#1b2a6b;word-break:break-all">' + escapeHtml_(downloadUrl) + '</a><br><br>सहायता: <a href="mailto:email2omkara@gmail.com" style="color:#1b2a6b">email2omkara@gmail.com</a></div>' +
      '</div><div style="padding:16px 24px;background:#f8f9fc;color:#6b7280;font-size:12px;line-height:1.6">Omkar Sir · New India Education, Jaipur</div></div></div>';

    GmailApp.sendEmail(String(payload.email).trim().toLowerCase(), subject, plainBody, {
      htmlBody: htmlBody,
      name: 'Omkar Sir | New India Education'
    });
    sheet.getRange(row, 5).setValue('SENT');
    sheet.getRange(row, 6).setValue(new Date());
    return output_({ ok: true, duplicate: false });
  } catch (err) {
    console.error(err && err.stack ? err.stack : err);
    return output_({ ok: false, error: 'Email send/log failed' });
  } finally {
    try { lock.releaseLock(); } catch (_) {}
  }
}

function output_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function emailIsValid_(value) {
  return value.length <= 254 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function constantTimeEqual_(a, b) {
  if (a.length !== b.length) return false;
  var diff = 0;
  for (var i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function escapeHtml_(value) {
  return String(value).replace(/[&<>"']/g, function (ch) {
    return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch];
  });
}
