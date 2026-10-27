// Run: node integrations/razorpay-pdf-delivery/test/worker.test.mjs  (no network; Razorpay, R2/KV/GitHub storage and Apps Script are mocked)
import worker from '../worker.js';
import crypto from 'node:crypto';
const now = Math.floor(Date.now()/1000);
const payments = {
  pay_FRESH1234: {id:'pay_FRESH1234',status:'captured',captured:true,currency:'INR',amount:4900,description:'Rajasthan History PDF',email:'stu@gmail.com',created_at:now-120},
  pay_OLD12345: {id:'pay_OLD12345',status:'captured',captured:true,currency:'INR',amount:4900,description:'Rajasthan History PDF',email:'stu@gmail.com',created_at:now-86400},
  pay_FAIL1234: {id:'pay_FAIL1234',status:'failed',currency:'INR',amount:4900,description:'Rajasthan History PDF',email:'stu@gmail.com',created_at:now},
  pay_MODERN49: {id:'pay_MODERN49',status:'captured',captured:true,currency:'INR',amount:4900,description:'सम्पूर्ण आधुनिक भारत का इतिहास PDF',email:'a@b.com',created_at:now-60},
  pay_P2ABCDEF: {id:'pay_P2ABCDEF',status:'captured',captured:true,currency:'INR',amount:4900,description:'RAS Mains Paper-II PYQ PDF',email:'p@q.com',created_at:now-60},
  pay_BTNADH49: {id:'pay_BTNADH49',status:'captured',captured:true,currency:'INR',amount:4900,description:'#Tmzqpr6RIRGU0K',order_id:'order_AAAAAA1',email:'b@c.com',created_at:now-60},
  pay_BTNRJH49: {id:'pay_BTNRJH49',status:'captured',captured:true,currency:'INR',amount:4900,description:'#TpCUODSwC6kIR9',order_id:'order_AAAAAA2',email:'r@h.com',created_at:now-60},
  pay_BTNNOTES: {id:'pay_BTNNOTES',status:'captured',captured:true,currency:'INR',amount:4900,description:'',notes:{payment_button:'pl_TmyJkDLHXDE2N3',email:'n@o.com'},email:'n@o.com',created_at:now-60},
  pay_BTNORDER: {id:'pay_BTNORDER',status:'captured',captured:true,currency:'INR',amount:4900,description:'',order_id:'order_VIABUTTON',notes:[],email:'o@r.com',created_at:now-60},
  pay_BTNBADAM: {id:'pay_BTNBADAM',status:'captured',captured:true,currency:'INR',amount:100,description:'#TpCUODSwC6kIR9',email:'r@h.com',created_at:now-60},
  pay_AMBIGUOU: {id:'pay_AMBIGUOU',status:'captured',captured:true,currency:'INR',amount:4900,description:'PDF',email:'x@y.com',created_at:now-60},
  pay_UNRELATD: {id:'pay_UNRELATD',status:'captured',captured:true,currency:'INR',amount:4900,description:'#ZZZZZZZZZZZZZZ',order_id:'order_UNRELATED',email:'u@v.com',created_at:now-60},
  pay_WRONGAMT: {id:'pay_WRONGAMT',status:'captured',captured:true,currency:'INR',amount:100,description:'Rajasthan History PDF',email:'stu@gmail.com',created_at:now-60},
};
let emailed=[]; const githubCalls=[];
globalThis.fetch = async (url, opts={}) => {
  url=String(url);
  if (url.startsWith('https://api.razorpay.com/v1/payments/')) {
    const id=decodeURIComponent(url.split('/').pop());
    if (opts.headers.authorization !== 'Basic '+btoa('rzp_key:rzp_secret')) return new Response('{}',{status:401});
    return payments[id] ? new Response(JSON.stringify(payments[id])) : new Response('{}',{status:400});
  }
  if (url.startsWith('https://api.razorpay.com/v1/orders/')) {
    const id=decodeURIComponent(url.split('/').pop());
    if (id==='order_VIABUTTON') return new Response(JSON.stringify({id,entity:'order',receipt:null,notes:{payment_page:'pl_TmyJkDLHXDE2N3'}}));
    return new Response(JSON.stringify({id,entity:'order',notes:[]}));
  }
  if (url.startsWith('https://api.github.com/repos/')) {
    githubCalls.push({url,headers:opts.headers});
    if (opts.headers.authorization!=='Bearer ghtok' || opts.headers.accept!=='application/vnd.github.raw+json') return new Response('{}',{status:401});
    const u=new URL(url); const path=decodeURIComponent(u.pathname.replace('/repos/owner/private-pdfs/contents/',''));
    const files={'pdfs/rajasthan-history.pdf':'GHPDF'};
    return files[path] && u.searchParams.get('ref')==='main' ? new Response(files[path],{headers:{'content-length':'5'}}) : new Response('{"message":"Not Found"}',{status:404});
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

// ---- product identification by Razorpay payment button ID ----
[st,,b]=await call('/verify?payment_id=pay_BTNADH49&product=adhunik-bharat-itihas-pdf',O); ok(st===200&&JSON.parse(b).product==='adhunik-bharat-itihas-pdf','button id in description (#suffix) -> modern history');
[st,,b]=await call('/verify?payment_id=pay_BTNRJH49&product=rajasthan-history-pdf',O); ok(st===200,'rajasthan history button id -> rajasthan history');
[st,,b]=await call('/verify?payment_id=pay_BTNRJH49&product=adhunik-bharat-itihas-pdf',O); ok(st===403&&JSON.parse(b).error==='wrong_product','rajasthan button cannot unlock modern history (same ₹49)');
[st,,b]=await call('/verify?payment_id=pay_BTNNOTES&product=ras-mains-paper-2-pdf',O); ok(st===200,'button id in payment.notes -> paper-2');
[st,,b]=await call('/verify?payment_id=pay_BTNORDER&product=ras-mains-paper-2-pdf',O); ok(st===200,'button id only in order notes (API lookup) -> paper-2');
[st,,b]=await call('/verify?payment_id=pay_BTNBADAM&product=rajasthan-history-pdf',O); ok(st===403,'right button but wrong amount rejected');
[st,,b]=await call('/verify?payment_id=pay_UNRELATD&product=rajasthan-history-pdf',O); ok(st===403,'unrelated button/payment rejected');
{ const e2={...env, RAJASTHAN_HISTORY_PAYMENT_DESCRIPTIONS:'PDF', RAS_MAINS_P2_PAYMENT_DESCRIPTIONS:'PDF'};
  const r=await worker.fetch(new Request('https://w.example/verify?payment_id=pay_AMBIGUOU&product=rajasthan-history-pdf',O),e2); ok(r.status===403,'ambiguous description match fails closed'); }
{ const e2={...env, RAJASTHAN_HISTORY_BUTTON_IDS:'pl_NEWBUTTON12345'};
  const r=await worker.fetch(new Request('https://w.example/verify?payment_id=pay_BTNRJH49&product=rajasthan-history-pdf',O),e2); ok(r.status===403,'button IDs overridable via env (old id no longer accepted)'); }
body=ev(payments.pay_BTNRJH49);
[st,,b]=await call('/webhook',{method:'POST',body,headers:{'x-razorpay-signature':sign(body)}}); ok(st===200&&emailed.at(-1).productCode==='rajasthan-history-pdf'&&emailed.at(-1).email==='r@h.com','webhook: button id -> Rajasthan History email');
body=ev(payments.pay_UNRELATD); const before=emailed.length;
[st,,b]=await call('/webhook',{method:'POST',body,headers:{'x-razorpay-signature':sign(body)}}); ok(st===200&&emailed.length===before,'webhook: unrelated payment not emailed');

// ---- storage backends ----
const tokenFor=async (e)=>{ const r=await worker.fetch(new Request('https://w.example/verify?payment_id=pay_BTNRJH49&product=rajasthan-history-pdf',O),e); const j=await r.json(); return decodeURIComponent(j.downloadUrl.split('token=')[1]); };
const dl=async (e,t)=>{ const r=await worker.fetch(new Request('https://w.example/download?token='+encodeURIComponent(t)),e); return [r.status,r.headers,await r.text()]; };
{ const kvStore={'rajasthan-history.pdf':{v:'KVPDF',m:{size:5}}};
  const e2={...env}; delete e2.PDF_BUCKET; e2.PDF_KV={get:async()=>null,getWithMetadata:async(k,o)=>kvStore[k]?{value:kvStore[k].v,metadata:kvStore[k].m}:{value:null,metadata:null}};
  const t=await tokenFor(e2); const [s1,h1,b1]=await dl(e2,t); ok(s1===200&&b1==='KVPDF'&&h1.get('content-length')==='5'&&h1.get('content-type')==='application/pdf','KV backend serves PDF (with size metadata)');
  e2.RAJASTHAN_HISTORY_PDF_OBJECT_KEY='missing.pdf'; const [s2]=await dl(e2,t); ok(s2===503,'KV backend missing key -> 503'); }
{ const e2={...env, GITHUB_PDF_REPO:'owner/private-pdfs', GITHUB_PDF_TOKEN:'ghtok', GITHUB_PDF_PATH_PREFIX:'pdfs'}; delete e2.PDF_BUCKET;
  const t=await tokenFor(e2); const [s1,h1,b1]=await dl(e2,t);
  ok(s1===200&&b1==='GHPDF'&&/Rajasthan-History/.test(h1.get('content-disposition'))&&h1.get('cache-control').includes('no-store'),'GitHub private-repo backend serves PDF');
  ok(githubCalls.at(-1).url==='https://api.github.com/repos/owner/private-pdfs/contents/pdfs/rajasthan-history.pdf?ref=main'&&githubCalls.at(-1).headers['user-agent'],'GitHub request: contents API, raw media type, ref, user-agent');
  const [s2]=await dl({...e2,GITHUB_PDF_TOKEN:'wrong'},t); ok(s2===503,'GitHub auth failure -> 503 (no leak)');
  const [s3]=await dl({...e2,RAJASTHAN_HISTORY_PDF_OBJECT_KEY:'../secret.pdf'},t); ok(s3===503,'path traversal object key refused');
  const [s4,,b4]=await dl({...e2,PDF_BUCKET:env.PDF_BUCKET},t); ok(s4===200&&b4==='RJPDF','R2 wins when both R2 and GitHub configured');
  const [s5,,b5]=await dl({...e2,PDF_BUCKET:env.PDF_BUCKET,STORAGE_BACKEND:'github'},t); ok(s5===200&&b5==='GHPDF','STORAGE_BACKEND forces GitHub');
  const [s6]=await dl({...e2,STORAGE_BACKEND:'kv'},t); ok(s6===503,'forced backend not bound -> 503'); }
{ const e2={...env}; delete e2.PDF_BUCKET; const t=await tokenFor({...env}); const [s1]=await dl(e2,t); ok(s1===503,'no storage configured -> 503'); }

delete env.RAZORPAY_KEY_SECRET; [st,,b]=await call('/verify?payment_id=pay_FRESH1234&product=rajasthan-history-pdf',O); ok(st===503,'verify not configured -> 503');
