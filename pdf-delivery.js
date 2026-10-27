/**
 * NIEd paid-PDF delivery page (download-*.html).
 *
 * Razorpay redirects the buyer here with ?razorpay_payment_id=pay_…
 * The page asks the Cloudflare Worker (/verify) to check that payment with
 * Razorpay server-side; only a verified, captured payment for THIS product gets
 * a signed, time-limited download link. No PDF URL is ever stored in this page.
 *
 * After deploying integrations/razorpay-pdf-delivery/worker.js, set WORKER_BASE
 * below to the Worker origin, e.g. "https://omkarsir-pdf-delivery.<you>.workers.dev".
 * While it is empty the page falls back to manual help (WhatsApp/email) so a
 * paying student is never left without a way to get the PDF.
 */
(function () {
  'use strict';

  var WORKER_BASE = 'https://omkarsir-pdf-delivery.omkarsir.workers.dev';
  var HELP_WHATSAPP = '917023166962';
  var HELP_EMAIL = 'email2omkara@gmail.com';

  var root = document.getElementById('pdf-delivery');
  if (!root) return;
  var product = root.getAttribute('data-product');
  var productName = root.getAttribute('data-product-name');

  var $ = function (id) { return document.getElementById(id); };
  var params = new URLSearchParams(location.search);
  var paymentId = (params.get('razorpay_payment_id') || params.get('payment_id') || '').trim();

  function show(state) {
    ['state-checking', 'state-ready', 'state-form', 'state-error', 'state-manual'].forEach(function (id) {
      var el = $(id);
      if (el) el.hidden = (id !== state);
    });
  }

  function helpLinks(pid) {
    var msg = 'नमस्ते Omkar Sir, मैंने "' + productName + '" PDF का भुगतान किया है।' +
      (pid ? ' Payment ID: ' + pid : '') + ' कृपया PDF भेज दें।';
    $('help-wa').href = 'https://wa.me/' + HELP_WHATSAPP + '?text=' + encodeURIComponent(msg);
    $('help-mail').href = 'mailto:' + HELP_EMAIL + '?subject=' + encodeURIComponent('PDF Download सहायता — ' + productName) +
      '&body=' + encodeURIComponent(msg);
  }

  function track(data) {
    if (typeof window.gtag !== 'function' || !data.amountInr) return;
    var key = 'nied_purchase_sent_' + paymentId;
    try { if (sessionStorage.getItem(key)) return; sessionStorage.setItem(key, '1'); } catch (e) {}
    // Server-verified purchase (Worker checked the payment with Razorpay).
    window.gtag('event', 'purchase', {
      transaction_id: paymentId,
      value: Number(data.amountInr),
      currency: 'INR',
      items: [{ item_id: product, item_name: productName, price: Number(data.amountInr), quantity: 1 }]
    });
  }

  var MESSAGES = {
    not_found: 'यह Payment ID नहीं मिला। कृपया Razorpay receipt email से "pay_" से शुरू होने वाला ID ठीक-ठीक copy करें।',
    not_captured: 'यह भुगतान अभी पूरा (captured) नहीं हुआ है। अगर पैसे कट गए हैं तो 5-10 मिनट बाद फिर कोशिश करें।',
    wrong_product: 'यह Payment ID इस PDF का नहीं है। कृपया उसी PDF के download पेज पर जाएँ जिसका भुगतान किया था।',
    bad_request: 'Payment ID सही format में नहीं है। वह "pay_" से शुरू होता है।',
    no_email_on_payment: 'इस भुगतान में email दर्ज नहीं है। कृपया नीचे दिए WhatsApp बटन से संपर्क करें।'
  };

  function verify(email) {
    show('state-checking');
    helpLinks(paymentId);
    var url = WORKER_BASE.replace(/\/$/, '') + '/verify?product=' + encodeURIComponent(product) +
      '&payment_id=' + encodeURIComponent(paymentId) + (email ? '&email=' + encodeURIComponent(email) : '');
    fetch(url, { cache: 'no-store' })
      .then(function (r) { return r.json().catch(function () { return { ok: false, error: 'gateway_error' }; }); })
      .then(function (data) {
        if (data && data.ok) {
          $('dl-btn').href = data.downloadUrl;
          $('ready-email').textContent = data.emailHint || 'आपके email';
          $('ready-pid').textContent = 'Payment ID: ' + paymentId;
          show('state-ready');
          track(data);
          return;
        }
        var err = data && data.error;
        if (err === 'email_required') {
          $('form-note').textContent = 'सुरक्षा के लिए, भुगतान के समय भरा गया email लिखें' +
            (data.emailHint ? ' (' + data.emailHint + ')' : '') + '।';
          $('f-pid').value = paymentId;
          $('f-email-row').hidden = false;
          show('state-form');
          if (email) $('form-error').textContent = 'यह email इस भुगतान से मेल नहीं खाता।';
          return;
        }
        if (err === 'not_configured' || err === 'gateway_unreachable' || err === 'gateway_error') {
          show('state-manual');
          return;
        }
        $('error-text').textContent = MESSAGES[err] || 'कुछ गड़बड़ हुई। कृपया दोबारा कोशिश करें या नीचे से सहायता लें।';
        show('state-error');
      })
      .catch(function () { show('state-manual'); });
  }

  $('verify-form').addEventListener('submit', function (e) {
    e.preventDefault();
    $('form-error').textContent = '';
    var pid = $('f-pid').value.trim();
    var email = $('f-email').value.trim();
    if (!/^pay_[A-Za-z0-9]{6,40}$/.test(pid)) {
      $('form-error').textContent = MESSAGES.bad_request;
      return;
    }
    paymentId = pid;
    try { history.replaceState(null, '', location.pathname + '?razorpay_payment_id=' + encodeURIComponent(pid)); } catch (e2) {}
    verify(email);
  });
  $('retry-btn').addEventListener('click', function () {
    $('f-pid').value = paymentId;
    show('state-form');
  });

  helpLinks(paymentId);
  if (!WORKER_BASE) {
    $('manual-pid').textContent = paymentId ? 'आपका Payment ID: ' + paymentId : '';
    show('state-manual');
  } else if (/^pay_[A-Za-z0-9]{6,40}$/.test(paymentId)) {
    verify('');
  } else {
    show('state-form');
  }
})();
