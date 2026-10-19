#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Builds /ras-mains-paper-3-sample.html (RAS Mains Paper-III PYQ - free sample)
from seo/paper3_data.py. Run:  python3 seo/build_paper3.py

The page is fully server-rendered (answers sit inside <details>), so search
engines read every answer; the small script only adds search / filter / expand.
Set RAZORPAY_BUTTON_ID once the Rs 49 Payment Button exists in the Razorpay
dashboard - until then the buy box shows a "launching soon" state.
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paper3_data import QUESTIONS  # noqa: E402

RAZORPAY_BUTTON_ID = None  # e.g. "pl_XXXXXXXXXXXXXX"
OUT = "ras-mains-paper-3-sample.html"
URL = "https://omkarsir.com/" + OUT
TITLE = "RAS Mains Paper-III PYQ (2013–2024) Answer Key — Free Sample | Omkar Sir"
H1 = "RAS Mains Paper-III PYQ (2013–2024) Answer Key"
DESC = "RPSC RAS Mains Paper-III (सामान्य अध्ययन-III) के 2013–2024 topic-wise PYQ और सरल हिंदी उत्तर। भारतीय संविधान, राजस्थान राजनीति, लोक प्रशासन, व्यवहार और विधि…"
CRED = "पिछले 8 सालों से Rajasthan GK पढ़ाने वाले सबसे Trusted Teacher — 6 लाख+ Students"
TOTAL_Q, TOTAL_PAGES = 306, 140

E = html.escape

SECTIONS = [
    ("इकाई-I", "खण्ड (अ)", "भारतीय संविधान, राजनीतिक व्यवस्था एवं समसामयिकी", "Indian Polity & Current Affairs", "पृष्ठ 1–31"),
    ("इकाई-I", "खण्ड (ब)", "राजस्थान की राज्य-राजनीति एवं स्थानीय स्वशासन", "Rajasthan Polity", "पृष्ठ 32–38"),
    ("इकाई-I", "खण्ड (स)", "अंतरराष्ट्रीय संबंध", "International Relations", "पृष्ठ 39–56"),
    ("इकाई-II", "खण्ड (अ)", "लोक प्रशासन की अवधारणाएं, संगठन के सिद्धांत, प्रबंध व नियंत्रण", "Public Administration Concepts", "पृष्ठ 57–85"),
    ("इकाई-II", "खण्ड (ब)", "राज्य एवं जिला प्रशासन तथा वैधानिक निकाय व अधिनियम", "State Administration & Acts", "पृष्ठ 86–99"),
    ("इकाई-III", "खण्ड (अ)", "खेल एवं योग", "Sports and Yoga", "पृष्ठ 100–109"),
    ("इकाई-III", "खण्ड (ब)", "व्यवहार", "Behaviour", "पृष्ठ 110–124"),
    ("इकाई-III", "खण्ड (स)", "विधि", "Law", "पृष्ठ 125–140"),
]

FAQ = [
    ("यह PDF किस परीक्षा के लिए है?",
     "यह RPSC RAS Mains के Paper-III (सामान्य अध्ययन-III) के वर्ष 2013 से 2024 तक के topic-wise पूर्व वर्ष प्रश्नों की उत्तर-कुंजी है। इसमें 306 प्रश्न, उनके अंक और सरल हिंदी उत्तर हैं।"),
    ("PDF में कौन-कौन से विषय हैं?",
     "भारतीय संविधान एवं राजनीतिक व्यवस्था, राजस्थान की राज्य-राजनीति व स्थानीय स्वशासन, अंतरराष्ट्रीय संबंध, लोक प्रशासन, राज्य व जिला प्रशासन, खेल एवं योग, व्यवहार और विधि।"),
    ("PDF ₹49 में कैसे मिलेगी?",
     "Razorpay से इसी वेबसाइट पर सुरक्षित भुगतान करने के बाद PDF का डाउनलोड लिंक तुरंत मिल जाता है। भुगतान किसी दूसरे ऐप पर नहीं ले जाया जाता।"),
]


def bold(t):
    t = E(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)


def plain(t):
    return re.sub(r"\*+", "", t)


def render_answer(blocks):
    out, in_ul, in_sub = [], False, False

    def close_sub():
        nonlocal in_sub
        if in_sub:
            out.append("</ul>")
            in_sub = False

    def close_ul():
        nonlocal in_ul
        close_sub()
        if in_ul:
            out.append("</li></ul>" if out and out[-1] != "</ul>" else "</ul>")
            in_ul = False

    for b in blocks:
        kind = b[0]
        if kind == "li":
            label, text = b[1], b[2]
            close_sub()
            if in_ul:
                out.append("</li>")
            else:
                out.append('<ul class="pts">')
                in_ul = True
            body = f"<strong>{bold(label)}</strong>" if label else ""
            if text:
                body += (" — " if label else "") + bold(text)
            out.append(f"<li>{body}")
        elif kind == "sub":
            if not in_sub:
                out.append('<ul class="sub">')
                in_sub = True
            out.append(f"<li><strong>{bold(b[1])}</strong> — {bold(b[2])}</li>")
        else:
            close_sub()
            if in_ul:
                out.append("</li></ul>")
                in_ul = False
            if kind == "p":
                out.append(f"<p>{bold(b[1])}</p>")
            elif kind == "h":
                out.append(f'<h3 class="ah">{bold(b[1])}</h3>')
            elif kind == "end":
                out.append(f'<div class="concl"><span>✍️ निष्कर्ष</span><p>{bold(b[1])}</p></div>')
    close_sub()
    if in_ul:
        out.append("</li></ul>")
    return "".join(out)


def card(q):
    keys = "".join(f"<span>{E(k)}</span>" for k in q["keys"])
    share = (f'https://wa.me/?text={E(("RAS Mains Paper-III PYQ प्रश्न %d — " % q["n"]) + URL + "#q%d" % q["n"], quote=True)}')
    marks_cls = {2: "m2", 5: "m5", 10: "m10", 20: "m20"}.get(q["marks"], "m5")
    search_blob = E(" ".join([q["q"], q["en"], q["topic"]] + q["keys"]).lower(), quote=True)
    return f'''<article class="qcard" id="q{q["n"]}" data-marks="{q["marks"]}" data-s="{search_blob}">
  <header class="qtop"><span class="qn">प्रश्न {q["n"]}</span><span class="mk {marks_cls}">{q["marks"]} अंक</span></header>
  <h2 class="qt">{E(q["q"])}</h2>
  <p class="qe" lang="en">{E(q["en"])}</p>
  <p class="qmeta"><span>{E(q["topic"])}</span><span>PDF पृष्ठ {E(q["page"])}</span></p>
  <details class="ans">
    <summary><span class="sl">उत्तर देखें</span><span class="chev" aria-hidden="true">⌄</span></summary>
    <div class="abody">
      <div class="ahead">उत्तर — सरल भाषा में</div>
      {render_answer(q["a"])}
      <div class="kbox"><b>🔑 याद रखने वाले शब्द</b><div class="chips">{keys}</div></div>
      <a class="wa" href="{share}" target="_blank" rel="noopener">WhatsApp पर भेजें ↗</a>
    </div>
  </details>
</article>'''


def section_card(s):
    return (f'<li><span class="u">{E(s[0])} · {E(s[1])}</span><strong>{E(s[2])}</strong>'
            f'<em lang="en">{E(s[3])}</em><span class="pg">{E(s[4])}</span></li>')


def buy_box():
    if RAZORPAY_BUTTON_ID:
        action = ('<div class="buybtn"><form><script src="https://checkout.razorpay.com/v1/payment-button.js" '
                  f'data-payment_button_id="{RAZORPAY_BUTTON_ID}" async></script></form></div>')
    else:
        action = ('<span class="soon">⏳ PDF जल्द उपलब्ध</span>'
                  '<a class="notify" href="https://t.me/omkarsirofficial" target="_blank" rel="noopener">Telegram पर सबसे पहले सूचना पाएँ →</a>')
    return f'''<section class="buy" id="buy" aria-label="पूरी PDF खरीदें">
  <div class="buy-l">
    <span class="eyebrow dark">📘 पूरी PDF</span>
    <h2>{TOTAL_Q} प्रश्न · {TOTAL_PAGES} पृष्ठ · सिर्फ़ ₹49</h2>
    <ul>
      <li>✅ Paper-III के 2013–2024 के सभी topic-wise PYQ</li>
      <li>✅ हर प्रश्न के अंक और सरल हिंदी उत्तर</li>
      <li>✅ 3 इकाई, 8 खण्ड — विषय-वार क्रम में</li>
      <li>✅ Mobile पर offline पढ़ें, print भी निकालें</li>
    </ul>
  </div>
  <div class="buy-r">
    <div class="price"><b>₹49</b><s>₹199</s><em>75% छूट</em></div>
    {action}
    <p class="secure">🔒 Razorpay से सुरक्षित भुगतान · इसी वेबसाइट पर</p>
  </div>
</section>'''


def jsonld():
    qs = [{
        "@type": "Question", "name": q["q"],
        "acceptedAnswer": {"@type": "Answer", "text": " ".join(plain(b[-1]) if b[0] != "li" else plain(b[1] + ": " + b[2]) for b in q["a"])},
    } for q in QUESTIONS]
    data = [
        {
            "@context": "https://schema.org", "@type": "LearningResource",
            "name": H1, "description": DESC, "url": URL, "inLanguage": "hi",
            "learningResourceType": "Previous Year Questions with Answer Key",
            "educationalLevel": "Competitive Examination (RPSC RAS Mains)",
            "isAccessibleForFree": True,
            "about": {"@type": "Thing", "name": "RPSC RAS Mains Paper-III (सामान्य अध्ययन-III)"},
            "provider": {"@type": "EducationalOrganization", "name": "New India Education", "url": "https://omkarsir.com"},
            "author": {"@type": "Person", "name": "Omkar Singh Gurjar", "alternateName": "Omkar Sir",
                       "url": "https://omkarsir.com/about.html"},
            "hasPart": qs,
        },
        {
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "होम", "item": "https://omkarsir.com/"},
                {"@type": "ListItem", "position": 2, "name": "Previous Year Papers", "item": "https://omkarsir.com/previous-year-papers.html"},
                {"@type": "ListItem", "position": 3, "name": "RAS Mains Paper-III PYQ", "item": URL},
            ],
        },
        {
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ],
        },
    ]
    return "\n".join('<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + "</script>" for d in data)


CSS = r"""
:root{--navy:#1B2A6B;--navy2:#2a3d8f;--saf:#FF6B00;--saf-d:#c24f00;--ink:#1f2937;--mut:#5b6478;--line:#e3e7f0;--bg:#f5f7fc;--card:#fff;--tint:#fff4ea;--blue:#eef2ff}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:150px}
body{margin:0;background:var(--bg);color:var(--ink);font-family:'Hind','Noto Sans Devanagari',Arial,sans-serif;font-size:16px;line-height:1.7}
a{color:inherit}
button,input{font:inherit}
.wrap{max-width:980px;margin:0 auto;padding:18px clamp(14px,4vw,30px) 56px}
.back{display:inline-block;margin:2px 0 14px;color:var(--navy);font-size:13px;font-weight:700;text-decoration:none}
.hero{position:relative;overflow:hidden;border-radius:20px;padding:clamp(22px,4.5vw,40px);color:#fff;background:linear-gradient(135deg,var(--navy) 0%,#243887 60%,#31479f 100%);box-shadow:0 14px 34px rgba(27,42,107,.22)}
.hero:before{content:"";position:absolute;right:-90px;top:-90px;width:260px;height:260px;border-radius:50%;border:34px solid rgba(255,107,0,.22)}
.hero:after{content:"";position:absolute;left:0;bottom:0;height:5px;width:100%;background:linear-gradient(90deg,var(--saf),#ffa24d)}
.eyebrow{display:inline-block;padding:5px 12px;border-radius:999px;background:rgba(255,107,0,.18);color:#ffd2ad;border:1px solid rgba(255,160,90,.45);font-size:12px;font-weight:700;letter-spacing:.3px}
.eyebrow.dark{background:var(--tint);color:var(--saf-d);border-color:#ffd3ad}
.hero h1{position:relative;margin:14px 0 10px;font-family:'Hind','Poppins',sans-serif;font-size:clamp(25px,5vw,40px);line-height:1.28;font-weight:700}
.hero h1 span{color:#ffb070}
.hero p.lead{position:relative;margin:0;max-width:680px;color:#dbe2fb;font-size:15.5px;line-height:1.85}
.cred{position:relative;margin:16px 0 0;padding:10px 14px;border-left:4px solid var(--saf);background:rgba(255,255,255,.1);border-radius:0 10px 10px 0;font-size:13.5px;font-weight:600;color:#fff}
.stats{position:relative;display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:20px 0 0}
.stats div{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);border-radius:12px;padding:11px 8px;text-align:center}
.stats b{display:block;font-family:'Poppins',sans-serif;font-size:22px;color:#ffb070;line-height:1.2}
.stats span{font-size:12px;color:#d3dbf6}
.cta{position:relative;display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}
.btn{display:inline-flex;align-items:center;gap:8px;min-height:46px;padding:11px 18px;border-radius:11px;font-size:14px;font-weight:700;text-decoration:none;border:0;cursor:pointer}
.btn.p{background:var(--saf);color:#fff;box-shadow:0 6px 16px rgba(255,107,0,.35)}
.btn.g{background:rgba(255,255,255,.12);color:#fff;border:1px solid rgba(255,255,255,.35)}
.btn:focus-visible,.fb:focus-visible,.ans summary:focus-visible,.notify:focus-visible,#qs:focus-visible{outline:3px solid #ffb070;outline-offset:2px}
.block-h{margin:30px 0 4px;font-size:21px;color:var(--navy);line-height:1.4}
.block-s{margin:0 0 14px;color:var(--mut);font-size:14px}
.secs{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
.secs li{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--saf);border-radius:11px;padding:12px 14px;display:flex;flex-direction:column;gap:2px}
.secs .u{font-size:11.5px;font-weight:700;color:var(--saf-d)}
.secs strong{color:var(--navy);font-size:15px;line-height:1.5}
.secs em{font-style:normal;font-size:12px;color:var(--mut);font-family:'Poppins',sans-serif}
.secs .pg{margin-top:3px;font-size:12px;color:#7a8398}
.tools{position:sticky;top:71px;z-index:20;margin:26px -4px 10px;padding:10px 4px 12px;background:rgba(245,247,252,.96);backdrop-filter:blur(8px)}
.sb{display:flex;align-items:center;gap:8px;background:#fff;border:1.5px solid #d6dcea;border-radius:12px;padding:0 12px;min-height:46px}
.sb:focus-within{border-color:var(--saf);box-shadow:0 0 0 3px rgba(255,107,0,.14)}
#qs{flex:1;min-width:0;border:0;outline:0;background:transparent;font-size:15px;padding:10px 0}
.sb button{border:1px solid #d9dfeb;background:#f6f8fc;border-radius:7px;padding:4px 9px;color:#56627a;font-size:12px;cursor:pointer}
.frow{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:9px}
.fb{border:1px solid #d6dcea;background:#fff;color:#44506b;border-radius:999px;padding:7px 13px;font-size:12.5px;font-weight:700;cursor:pointer}
.fb[aria-pressed=true]{background:var(--navy);border-color:var(--navy);color:#fff}
.fb.x{border-radius:8px;margin-left:auto}
.fb.x+.fb.x{margin-left:0}
.count{margin:8px 2px 12px;font-size:12.5px;color:#6b7489}
.count b{color:var(--navy)}
#list{display:grid;gap:14px}
.qcard{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--navy);border-radius:14px;padding:clamp(15px,3vw,22px);box-shadow:0 3px 12px rgba(27,42,107,.05);scroll-margin-top:150px}
.qcard[hidden]{display:none}
.qtop{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:8px}
.qn{display:inline-block;padding:3px 11px;border-radius:7px;background:var(--navy);color:#fff;font-size:12.5px;font-weight:700}
.mk{padding:3px 11px;border-radius:999px;font-size:12px;font-weight:700;border:1px solid}
.m2{background:#eefaf1;color:#176a35;border-color:#bfe6cb}
.m5{background:var(--tint);color:var(--saf-d);border-color:#ffd3ad}
.m10{background:#fdeef0;color:#a3122a;border-color:#f6c3cb}
.m20{background:#f3e8ff;color:#6b21a8;border-color:#e9d5ff}
.qt{margin:0;font-size:clamp(17.5px,2.4vw,20px);line-height:1.65;color:var(--navy);font-weight:700}
.qe{margin:5px 0 0;font-family:'Poppins',sans-serif;font-size:12.5px;line-height:1.6;color:#7a8398}
.qmeta{display:flex;flex-wrap:wrap;gap:6px;margin:11px 0 0}
.qmeta span{font-size:11.5px;color:#56627a;background:#f2f5fb;border:1px solid #e4e9f3;border-radius:6px;padding:2px 8px}
.ans{margin-top:14px;border:1px solid #c9d5f5;border-radius:11px;background:var(--blue);overflow:hidden}
.ans summary{list-style:none;cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 15px;background:#e3eafd;color:var(--navy);font-weight:700;font-size:15px;user-select:none;min-height:46px}
.ans summary::-webkit-details-marker{display:none}
.ans summary:hover{background:#d9e3fc}
.chev{display:grid;place-items:center;width:26px;height:26px;border-radius:7px;background:#fff;border:1px solid #bccaf0;transition:transform .15s}
.ans[open] .chev{transform:rotate(180deg)}
.abody{padding:16px clamp(13px,3vw,20px) 18px;color:#1f2f63;font-size:15.5px;line-height:1.9}
.ahead{display:inline-block;margin:0 0 10px;padding:3px 10px;border-radius:6px;background:#fff;border:1px solid #c9d5f5;color:var(--navy);font-size:12.5px;font-weight:700}
.abody p{margin:6px 0 10px}
.abody strong{color:var(--navy)}
.ah{margin:16px 0 6px;padding:6px 11px;border-left:4px solid var(--saf);background:#fff;border-radius:0 8px 8px 0;font-size:15.5px;color:var(--navy);line-height:1.6}
.pts,.sub{margin:6px 0 10px;padding:0;list-style:none}
.pts>li{position:relative;margin:7px 0;padding:8px 11px 8px 30px;background:rgba(255,255,255,.75);border:1px solid #d8e2fa;border-radius:9px}
.pts>li:before{content:"▸";position:absolute;left:11px;top:8px;color:var(--saf)}
.sub{margin:6px 0 0}
.sub li{position:relative;margin:5px 0;padding:6px 10px 6px 22px;background:#fff;border:1px solid #e1e8fb;border-radius:7px;font-size:14.5px}
.sub li:before{content:"•";position:absolute;left:9px;color:var(--navy);font-weight:700}
.concl{margin:14px 0 4px;padding:11px 14px;border-radius:10px;background:#fff7ef;border:1px solid #ffd7b5;border-left:5px solid var(--saf)}
.concl span{display:block;font-size:12.5px;font-weight:700;color:var(--saf-d);margin-bottom:2px}
.concl p{margin:0;color:#3b2a16}
.kbox{margin:16px 0 8px;padding:11px 13px;border-radius:10px;background:var(--navy);color:#fff}
.kbox b{display:block;font-size:13px;margin-bottom:7px;color:#ffd2ad}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chips span{padding:3px 10px;border-radius:999px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.28);font-size:12.5px}
.wa{display:inline-block;margin-top:8px;font-size:12.5px;font-weight:700;color:#0f7a3d;text-decoration:none}
.empty{display:none;margin:12px 0;padding:28px 16px;text-align:center;border:1px dashed #cdd5e6;border-radius:12px;background:#fff;color:#6b7489}
.empty.show{display:block}
.more{margin:18px 0 0;padding:16px 18px;border:1px dashed #f0b27a;border-radius:13px;background:#fffaf4;color:#6a4a2a;font-size:14px}
.more b{color:var(--navy)}
.buy{margin:30px 0 0;display:grid;grid-template-columns:1.25fr 1fr;gap:20px;padding:clamp(18px,3.5vw,28px);border-radius:18px;background:#fff;border:2px solid var(--saf);box-shadow:0 12px 30px rgba(255,107,0,.14)}
.buy h2{margin:10px 0 8px;font-size:22px;color:var(--navy);line-height:1.35}
.buy ul{list-style:none;margin:0;padding:0;font-size:14.5px;color:#374151}
.buy li{margin:4px 0}
.buy-r{display:flex;flex-direction:column;justify-content:center;gap:10px;padding:16px;border-radius:14px;background:var(--bg);text-align:center}
.price b{font-family:'Poppins',sans-serif;font-size:42px;color:var(--navy);line-height:1}
.price s{margin:0 8px;color:#8a93a6;font-size:18px}
.price em{font-style:normal;font-size:12px;font-weight:700;color:#176a35;background:#eefaf1;border:1px solid #bfe6cb;border-radius:6px;padding:2px 8px}
.soon{display:block;padding:12px;border-radius:11px;background:#e9edf8;color:var(--navy);font-weight:700}
.notify{display:block;padding:12px;border-radius:11px;background:var(--saf);color:#fff;font-weight:700;text-decoration:none;font-size:14px}
.secure{margin:0;font-size:12px;color:#6b7489}
.faq{margin-top:30px}
.faq details{background:#fff;border:1px solid var(--line);border-radius:11px;margin:8px 0;padding:0 15px}
.faq summary{cursor:pointer;padding:13px 0;font-weight:700;color:var(--navy);min-height:46px}
.faq p{margin:0 0 13px;color:#4b5568;font-size:14.5px}
.note{margin-top:24px;padding:14px 16px;border-radius:11px;background:#fff;border:1px solid var(--line);color:#667086;font-size:12.5px;line-height:1.8}
.foot{margin-top:22px;padding:22px 10px;text-align:center;border-top:1px solid var(--line);color:#8a91a1;font-size:12.5px}
.foot a{color:var(--navy);font-weight:700;text-decoration:none;margin:0 8px}
@media(max-width:700px){
.stats{grid-template-columns:repeat(2,1fr)}
.secs{grid-template-columns:1fr}
.buy{grid-template-columns:1fr}
.fb.x{margin-left:0;flex:1;text-align:center}
.abody{font-size:15px}
.btn{flex:1;justify-content:center}
.tools{position:static;margin:22px 0 8px;padding:0;background:none}
html{scroll-padding-top:140px}
}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
@media print{.tools,.cta,.buy,.wa,#nied-navbar{display:none!important}details.ans>*{display:block!important}}
"""

JS = r"""
(function(){
  var cards=[].slice.call(document.querySelectorAll('.qcard'));
  var s=document.getElementById('qs'),cnt=document.getElementById('cnt'),emp=document.getElementById('emp');
  var fbs=[].slice.call(document.querySelectorAll('.fb[data-m]')),cur='all';
  function run(){
    var t=(s.value||'').trim().toLowerCase(),n=0;
    cards.forEach(function(c){
      var ok=(cur==='all'||c.dataset.marks===cur)&&(!t||c.dataset.s.indexOf(t)>-1||c.textContent.toLowerCase().indexOf(t)>-1);
      c.hidden=!ok;if(ok)n++;
    });
    fbs.forEach(function(b){b.setAttribute('aria-pressed',b.dataset.m===cur?'true':'false');});
    cnt.innerHTML='<b>'+n+'</b> / '+cards.length+' प्रश्न दिख रहे हैं';
    emp.classList.toggle('show',n===0);
  }
  s.addEventListener('input',run);
  document.getElementById('clr').addEventListener('click',function(){s.value='';run();s.focus();});
  fbs.forEach(function(b){b.addEventListener('click',function(){cur=b.dataset.m;run();});});
  document.getElementById('openAll').addEventListener('click',function(){cards.forEach(function(c){if(!c.hidden)c.querySelector('details').open=true;});});
  document.getElementById('closeAll').addEventListener('click',function(){cards.forEach(function(c){c.querySelector('details').open=false;});});
  function fromHash(){
    var m=/^#q(\d+)$/.exec(location.hash);if(!m)return;
    var c=document.getElementById('q'+m[1]);
    if(c){c.querySelector('details').open=true;}
  }
  window.addEventListener('hashchange',fromHash);fromHash();
})();
"""


def build():
    cards = "\n".join(card(q) for q in QUESTIONS)
    counts = {m: sum(1 for q in QUESTIONS if q["marks"] == m) for m in (2, 5, 10, 20)}
    n = len(QUESTIONS)
    secs = "\n".join(section_card(s) for s in SECTIONS)
    faq = "\n".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in FAQ)
    last = QUESTIONS[-1]["n"]
    return f'''<!doctype html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(TITLE)}</title>
<meta name="description" content="{E(DESC, quote=True)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<link rel="canonical" href="{URL}">
<meta name="author" content="Omkar Singh Gurjar">
<meta name="theme-color" content="#1B2A6B">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta property="og:type" content="website">
<meta property="og:title" content="{E(TITLE)}">
<meta property="og:description" content="{E(DESC, quote=True)}">
<meta property="og:url" content="{URL}">
<meta property="og:site_name" content="Omkar Sir | New India Education">
<meta property="og:locale" content="hi_IN">
<meta property="og:image" content="https://omkarsir.com/og-image.png">
<meta property="og:image:alt" content="{E(TITLE)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{E(TITLE)}">
<meta name="twitter:description" content="{E(DESC, quote=True)}">
<meta name="twitter:image" content="https://omkarsir.com/og-image.png">
<meta name="twitter:url" content="{URL}">
<link rel="stylesheet" href="/assets/fonts/gf-9f62de1d.css">
<style>{CSS}</style>
{jsonld()}
<style id="nied-navbar-reserve">#nied-navbar{{min-height:72px}}@media(max-width:520px){{#nied-navbar{{min-height:62px}}}}</style>
</head>
<body>
<div id="nied-navbar"></div>
<main class="wrap">
<a class="back" href="/previous-year-papers.html#block-ras">← सभी Previous Year Papers</a>

<section class="hero">
  <span class="eyebrow">🆓 FREE SAMPLE · प्रश्न 1–{last}</span>
  <h1>RAS Mains <span>Paper-III</span> PYQ (2013–2024) Answer Key</h1>
  <p class="lead">General Studies-III · भारतीय संविधान, राजस्थान राजनीति, लोक प्रशासन, व्यवहार और विधि के topic-wise पूर्व वर्ष प्रश्न — हर प्रश्न के अंक और सरल हिंदी उत्तर के साथ। नीचे पहले {n} प्रश्न मुफ्त पढ़ें।</p>
  <p class="cred">🏆 {CRED}</p>
  <div class="stats">
    <div><b>{TOTAL_Q}</b><span>प्रश्न</span></div>
    <div><b>{TOTAL_PAGES}</b><span>पृष्ठ</span></div>
    <div><b>2013–24</b><span>पूर्व वर्ष</span></div>
    <div><b>8</b><span>खण्ड · 3 इकाई</span></div>
  </div>
  <div class="cta">
    <a class="btn p" href="#buy">📥 पूरी PDF ₹49 में</a>
    <a class="btn g" href="#qs">पहले {n} प्रश्न मुफ्त पढ़ें ↓</a>
  </div>
</section>

<h2 class="block-h">📚 पूरी PDF में क्या-क्या है?</h2>
<p class="block-s">3 इकाई और 8 खण्ड — परीक्षा के पाठ्यक्रम के क्रम में।</p>
<ul class="secs">
{secs}
</ul>

<div id="qarea">
<section class="tools" aria-label="प्रश्न खोजें और फ़िल्टर करें">
  <div class="sb"><span aria-hidden="true">🔍</span><input id="qs" type="search" placeholder="खोजें: जैसे अनुच्छेद 14, OCI, पंथनिरपेक्षता…" aria-label="प्रश्न या विषय खोजें" autocomplete="off"><button type="button" id="clr">साफ़ करें</button></div>
  <div class="frow" role="group" aria-label="अंक के आधार पर फ़िल्टर">
    <button type="button" class="fb" data-m="all" aria-pressed="true">सभी ({n})</button>
    <button type="button" class="fb" data-m="2" aria-pressed="false">2 अंक ({counts[2]})</button>
    <button type="button" class="fb" data-m="5" aria-pressed="false">5 अंक ({counts[5]})</button>
    <button type="button" class="fb" data-m="10" aria-pressed="false">10 अंक ({counts[10]})</button>
    {f'<button type="button" class="fb" data-m="20" aria-pressed="false">20 अंक ({counts[20]})</button>' if counts.get(20, 0) > 0 else ''}
    <button type="button" class="fb x" id="openAll">सभी उत्तर खोलें</button>
    <button type="button" class="fb x" id="closeAll">बंद करें</button>
  </div>
</section>
<div class="count" id="cnt"><b>{n}</b> / {n} प्रश्न दिख रहे हैं</div>

<section id="list" aria-label="RAS Mains Paper-III के प्रश्न और उत्तर">
{cards}
</section>
<div class="empty" id="emp">इस खोज से कोई प्रश्न नहीं मिला। कोई दूसरा keyword लिखकर देखें।</div>
</div>

<div class="more">🔒 <b>आगे के {TOTAL_Q - n} प्रश्न</b> पूरी PDF में हैं — राजस्थान राजनीति, अंतरराष्ट्रीय संबंध, लोक प्रशासन, खेल एवं योग, व्यवहार और विधि। सब कुछ एक ही PDF में, सिर्फ़ ₹49 में।</div>

{buy_box()}

<section class="faq" aria-label="अक्सर पूछे जाने वाले प्रश्न">
  <h2 class="block-h">❓ अक्सर पूछे जाने वाले प्रश्न</h2>
{faq}
</section>

<div class="note"><strong>स्रोत एवं संपादकीय नोट:</strong> ये प्रश्न RPSC RAS Mains Paper-III के 2013–2024 के topic-wise previous-year question compilation (NIEd की उत्तर-कुंजी) पर आधारित हैं। उत्तर सरल हिंदी और क्रमवार बिंदुओं में दिए गए हैं। मूल प्रश्न और आधिकारिक परीक्षा-निर्देशों में किसी अंतर की स्थिति में संबंधित RPSC प्रश्नपत्र को प्राथमिकता दें।</div>

<div class="foot">
  <div><strong>New India Education · Omkar Sir</strong></div>
  <div style="margin-top:8px"><a href="/previous-year-papers.html#block-ras">PYQ Papers</a><a href="/store.html">Premium Notes Store</a><a href="/all-notes.html">Free Notes</a><a href="/contact.html">Contact</a></div>
</div>
</main>
<script src="/nied-menu.js" defer></script>
<script>{JS}</script>
</body>
</html>
'''


if __name__ == "__main__":
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build())
    print("wrote", OUT, len(QUESTIONS), "questions")
