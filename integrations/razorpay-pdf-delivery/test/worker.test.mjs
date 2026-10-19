// Run: node integrations/razorpay-pdf-delivery/test/worker.test.mjs  (no network; Razorpay, R2 and Apps Script are mocked)
import worker from '../worker.js';
import crypto from 'node:crypto';
const now = Math.floor(Date.now()/1000);
const payments = {
  pay_FRESH1234: {id:'pay_FRESH1234',status:'captured',captured:true,currency:'INR',amount:4900,description:'Rajasthan History PDF',email:'stu@gmail.com',created_at:now-120},
  pay_OLD12345: {id:'pay_OLD12345',status:'captured',captured:true,currency:'INR',amount:4900,description:'Rajasthan History PDF',email:'stu@gmail.com',created_at:now-86400},
  pay_FAIL1234: {id:'pay_FAIL1234',status:'failed',currency:'INR',amount:4900,description:'Rajasthan History PDF',email:'stu@gmail.com',created_at:now},
  pay_MODERN49: {id:'pay_MODERN49',status:'captured',captured:true,currency:'INR',amount:4900,description:'सम्पूर्ण आधुनिक भारत का इतिहास PDF',email:'a@b.com',created_at:now-60},
  pay_P2ABCDEF: {id:'pay_P2ABCDEF',status:'captured',captured:true,currency:'INR',amount:4900,description:'RAS Mains Paper-II PYQ PDF',email:'p@q.com',created_at:now-60},
  pay_WRONGAMT: {id:'pay_WRONGAMT',status:'captured',captured:true,currency:'INR',amount:100,description:'Rajasthan History PDF',email:'stu@gmail.com',created_at:now-60},
};
let emailed=[];
globalThis.fetch = async (url, opts={}) => {
  url=String(url);
  if (url.startsWith('https://api.razorpay.com/v1/payments/')) {
    const id=decodeURIComponent(url.split('/').pop());
    if (opts.headers.authorization !== 'Basic '+btoa('rzp_key:rzp_secret')) return new Response('{}',{status:401});
    return payments[id] ? new Response(JSON.stringify(payments[id])) : new Response('{}',{status:400});
  }
  if (url==='https://script.example/exec') { emailed.push(JSON.parse(opts.body)); return new Response(JSON.stringify({ok:true})); }
  throw new Error('unexpected fetch '+url);
};
const store={'rajasthan-history.pdf':'RJPDF','adhunik.pdf':'ADPDF','p2.pdf':'P2PDF'};
const env = {
  RAZORPAY_WEBHOOK_SECRET:'whsec', DOWNLOAD_SIGNING_SECRET:'dlsec', APPS_SCRIPT_URL:'https://script.example/exec', INTERNAL_SHARED_SECRET:'int',
  PUBLIC_DOWNLOAD_BASE:'https://w.example/download?token=', RAZORPAY_KEY_ID:'rzp_key', RAZORPAY_KEY_SECRET:'rzp_secret',
  ALLOWED_PAYMENT_DESCRIPTIONS:'सम्पूर्ण आधुनिक भारत का इतिहास PDF', PDF_OBJECT_KEY:'adhunik.pdf',
  RAJASTHAN_HISTORY_PAYMENT_DESCRIPTIONS:'Rajasthan History PDF', RAJASTHAN_HISTORY_PDF_OBJECT_KEY:'rajasthan-history.pdf',
  RAS_MAINS_P2_PAYMENT_DESCRIPTIONS:'RAS Mains Paper-II', RAS_MAINS_P2_PDF_OBJECT_KEY:'p2.pdf',
  PDF_BUCKET:{ get: async k => store[k] ? { body: store[k], size: store[k].length, writeHttpMetadata(){} } : null }
};
const O={headers:{origin:'https://omkarsir.com'}};
const call = async (path, init) => { const r = await worker.fetch(new Request('https://w.example'+path, init), env); return [r.status, r.headers, await r.text()]; };
const ok=(c,m)=>{ console.log((c?'PASS ':'FAIL ')+m); if(!c) process.exitCode=1; };
// verify
let [st,h,b]=await call('/verify?payment_id=pay_FRESH1234&product=rajasthan-history-pdf',O); let j=JSON.parse(b);
ok(st===200&&j.ok&&j.downloadUrl.startsWith(env.PUBLIC_DOWNLOAD_BASE)&&h.get('access-control-allow-origin')==='https://omkarsir.com','fresh payment -> download link + CORS');
const token=decodeURIComponent(j.downloadUrl.split('token=')[1]);
[st,h,b]=await call('/download?token='+encodeURIComponent(token)); ok(st===200&&b==='RJPDF'&&/Rajasthan-History/.test(h.get('content-disposition')),'token downloads Rajasthan PDF');
[st,,b]=await call('/download?token='+encodeURIComponent(token.slice(0,-2)+'xx')); ok(st===403,'tampered token rejected');
[st,,b]=await call('/verify?payment_id=pay_OLD12345&product=rajasthan-history-pdf',O); ok(st===401&&JSON.parse(b).error==='email_required'&&JSON.parse(b).emailHint==='st***@gmail.com','old payment needs email');
[st,,b]=await call('/verify?payment_id=pay_OLD12345&product=rajasthan-history-pdf&email=STU@gmail.com',O); ok(st===200&&JSON.parse(b).ok,'old payment + matching email ok');
[st,,b]=await call('/verify?payment_id=pay_OLD12345&product=rajasthan-history-pdf&email=x@y.com',O); ok(st===401,'old payment + wrong email rejected');
[st,,b]=await call('/verify?payment_id=pay_FAIL1234&product=rajasthan-history-pdf',O); ok(st===402,'failed payment rejected');
[st,,b]=await call('/verify?payment_id=pay_FRESH1234&product=adhunik-bharat-itihas-pdf',O); ok(st===403&&JSON.parse(b).error==='wrong_product','other product page rejected');
[st,,b]=await call('/verify?payment_id=pay_WRONGAMT&product=rajasthan-history-pdf',O); ok(st===403,'wrong amount rejected');
[st,,b]=await call('/verify?payment_id=pay_NOPE9999&product=rajasthan-history-pdf',O); ok(st===404,'unknown payment 404');
[st,,b]=await call('/verify?payment_id=abc&product=rajasthan-history-pdf',O); ok(st===400,'bad id 400');
[st,,b]=await call('/verify?payment_id=pay_MODERN49&product=adhunik-bharat-itihas-pdf',O); ok(st===200,'modern history ₹49 accepted');
[st,,b]=await call('/verify?payment_id=pay_P2ABCDEF&product=ras-mains-paper-2-pdf',O); ok(st===200,'paper-2 accepted');
[st,,b]=await call('/verify?payment_id=pay_FRESH1234&product=rajasthan-arthvyavastha-pdf',O); ok(st===403,'economic survey (unconfigured) fails closed');
[st,h]=await call('/verify?payment_id=pay_FRESH1234&product=rajasthan-history-pdf',{headers:{origin:'https://evil.com'}}); ok(!h.get('access-control-allow-origin'),'no CORS for other origins');
// webhook
const sign=body=>crypto.createHmac('sha256','whsec').update(body).digest('hex');
const ev=p=>JSON.stringify({event:'payment.captured',payload:{payment:{entity:p}}});
let body=ev(payments.pay_P2ABCDEF);
[st,,b]=await call('/webhook',{method:'POST',body,headers:{'x-razorpay-signature':sign(body)}}); ok(st===200&&emailed.length===1&&emailed[0].productCode==='ras-mains-paper-2-pdf','webhook emails paper-2 buyer');
[st,,b]=await call('/webhook',{method:'POST',body,headers:{'x-razorpay-signature':'bad'}}); ok(st===401,'bad signature rejected');
body=ev(payments.pay_WRONGAMT);
[st,,b]=await call('/webhook',{method:'POST',body,headers:{'x-razorpay-signature':sign(body)}}); ok(emailed.length===1,'wrong amount not emailed');
delete env.RAZORPAY_KEY_SECRET; [st,,b]=await call('/verify?payment_id=pay_FRESH1234&product=rajasthan-history-pdf',O); ok(st===503,'verify not configured -> 503');
