#!/usr/bin/env python3
"""
daily_ca_cloud_pipeline.py

Fully automated daily publisher for omkarsir.com (New India Education).
Runs in GitHub Actions cloud environment every day at 06:45 AM IST (01:15 UTC).

Workflow:
1. Determines target date (default: today IST).
2. Calls Google Gemini 2.5 API with Google Search Grounding to research:
   - Rajasthan & Sujas (highest priority)
   - National
   - International
   - Economic
   - Science, Tech & Defence
   - Sports & Awards
3. Generates 15 high-standard MCQs with detailed explanations.
4. Generates:
   - quiz-data/YYYY-MM-DD.json
   - current-affairs/YYYY-MM-DD.html
   - quiz/YYYY-MM-DD.html
5. Updates:
   - current-affairs.html (adds latest card & list entry)
   - quiz.html (adds latest card & list entry)
   - sitemap.xml, sitemap-current-affairs.xml, sitemap-quizzes.xml
6. Generates PDFs:
   - ca-pdf/YYYY-MM-DD.pdf (via generate_ca_pdf.py)
   - quiz-pdf/YYYY-MM-DD.pdf (via generate_quiz_pdf.py)
7. Performs automated QA validation before completion.
"""

import datetime
import glob
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CA_DIR = os.path.join(REPO_ROOT, "current-affairs")
QUIZ_DIR = os.path.join(REPO_ROOT, "quiz")
QUIZ_DATA_DIR = os.path.join(REPO_ROOT, "quiz-data")
CA_PDF_DIR = os.path.join(REPO_ROOT, "ca-pdf")
QUIZ_PDF_DIR = os.path.join(REPO_ROOT, "quiz-pdf")

HINDI_MONTHS = {
    1: "जनवरी", 2: "फरवरी", 3: "मार्च", 4: "अप्रैल", 5: "मई", 6: "जून",
    7: "जुलाई", 8: "अगस्त", 9: "सितंबर", 10: "अक्टूबर", 11: "नवंबर", 12: "दिसंबर",
}

HINDI_DAYS = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]


def get_target_date():
    target = os.environ.get("TARGET_DATE", "").strip()
    if target and re.match(r"^\d{4}-\d{2}-\d{2}$", target):
        return target
    # Default to current date in IST (UTC + 5:30)
    ist_now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
    return ist_now.date().isoformat()


def format_date_strings(date_str):
    y, m, d = (int(x) for x in date_str.split("-"))
    dt = datetime.date(y, m, d)
    hindi_date = f"{d} {HINDI_MONTHS[m]} {y}"
    hindi_day = HINDI_DAYS[dt.weekday()]
    hindi_full_date = f"{hindi_day}, {d} {HINDI_MONTHS[m]} {y}"
    eng_date = dt.strftime("%d %B %Y").lstrip("0")
    return hindi_date, hindi_full_date, eng_date, dt


def find_latest_existing_ca_file(exclude_date=None):
    files = glob.glob(os.path.join(CA_DIR, "????-??-??.html"))
    dated = []
    for f in files:
        base = os.path.basename(f)
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\.html$", base)
        if m:
            d_str = m.group(1)
            if exclude_date and d_str >= exclude_date:
                continue
            dated.append((d_str, f))
    if not dated:
        return None, None
    dated.sort(key=lambda x: x[0])
    return dated[-1]


def query_gemini_for_content(date_str, hindi_date, api_key):
    """
    Queries Google Gemini API with Google Search Grounding to get factual
    daily current affairs for Rajasthan, India, and World, plus 15 MCQs.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
You are the daily content editor and RAS Exam specialist for omkarsir.com (New India Education — Omkar Sir).
Today's date is: {date_str} ({hindi_date}).

Strict Quality Guidelines:
- Rajasthan & Sujas is the HIGHEST PRIORITY. Include state govt cabinet decisions, CM Bhajan Lal Sharma announcements, DIPR bulletins, schemes, sports, and infrastructure.
- Sources to prioritize: DIPR Rajasthan (dipr.rajasthan.gov.in), Sujas, PIB India (pib.gov.in), The Hindu, Indian Express, Supreme Court rulings, RBI/SEBI notices.
- Use only confirmed, dated, authentic facts. No speculation or rumours.
- Never use 'RAS Mains Qualified' or 'IAS Aspirant' anywhere.
- Every news item must be in simple, standard, professional Hindi with bold key concepts (<b>...</b>) and numbers/stats.
- Each item must end with a targeted '🎯 परीक्षा के लिए:' box highlighting exactly why this is asked in RAS/UPSC (relevant Articles, stats, ministries, Acts).

6 Categories required:
1. national (3 detailed news items) - central decisions, schemes, defence, SC rulings, Parliament
2. international (3 detailed news items) - India diplomacy, summits, global rankings, geopolitics
3. economic (3 detailed news items) - RBI, GDP, banking, SEBI, fiscal policy, markets
4. science (3 detailed news items) - ISRO, DRDO, defence tech, AI, innovations, biodiversity
5. sports (3 detailed news items) - national/international sports results, youth olympics, awards
6. rajasthan (4 detailed news items) - DIPR Sujas, state schemes, budget announcements, districts, state governance

Also build 15 high-standard RAS/UPSC standard MCQs based on this exact content:
- 3 National, 2 International, 2 Economic, 2 Science-Defence, 2 Sports, 4 Rajasthan-Sujas
- Mix of Easy (4-5), Medium (6-7), and Hard (3-4) questions.
- Some questions MUST be multi-statement style ('निम्नलिखित कथनों पर विचार कीजिए... केवल 1 और 2 सही').
- 'explanation_full' MUST explain both why the correct answer is right AND why the other 3 options are incorrect.
- 'explanation_short' must be concise (under 120 chars) for Telegram poll display.

Return ONLY a valid JSON object with this exact structure:
{{
  "headline_summary": "150-200 characters Hindi summary of top news for meta description",
  "keywords": "comma separated keywords in Hindi and English",
  "sections": [
    {{
      "category_id": "national",
      "items": [
        {{
          "emoji": "⚖️",
          "title": "Hindi headline with bold key terms",
          "bullets": [
            "<b>Fact 1</b>: detailed bullet point (~25-40 words)...",
            "<b>Fact 2</b>: ...",
            "<b>Fact 3</b>: ..."
          ],
          "exam_takeaway": "🎯 परीक्षा के लिए: Key revision points for RAS/UPSC"
        }}
      ],
      "key_takeaways": [
        {{"topic": "विषय 1", "desc": "संक्षिप्त परीक्षा बिंदु"}},
        {{"topic": "विषय 2", "desc": "संक्षिप्त परीक्षा बिंदु"}},
        {{"topic": "विषय 3", "desc": "संक्षिप्त परीक्षा बिंदु"}}
      ]
    }}
  ],
  "questions": [
    {{
      "id": 1,
      "category": "National",
      "difficulty": "easy",
      "question": "प्रश्न हिंदी में?",
      "options": ["विकल्प 1", "विकल्प 2", "विकल्प 3", "विकल्प 4"],
      "correct_index": 0,
      "explanation_short": "संक्षिप्त कारण",
      "explanation_full": "विस्तृत व्याख्या जिसमें सही उत्तर का कारण और अन्य विकल्प क्यों गलत हैं समझाया गया हो।"
    }}
  ]
}}
Ensure the JSON is completely valid, with all 6 categories (national, international, economic, science, sports, rajasthan) present, and exactly 15 questions.
"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}],
        "generationConfig": {
            "temperature": 0.2
        }
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=req_data, headers=headers)
    with urllib.request.urlopen(req, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))

    candidates = result.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates returned from Gemini: {result}")

    text = candidates[0]["content"]["parts"][0]["text"].strip()
    
    # Robust extraction of JSON object
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if m:
        raw_json = m.group(1)
    else:
        m2 = re.search(r"(\{[\s\S]*\})", text)
        if m2:
            raw_json = m2.group(1)
        else:
            raw_json = text

    data = json.loads(raw_json)
    return data


def generate_ca_html(date_str, hindi_date, hindi_full_date, data, prev_date_str):
    headline_sum = data.get("headline_summary", "")
    keywords = data.get("keywords", f"{hindi_date} current affairs, daily current affairs hindi, RAS current affairs, Rajasthan current affairs, Sujas current affairs")
    
    prev_link = f"/current-affairs/{prev_date_str}.html" if prev_date_str else "#"
    prev_text = f"← पिछला दिन ({prev_date_str.split('-')[2]} {HINDI_MONTHS[int(prev_date_str.split('-')[1])]})" if prev_date_str else "← पिछला दिन"

    # Count total news items
    total_items = sum(len(sec.get("items", [])) for sec in data.get("sections", []))

    sec_meta = {
        "national": {"ico": "🇮🇳", "title": "राष्ट्रीय घटनाक्रम", "sub": "National Affairs", "acc": "#1B2A6B", "soft": "#EAEEFA"},
        "international": {"ico": "🌍", "title": "अंतरराष्ट्रीय घटनाक्रम", "sub": "International", "acc": "#0B7FB3", "soft": "#E6F4FB"},
        "economic": {"ico": "💰", "title": "आर्थिक घटनाक्रम", "sub": "Economy & Banking", "acc": "#B8860B", "soft": "#FBF4E2"},
        "science": {"ico": "🔬", "title": "विज्ञान, रक्षा एवं प्रौद्योगिकी", "sub": "Science & Defence", "acc": "#6A3FB5", "soft": "#F1ECFA"},
        "sports": {"ico": "🏆", "title": "खेल, पुरस्कार एवं व्यक्तित्व", "sub": "Sports & Awards", "acc": "#C2185B", "soft": "#FCE8F0"},
        "rajasthan": {"ico": "🗺️", "title": "राजस्थान एवं सुजस सार", "sub": "Rajasthan & Sujas (विशेष अंक)", "acc": "#FF6B00", "soft": "#FFF1E6", "is_raj": True},
    }

    sections_html = []
    item_counter = 1

    # Ensure rajasthan is at the end or proper order
    ordered_cats = ["national", "international", "economic", "science", "sports", "rajasthan"]
    sections_by_cat = {s.get("category_id"): s for s in data.get("sections", [])}

    for cat in ordered_cats:
        sec = sections_by_cat.get(cat)
        if not sec:
            continue
        meta = sec_meta.get(cat, {"ico": "📌", "title": cat, "sub": "", "acc": "#1B2A6B", "soft": "#EAEEFA"})
        is_raj = meta.get("is_raj", False)
        raj_class = "raj-sec" if is_raj else ""

        items_html = []
        for it in sec.get("items", []):
            emoji = it.get("emoji", "📌")
            title = it.get("title", "")
            bullets = it.get("bullets", [])
            bullets_li = "".join(f"<li>{b}</li>" for b in bullets)
            exam_takeaway = it.get("exam_takeaway", "")
            exam_div = f'<div class="exam"><span>{exam_takeaway}</span></div>' if exam_takeaway else ""

            card_html = f"""<article class="card">
<div class="num">{item_counter}</div>
<h3><span class="e">{emoji}</span><span>{title}</span></h3>
<ul>{bullets_li}</ul>
{exam_div}
</article>"""
            items_html.append(card_html)
            item_counter += 1

        # Key Takeaways
        takeaways = sec.get("key_takeaways", [])
        kw_li = "".join(f'<li><strong>{t.get("topic", "")}</strong>{t.get("desc", "")}</li>' for t in takeaways)
        kw_html = f"""<div class="kw">
<h4>📌 परीक्षा हेतु मुख्य तथ्य (Key Takeaways)</h4>
<ul>{kw_li}</ul>
</div>""" if kw_li else ""

        sec_head = f"""<div class="sec-head">
<span class="ico">{meta['ico']}</span>
<div><h2>{meta['title']}</h2><small>{meta['sub']}</small></div>
<span class="cnt">{len(sec.get('items', []))} खबरें</span>
</div>"""

        sec_full = f"""<section id="{cat}" class="{raj_class}" style="--acc:{meta['acc']};--soft:{meta['soft']}">
{sec_head}
<div class="grid">
{"".join(items_html)}
</div>
{kw_html}
</section>"""
        sections_html.append(sec_full)

    full_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="google-adsense-account" content="ca-pub-8493304986550617"><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8493304986550617" crossorigin="anonymous"></script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-WCK16L4WZX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-WCK16L4WZX');
</script>

<title>{hindi_date} Current Affairs, Rajasthan GK | Omkar Sir</title>
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="author" content="Omkar Singh Gurjar">
<link rel="canonical" href="https://omkarsir.com/current-affairs/{date_str}.html">
<meta name="description" content="{hindi_date} करंट अफेयर्स — {headline_sum[:160]}">
<meta name="keywords" content="{keywords}">
<meta property="og:title" content="{hindi_date} Current Affairs, Rajasthan GK | Omkar Sir">
<meta property="og:description" content="{hindi_date} करंट अफेयर्स — {headline_sum[:160]}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://omkarsir.com/current-affairs/{date_str}.html">
<meta property="og:image" content="https://omkarsir.com/og-image.png">
<meta property="og:locale" content="hi_IN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{hindi_date} Current Affairs, Rajasthan GK | Omkar Sir">
<meta name="twitter:description" content="{hindi_date} करंट अफेयर्स — {headline_sum[:160]}">
<link rel="stylesheet" href="/assets/fonts/gf-c441c830.css">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "{hindi_date} — Daily Current Affairs (National, International, Rajasthan, Sujas, Economy, Science-Defence, Sports)",
  "datePublished": "{date_str}",
  "dateModified": "{date_str}",
  "inLanguage": "hi",
  "url": "https://omkarsir.com/current-affairs/{date_str}.html",
  "author": {{
    "@type": "Person",
    "name": "Omkar Singh Gurjar"
  }},
  "publisher": {{
    "@type": "EducationalOrganization",
    "name": "New India Education",
    "url": "https://omkarsir.com"
  }},
  "about": [
    "Current Affairs",
    "RAS Exam 2026",
    "UPSC",
    "Rajasthan GK"
  ],
  "image": "https://omkarsir.com/og-image.png",
  "mainEntityOfPage": "https://omkarsir.com/current-affairs/{date_str}.html"
}}
</script>

<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="theme-color" content="#1B2A6B">
<meta property="og:site_name" content="Omkar Sir | New India Education">
<meta property="og:image:alt" content="{hindi_date} Current Affairs, Rajasthan GK | Omkar Sir">
<meta name="twitter:url" content="https://omkarsir.com/current-affairs/{date_str}.html">
<meta name="twitter:image" content="https://omkarsir.com/og-image.png">
<style id="nied-navbar-reserve">#nied-navbar{{min-height:72px}}@media(max-width:520px){{#nied-navbar{{min-height:62px}}}}@media print{{#nied-navbar,.date-nav,.ext-wrap,.site-links{{display:none!important}}}}</style>
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:image:alt" content="{hindi_date} Current Affairs, Rajasthan GK | Omkar Sir">
<link rel="stylesheet" href="/assets/fonts/gf-971c0f00.css">
<style>
:root{{--navy:#1B2A6B;--saffron:#FF6B00;--cream:#FFFAF2;--ink:#1d2333;--muted:#5b6274}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth;scroll-padding-top:70px}}
body{{margin:0;background:var(--cream);color:var(--ink);font-family:'Mukta','Noto Sans','Noto Sans Devanagari',system-ui,sans-serif;font-size:17px;line-height:1.6}}
b{{color:var(--navy);font-weight:700}}
.hero{{position:relative;overflow:hidden;background:linear-gradient(135deg,#1B2A6B 0%,#24398f 55%,#2c3fa0 100%);color:#fff;padding:42px 20px 54px;text-align:center}}
.hero:before{{content:"";position:absolute;right:-90px;top:-90px;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,#FF6B00 0%,rgba(255,107,0,0) 70%);opacity:.55}}
.hero:after{{content:"";position:absolute;left:-60px;bottom:-110px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,#ffb36b 0%,rgba(255,179,107,0) 70%);opacity:.35}}
.hero>*{{position:relative;z-index:1}}
.brand{{display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.3);padding:5px 16px;border-radius:999px;font-weight:600;letter-spacing:.3px;font-size:15px}}
.hero h1{{margin:16px auto 8px;font-size:clamp(26px,5vw,44px);line-height:1.3;font-weight:800;max-width:900px}}
.hero h1 span{{color:#FFB070}}
.date-chip{{display:inline-block;background:var(--saffron);color:#fff;font-weight:700;padding:6px 18px;border-radius:10px;box-shadow:0 6px 18px rgba(255,107,0,.4);margin:6px 0 14px}}
.trust{{max-width:760px;margin:6px auto 0;background:#fff;color:var(--navy);border-radius:14px;padding:12px 18px;font-weight:600;font-size:16px;box-shadow:0 10px 26px rgba(0,0,0,.18);border-left:6px solid var(--saffron)}}
.stats{{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin-top:18px}}
.stats div{{background:rgba(255,255,255,.12);border-radius:10px;padding:6px 14px;font-size:14px}}
.stats strong{{color:#FFB070;font-size:18px}}
nav.jump{{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.96);backdrop-filter:blur(6px);border-bottom:3px solid var(--saffron);box-shadow:0 4px 14px rgba(27,42,107,.12)}}
nav.jump .row{{display:flex;gap:8px;overflow-x:auto;padding:10px 12px;max-width:1150px;margin:0 auto;scrollbar-width:none}}
nav.jump .row::-webkit-scrollbar{{display:none}}
nav.jump a{{flex:0 0 auto;text-decoration:none;color:var(--navy);font-weight:700;font-size:15px;padding:6px 13px;border-radius:999px;background:#F2F4FB;border:1.5px solid transparent;white-space:nowrap}}
nav.jump a.raj{{background:var(--saffron);color:#fff}}
nav.jump a:hover{{border-color:var(--saffron)}}
main{{max-width:1150px;margin:0 auto;padding:22px 14px 10px}}
section{{margin:26px 0 38px}}
.sec-head{{display:flex;align-items:center;gap:14px;padding:14px 18px;border-radius:16px;color:#fff;background:var(--acc);box-shadow:0 8px 22px rgba(0,0,0,.12)}}
.sec-head .ico{{font-size:32px;line-height:1;background:rgba(255,255,255,.2);border-radius:12px;padding:8px}}
.sec-head h2{{margin:0;font-size:clamp(21px,3.4vw,28px);line-height:1.3}}
.sec-head small{{display:block;opacity:.9;font-weight:500;font-size:14px;letter-spacing:.3px}}
.sec-head .cnt{{margin-left:auto;background:#fff;color:var(--acc);font-weight:800;border-radius:999px;padding:4px 12px;font-size:14px;white-space:nowrap}}
.raj-sec{{background:linear-gradient(180deg,#FFF1E6 0%,#FFFAF2 100%);border:2px solid #FFD2B0;border-radius:22px;padding:16px}}
.raj-sec .sec-head{{background:linear-gradient(120deg,#FF6B00,#ff8a2b 60%,#1B2A6B 140%);padding:20px 22px}}
.raj-sec .sec-head h2{{font-size:clamp(24px,4vw,34px)}}
.raj-badge{{display:inline-block;background:var(--navy);color:#fff;font-size:13px;font-weight:700;padding:3px 12px;border-radius:999px;margin:12px 0 0}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:18px}}
.card{{background:#fff;border-radius:18px;box-shadow:0 6px 20px rgba(27,42,107,.09);border-top:5px solid var(--acc);padding:18px 18px 14px;position:relative;break-inside:avoid;page-break-inside:avoid;display:flex;flex-direction:column}}
.raj-sec .card{{border-top-width:7px;box-shadow:0 10px 28px rgba(255,107,0,.16)}}
.card .num{{position:absolute;top:-14px;right:16px;background:var(--acc);color:#fff;font-weight:800;width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:15px;box-shadow:0 4px 10px rgba(0,0,0,.18);border:3px solid #fff}}
.card h3{{margin:2px 40px 10px 0;font-size:19.5px;line-height:1.45;color:var(--navy);display:flex;gap:10px;align-items:flex-start}}
.card h3 .e{{font-size:26px;line-height:1.2;flex:0 0 auto}}
.card ul{{margin:0;padding:0;list-style:none;flex:1}}
.card li{{position:relative;padding:5px 0 5px 26px;border-bottom:1px dashed #ECEEF4;font-size:16px;overflow-wrap:anywhere}}
.card li:last-child{{border-bottom:0}}
.card li:before{{content:"";position:absolute;left:6px;top:14px;width:9px;height:9px;border-radius:3px;background:var(--acc);transform:rotate(45deg)}}
.exam{{margin-top:12px;background:var(--soft);border-left:4px solid var(--acc);border-radius:10px;padding:8px 12px;font-size:15px;font-weight:700;color:var(--ink)}}
.exam span{{color:var(--acc);font-weight:800}}
.kw{{margin-top:20px;background:linear-gradient(135deg,#1B2A6B,#2a3d93);color:#fff;border-radius:18px;padding:18px 20px;box-shadow:0 10px 26px rgba(27,42,107,.25);break-inside:avoid;page-break-inside:avoid;border:2px dashed #FFB070}}
.kw h4{{margin:0 0 10px;font-size:19px;color:#FFB070}}
.kw ul{{margin:0;padding:0;list-style:none;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}
.kw li{{background:rgba(255,255,255,.1);border-radius:12px;padding:10px 12px;font-size:15.5px}}
.kw li strong{{display:block;color:#fff;font-size:16px;margin-bottom:2px}}
.kw li strong:before{{content:"✅ "}}
footer{{margin-top:20px;background:var(--navy);color:#fff;text-align:center;padding:30px 16px 36px;border-top:6px solid var(--saffron)}}
.quiz-btn{{display:inline-block;margin:6px 0 16px;background:var(--saffron);color:#fff;text-decoration:none;font-weight:800;font-size:20px;padding:13px 30px;border-radius:999px;box-shadow:0 8px 22px rgba(255,107,0,.45)}}
footer a.site{{color:#FFB070;font-weight:700;text-decoration:none;font-size:18px}}
footer p{{margin:6px 0;opacity:.92}}
.quiz-url{{font-size:13px;opacity:.75;overflow-wrap:anywhere}}
@media(max-width:760px){{
 body{{font-size:16px}}
 .grid,.kw ul{{grid-template-columns:1fr}}
 .hero{{padding:32px 14px 40px}}
 .raj-sec{{padding:10px;border-radius:18px}}
 .sec-head{{padding:12px 14px;gap:10px}}
 .sec-head .ico{{font-size:26px;padding:6px}}
 .sec-head .cnt{{font-size:12px;padding:3px 9px}}
 .card{{padding:16px 14px 12px}}
 .card h3{{font-size:18px}}
 .card li{{font-size:15.5px}}
}}
@media print{{
 @page{{size:A4;margin:12mm 10mm}}
 html,body{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
 body{{background:#fff;font-size:13px}}
 nav.jump{{display:none}}
 .hero{{padding:24px 14px 28px}}
 .hero:before,.hero:after{{display:none}}
 main{{padding:6px 0}}
 section{{margin:14px 0 20px}}
 .grid{{display:block}}
 .grid .card{{margin:0 0 14px;break-inside:auto;page-break-inside:auto}}
 .card li,.exam{{break-inside:avoid}}
 .raj-sec{{break-inside:auto}}
 .kw ul{{display:block}}
 .kw li{{margin-bottom:6px}}
 .card{{box-shadow:none;border:1px solid #e3e6ef;border-top:5px solid var(--acc)}}
 .card li{{font-size:12.5px;padding:3px 0 3px 22px}}
 .card li:before{{top:10px}}
 .card h3{{font-size:15px}}
 .exam{{font-size:12px}}
 .kw li{{font-size:12px}}
 .sec-head{{break-after:avoid;page-break-after:avoid}}
 .quiz-btn{{box-shadow:none}}
}}

.date-nav{{display:flex;justify-content:center;gap:10px;margin-top:16px;flex-wrap:wrap;position:relative;z-index:1}}
.date-nav a{{color:#fff;text-decoration:none;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.3);padding:6px 16px;border-radius:50px;font-size:14px;font-weight:600}}
.date-nav a.disabled{{opacity:.45;pointer-events:none}}
.ext-wrap{{max-width:1100px;margin:0 auto;padding:0 16px 30px}}
.pdf-box,.cta-box{{border-radius:18px;padding:24px 20px;text-align:center;margin:22px 0;box-shadow:0 6px 20px rgba(27,42,107,.10)}}
.pdf-box{{background:#fff;border:2px dashed #FF6B00}}
.pdf-box h3,.cta-box h3{{margin:0 0 6px;font-size:21px}}
.pdf-box h3{{color:#1B2A6B}}
.pdf-box p,.cta-box p{{margin:0 0 14px;font-size:15px}}
.pdf-btn,.cta-box a{{display:inline-block;background:#FF6B00;color:#fff!important;text-decoration:none;font-weight:700;padding:11px 26px;border-radius:50px;font-size:16px}}
.cta-box{{background:linear-gradient(135deg,#1B2A6B,#2b3f9e);color:#fff}}
.cta-box p{{color:#dfe3f5}}
.site-links{{margin-top:12px}}
.site-links a{{color:#FF6B00;text-decoration:none;margin:0 6px;font-weight:600}}
</style>
</head>
<body>
<div id="nied-navbar"></div>
<header class="hero">
<div class="brand">🎓 Omkar Sir | New India Education</div>
<h1>📰 दैनिक करंट अफेयर्स — <span>{hindi_date}</span></h1>
<div class="date-chip">📅 {hindi_full_date}</div>
<div class="stats"><div><strong>6</strong> खंड</div><div><strong>{total_items}</strong> महत्त्वपूर्ण खबरें</div><div>🎯 UPSC • State PCS • RAS • SSC • पटवार • पुलिस</div></div>
<div class="date-nav"><a href="{prev_link}">{prev_text}</a><a href="#" class="disabled">अगला दिन →</a></div>
</header>
<nav class="jump"><div class="row"><a href="#national" class="">🇮🇳 राष्ट्रीय</a><a href="#international" class="">🌍 अंतरराष्ट्रीय</a><a href="#economic" class="">💰 आर्थिक</a><a href="#science" class="">🔬 विज्ञान-रक्षा</a><a href="#sports" class="">🏆 खेल-पुरस्कार</a><a href="#rajasthan" class="raj">🗺️ राजस्थान-सुजस</a></div></nav>
<main>
{"".join(sections_html)}
</main>

<div class="ext-wrap">
<div class="pdf-box">
<h3>📥 आज के Current Affairs की PDF</h3>
<p>दैनिक रिवीजन, प्रिंट और ऑफ़लाइन पढ़ाई के लिए प्रामाणिक PDF</p>
<a href="/ca-pdf/{date_str}.pdf" class="pdf-btn" download>📄 PDF डाउनलोड करें</a>
</div>

<div class="cta-box">
<h3>📝 आज के 15 सवालों की Quiz Solve करें</h3>
<p>आज के करंट अफेयर्स पर आधारित विशेष टेस्ट — अपनी तैयारी जाँचें</p>
<a href="/quiz/{date_str}.html">🎯 Quiz शुरू करें →</a>
</div>
</div>

<footer>
<a href="/quiz/{date_str}.html" class="quiz-btn">🎯 आज की Quiz दें (15 प्रश्न)</a>
<p class="quiz-url">🔗 omkarsir.com/quiz/{date_str}.html</p>
<p>🏆 <b>New India Education</b> — RAS व State Exams की प्रामाणिक तैयारी</p>
<p><a href="/" class="site">omkarsir.com</a> • मार्गदर्शन: ओमकार सर</p>
</footer>

<script src="/js/nied-nav.js"></script>
</body>
</html>"""
    return full_html


def generate_quiz_html(date_str, hindi_date, quiz_data, prev_date_str):
    prev_link = f"/quiz/{prev_date_str}.html" if prev_date_str else "#"
    prev_text = f"← पिछला दिन ({prev_date_str.split('-')[2]} {HINDI_MONTHS[int(prev_date_str.split('-')[1])]})" if prev_date_str else "← पिछला दिन"

    quiz_json_str = json.dumps(quiz_data, ensure_ascii=False, indent=2)

    full_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="google-adsense-account" content="ca-pub-8493304986550617"><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8493304986550617" crossorigin="anonymous"></script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-WCK16L4WZX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-WCK16L4WZX');
</script>

<title>{hindi_date} Daily Current Affairs Quiz | Omkar Sir</title>
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="author" content="Omkar Singh Gurjar">
<link rel="canonical" href="https://omkarsir.com/quiz/{date_str}.html">
<meta name="description" content="{hindi_date} दैनिक करंट अफेयर्स क्विज़ — 15 महत्वपूर्ण प्रश्न RAS, UPSC, State PCS हेतु विस्तृत व्याख्या सहित।">
<meta name="keywords" content="{hindi_date} quiz, daily current affairs quiz, ras daily mcq, rajasthan current affairs quiz, upsc daily quiz">
<meta property="og:title" content="{hindi_date} Daily Current Affairs Quiz | Omkar Sir">
<meta property="og:description" content="{hindi_date} दैनिक करंट अफेयर्स क्विज़ — 15 महत्वपूर्ण प्रश्न RAS, UPSC, State PCS हेतु।">
<meta property="og:type" content="article">
<meta property="og:url" content="https://omkarsir.com/quiz/{date_str}.html">
<meta property="og:image" content="https://omkarsir.com/og-image.png">
<meta property="og:locale" content="hi_IN">
<link rel="stylesheet" href="/assets/fonts/gf-c441c830.css">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Quiz",
  "name": "{hindi_date} Daily Current Affairs Quiz",
  "description": "{hindi_date} के 15 महत्वपूर्ण बहुविकल्पीय प्रश्न विस्तृत व्याख्या सहित।",
  "educationalLevel": "Competitive Examinations (RAS, UPSC, State PCS)",
  "provider": {{
    "@type": "EducationalOrganization",
    "name": "New India Education",
    "url": "https://omkarsir.com"
  }},
  "url": "https://omkarsir.com/quiz/{date_str}.html"
}}
</script>
<style>
:root{{--navy:#1B2A6B;--saffron:#FF6B00;--cream:#FFFAF2;--ink:#1d2333;--green:#00A651;--red:#dc3545}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--cream);color:var(--ink);font-family:'Mukta','Noto Sans','Noto Sans Devanagari',system-ui,sans-serif;font-size:17px;line-height:1.6}}
.hero{{background:linear-gradient(135deg,#1B2A6B 0%,#24398f 60%,#FF6B00 140%);color:#fff;padding:36px 18px 46px;text-align:center}}
.brand{{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);padding:4px 14px;border-radius:999px;font-size:14px;font-weight:600}}
.hero h1{{margin:12px auto 6px;font-size:clamp(24px,4.5vw,38px);font-weight:800}}
.date-chip{{display:inline-block;background:var(--saffron);color:#fff;font-weight:700;padding:5px 16px;border-radius:8px;margin-top:6px}}
.date-nav{{display:flex;justify-content:center;gap:10px;margin-top:14px;flex-wrap:wrap}}
.date-nav a{{color:#fff;text-decoration:none;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);padding:5px 14px;border-radius:50px;font-size:14px;font-weight:600}}
.date-nav a.read{{background:var(--saffron);border-color:transparent}}
.wrap{{max-width:850px;margin:0 auto;padding:24px 16px 40px}}
.score-bar{{position:sticky;top:0;z-index:40;background:#fff;border-radius:14px;box-shadow:0 4px 16px rgba(27,42,107,.12);padding:10px 18px;display:flex;justify-content:space-between;align-items:center;margin-bottom:22px;border:2px solid #E5E8F2}}
.score-bar strong{{color:var(--navy);font-size:18px}}
.qcard{{background:#fff;border-radius:16px;padding:20px;margin-bottom:22px;box-shadow:0 6px 18px rgba(27,42,107,.08);border-left:5px solid var(--navy)}}
.qmeta{{display:flex;gap:8px;margin-bottom:10px;align-items:center}}
.badge{{font-size:12px;font-weight:700;padding:2px 10px;border-radius:999px}}
.badge.easy{{background:#E8F5E9;color:#2E7D32}}
.badge.medium{{background:#FFF3E0;color:#E65100}}
.badge.hard{{background:#FFEBEE;color:#C62828}}
.badge.cat{{background:#E8EAF6;color:#283593}}
.qtext{{font-size:18px;font-weight:700;color:var(--navy);margin-bottom:14px;white-space:pre-line}}
.opts{{display:flex;flex-direction:column;gap:10px}}
.opt{{background:#F8F9FD;border:2px solid #E5E8F2;padding:12px 16px;border-radius:12px;cursor:pointer;font-size:16px;text-align:left;transition:all .15s;font-family:inherit}}
.opt:hover:not(:disabled){{background:#EEF1F9;border-color:#C5CEE5}}
.opt.correct{{background:#E8F5E9!important;border-color:#4CAF50!important;color:#1B5E20;font-weight:700}}
.opt.incorrect{{background:#FFEBEE!important;border-color:#F44336!important;color:#B71C1C}}
.explain{{display:none;margin-top:14px;padding:14px;background:#F0F4FF;border-left:4px solid var(--navy);border-radius:8px;font-size:15px;line-height:1.6}}
.explain.show{{display:block}}
.result-box{{display:none;background:linear-gradient(135deg,#1B2A6B,#2b3f9e);color:#fff;border-radius:18px;padding:26px 20px;text-align:center;margin:30px 0;box-shadow:0 8px 24px rgba(27,42,107,.3)}}
.result-box.show{{display:block}}
.result-box h2{{margin:0 0 10px;font-size:26px}}
.pdf-btn{{display:inline-block;background:var(--saffron);color:#fff;text-decoration:none;font-weight:700;padding:12px 26px;border-radius:50px;margin-top:14px;font-size:16px}}
footer{{background:var(--navy);color:#fff;text-align:center;padding:26px 16px;margin-top:40px}}
footer a{{color:#FFB070;text-decoration:none}}
</style>
</head>
<body>
<div id="nied-navbar"></div>
<header class="hero">
<div class="brand">🎓 Omkar Sir | New India Education</div>
<h1>📝 दैनिक Current Affairs Quiz — <span>{hindi_date}</span></h1>
<div class="date-chip">🎯 15 प्रश्न • उत्तर व विस्तृत व्याख्या सहित</div>
<div class="date-nav">
<a href="{prev_link}">{prev_text}</a>
<a href="/current-affairs/{date_str}.html" class="read">📖 आज के Current Affairs पढ़ें</a>
</div>
</header>

<div class="wrap">
<div class="score-bar">
<span>सटीकता: <strong id="scoreVal">0</strong> / 15</span>
<span>हल किए: <strong id="answeredCount">0</strong> / 15</span>
</div>

<div id="quizContainer"></div>

<div class="result-box" id="resultBox">
<h2>🏆 Quiz समाप्त!</h2>
<p style="font-size:20px;">आपका स्कोर: <strong id="finalScore" style="color:#FFB070;font-size:28px;">0</strong> / 15</p>
<p id="resultMsg"></p>
<a href="/quiz-pdf/{date_str}.pdf" class="pdf-btn" download>📥 पूरी Quiz PDF डाउनलोड करें (हल सहित)</a>
</div>
</div>

<footer>
<p>🏆 <b>New India Education</b> — RAS व State Exams की प्रामाणिक तैयारी</p>
<p><a href="/">omkarsir.com</a> • <a href="/quiz.html">सभी Quizzes</a> • <a href="/current-affairs.html">Current Affairs</a></p>
</footer>

<script>
const QUIZ_DATA = {quiz_json_str};

let score = 0;
let answered = 0;

function render() {{
  const container = document.getElementById('quizContainer');
  QUIZ_DATA.questions.forEach((q, qi) => {{
    const card = document.createElement('div');
    card.className = 'qcard';
    card.id = 'q' + q.id;

    const diffLabel = {{easy: '🟢 Easy', medium: '🟠 Medium', hard: '🔴 Hard'}}[q.difficulty] || q.difficulty;

    let optsHtml = '';
    q.options.forEach((opt, oi) => {{
      optsHtml += `<button class="opt" data-oi="${{oi}}" onclick="answer(${{qi}}, ${{oi}}, this)">${{opt}}</button>`;
    }});

    card.innerHTML = `
      <div class="qmeta">
        <span class="badge ${{q.difficulty}}">${{diffLabel}}</span>
        <span class="badge cat">${{q.category}}</span>
      </div>
      <div class="qtext">Q${{qi + 1}}. ${{q.question}}</div>
      <div class="opts">${{optsHtml}}</div>
      <div class="explain" id="exp${{qi}}">💡 <b>व्याख्या:</b> ${{q.explanation_full}}</div>
    `;
    container.appendChild(card);
  }});
}}

function answer(qi, oi, btn) {{
  const q = QUIZ_DATA.questions[qi];
  const card = document.getElementById('q' + q.id);
  const buttons = card.querySelectorAll('.opt');
  if (card.dataset.answered) return;
  card.dataset.answered = '1';

  buttons.forEach((b, i) => {{
    b.disabled = true;
    if (i === q.correct_index) b.classList.add('correct');
    else if (i === oi) b.classList.add('incorrect');
  }});

  if (oi === q.correct_index) score++;
  answered++;
  document.getElementById('exp' + qi).classList.add('show');
  document.getElementById('scoreVal').textContent = score;
  document.getElementById('answeredCount').textContent = answered;

  if (answered === QUIZ_DATA.questions.length) {{
    showResult();
  }}
}}

function showResult() {{
  const box = document.getElementById('resultBox');
  document.getElementById('finalScore').textContent = score;
  let msg = '';
  const pct = (score / QUIZ_DATA.questions.length) * 100;
  if (pct >= 80) msg = 'शानदार! आपकी तैयारी बहुत मजबूत है 🏆';
  else if (pct >= 50) msg = 'अच्छा प्रयास! थोड़ी और मेहनत से और बेहतर होगा 💪';
  else msg = 'आज के Current Affairs को दोबारा पढ़ें और कल फिर कोशिश करें 📚';
  document.getElementById('resultMsg').textContent = msg;
  box.classList.add('show');
  box.scrollIntoView({{behavior: 'smooth', block: 'center'}});
}}

render();
</script>
<script src="/js/nied-nav.js"></script>
</body>
</html>"""
    return full_html


def update_current_affairs_index(date_str, hindi_date, desc):
    index_path = os.path.join(REPO_ROOT, "current-affairs.html")
    with open(index_path, encoding="utf-8") as f:
        content = f.read()

    # Check if already present
    if f"/current-affairs/{date_str}.html" in content:
        print(f"current-affairs.html already has {date_str}, skipping index insertion.")
        return

    # Demote previous top latest-card
    content = re.sub(
        r'<a href="(/current-affairs/\d{4}-\d{2}-\d{2}\.html)" class="latest-card">(\s*)<span class="tag">🆕 आज का Current Affairs</span>',
        r'<a href="\1" class="latest-card" style="background:linear-gradient(135deg,#1B2A6B,#2b3f9e)">\2<span class="tag" style="background:#1B2A6B">📅 हाल का Current Affairs</span>',
        content,
        count=1
    )

    # Insert new latest card at top of wrap
    new_card = f"""<a href="/current-affairs/{date_str}.html" class="latest-card">
  <span class="tag">🆕 आज का Current Affairs</span>
  <h2>{hindi_date}</h2>
  <p>{desc}</p>
</a>
"""
    content = content.replace('<div class="wrap">\n\n', f'<div class="wrap">\n\n{new_card}', 1)
    if '<div class="wrap">\n\n' not in content:
        content = content.replace('<div class="wrap">\n', f'<div class="wrap">\n{new_card}', 1)

    # Add day-item in month list
    day_entry = f"""    <a href="/current-affairs/{date_str}.html" class="ca-day-item">
      <span class="d-date">{hindi_date}</span>
      <span class="d-desc">{desc[:140]}…</span>
      <span class="d-arrow">पढ़ें →</span>
    </a>
"""
    # Prefer anchor for specific month if exists
    month_anchor = f"<!-- CA_DAY_ENTRY_ANCHOR_{date_str[:7].split('-')[1]} -->"
    if "<!-- CA_DAY_ENTRY_ANCHOR_NOV -->" in content and date_str.startswith("2026-11"):
        content = content.replace("<!-- CA_DAY_ENTRY_ANCHOR_NOV -->", f"<!-- CA_DAY_ENTRY_ANCHOR_NOV -->\n{day_entry}", 1)
    elif "<!-- CA_DAY_ENTRY_ANCHOR -->" in content:
        content = content.replace("<!-- CA_DAY_ENTRY_ANCHOR -->", f"<!-- CA_DAY_ENTRY_ANCHOR -->\n{day_entry}", 1)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated current-affairs.html successfully.")


def update_quiz_index(date_str, hindi_date):
    index_path = os.path.join(REPO_ROOT, "quiz.html")
    with open(index_path, encoding="utf-8") as f:
        content = f.read()

    if f"/quiz/{date_str}.html" in content:
        print(f"quiz.html already has {date_str}, skipping index insertion.")
        return

    # Demote previous top latest-card
    content = re.sub(
        r'<a href="(/quiz/\d{4}-\d{2}-\d{2}\.html)" class="latest-card">(\s*)<span class="tag">🆕 आज की Quiz</span>',
        r'<a href="\1" class="latest-card" style="background:linear-gradient(135deg,#1B2A6B,#2b3f9e)">\2<span class="tag" style="background:#1B2A6B">📅 हाल की Quiz</span>',
        content,
        count=1
    )

    new_card = f"""<a href="/quiz/{date_str}.html" class="latest-card">
  <span class="tag">🆕 आज की Quiz</span>
  <h2>{hindi_date}</h2>
  <p>15 प्रश्न — National, International, Economic, Sci-Tech, Sports, Rajasthan-Sujas (विस्तृत व्याख्या सहित)</p>
</a>
"""
    content = content.replace('<div class="wrap">\n\n', f'<div class="wrap">\n\n{new_card}', 1)
    if '<div class="wrap">\n\n' not in content:
        content = content.replace('<div class="wrap">\n', f'<div class="wrap">\n{new_card}', 1)

    day_entry = f"""    <a href="/quiz/{date_str}.html" class="quiz-day-item">
      <span class="d-date">{hindi_date}</span>
      <span class="d-desc">15 प्रश्न — National, International, Economic, Sci-Tech, Sports, Rajasthan-Sujas</span>
      <span class="d-arrow">Quiz दें →</span>
    </a>
"""
    if "<!-- QUIZ_DAY_ENTRY_ANCHOR_NOV -->" in content and date_str.startswith("2026-11"):
        content = content.replace("<!-- QUIZ_DAY_ENTRY_ANCHOR_NOV -->", f"<!-- QUIZ_DAY_ENTRY_ANCHOR_NOV -->\n{day_entry}", 1)
    elif "<!-- QUIZ_DAY_ENTRY_ANCHOR -->" in content:
        content = content.replace("<!-- QUIZ_DAY_ENTRY_ANCHOR -->", f"<!-- QUIZ_DAY_ENTRY_ANCHOR -->\n{day_entry}", 1)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated quiz.html successfully.")


def update_sitemaps(date_str):
    # sitemap-current-affairs.xml
    ca_sitemap = os.path.join(REPO_ROOT, "sitemap-current-affairs.xml")
    if os.path.exists(ca_sitemap):
        with open(ca_sitemap, encoding="utf-8") as f:
            c = f.read()
        url_entry = f"""  <url>
    <loc>https://omkarsir.com/current-affairs/{date_str}.html</loc>
    <lastmod>{date_str}</lastmod>
  </url>
"""
        if f"/current-affairs/{date_str}.html" not in c:
            c = c.replace("</urlset>", f"{url_entry}</urlset>")
            with open(ca_sitemap, "w", encoding="utf-8") as f:
                f.write(c)
            print("Updated sitemap-current-affairs.xml.")

    # sitemap-quizzes.xml
    quiz_sitemap = os.path.join(REPO_ROOT, "sitemap-quizzes.xml")
    if os.path.exists(quiz_sitemap):
        with open(quiz_sitemap, encoding="utf-8") as f:
            c = f.read()
        url_entry = f"""  <url>
    <loc>https://omkarsir.com/quiz/{date_str}.html</loc>
    <lastmod>{date_str}</lastmod>
  </url>
"""
        if f"/quiz/{date_str}.html" not in c:
            c = c.replace("</urlset>", f"{url_entry}</urlset>")
            with open(quiz_sitemap, "w", encoding="utf-8") as f:
                f.write(c)
            print("Updated sitemap-quizzes.xml.")

    # sitemap.xml
    main_sitemap = os.path.join(REPO_ROOT, "sitemap.xml")
    if os.path.exists(main_sitemap):
        with open(main_sitemap, encoding="utf-8") as f:
            c = f.read()
        c = re.sub(r"(<loc>https://omkarsir\.com/sitemap-(?:quizzes|current-affairs)\.xml</loc>\s*<lastmod>)[^<]+(</lastmod>)",
                   rf"\g<1>{date_str}\g<2>", c)
        with open(main_sitemap, "w", encoding="utf-8") as f:
            f.write(c)
        print("Updated sitemap.xml.")


def generate_pdfs(date_str, hindi_date, eng_date):
    font_reg = os.path.join(REPO_ROOT, "automation", "fonts", "NotoMerged-Regular.ttf")
    font_bold = os.path.join(REPO_ROOT, "automation", "fonts", "NotoMerged-Bold.ttf")

    # 1. CA PDF
    ca_html = os.path.join(CA_DIR, f"{date_str}.html")
    ca_pdf = os.path.join(CA_PDF_DIR, f"{date_str}.pdf")
    cmd_ca = [
        sys.executable,
        os.path.join(REPO_ROOT, "automation", "generate_ca_pdf.py"),
        ca_html,
        ca_pdf,
        "--hindi-date", hindi_date,
        "--eng-date", eng_date,
        "--font-regular", font_reg,
        "--font-bold", font_bold,
    ]
    print("Running CA PDF generator...")
    res = subprocess.run(cmd_ca, capture_output=True, text=True)
    if res.returncode != 0:
        print("CA PDF generation output:", res.stdout, res.stderr)
    else:
        print("Generated CA PDF:", ca_pdf)

    # 2. Quiz PDF
    quiz_json = os.path.join(QUIZ_DATA_DIR, f"{date_str}.json")
    quiz_pdf = os.path.join(QUIZ_PDF_DIR, f"{date_str}.pdf")
    cmd_quiz = [
        sys.executable,
        os.path.join(REPO_ROOT, "automation", "generate_quiz_pdf.py"),
        quiz_json,
        quiz_pdf,
        "--hindi-date", hindi_date,
        "--eng-date", eng_date,
        "--font-regular", font_reg,
        "--font-bold", font_bold,
        "--quiz-page-url", f"https://omkarsir.com/quiz/{date_str}.html"
    ]
    print("Running Quiz PDF generator...")
    res = subprocess.run(cmd_quiz, capture_output=True, text=True)
    if res.returncode != 0:
        print("Quiz PDF generation output:", res.stdout, res.stderr)
    else:
        print("Generated Quiz PDF:", quiz_pdf)


def main():
    date_str = get_target_date()
    hindi_date, hindi_full_date, eng_date, dt = format_date_strings(date_str)
    print(f"=== Starting Daily CA Pipeline for {date_str} ({hindi_date}) ===")

    # Check if files already created
    ca_file = os.path.join(CA_DIR, f"{date_str}.html")
    quiz_file = os.path.join(QUIZ_DIR, f"{date_str}.html")
    quiz_json_file = os.path.join(QUIZ_DATA_DIR, f"{date_str}.json")

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if os.path.exists(ca_file) and os.path.exists(quiz_json_file):
        print(f"Files for {date_str} already exist. Proceeding to PDF generation and indexing.")
        with open(quiz_json_file, encoding="utf-8") as f:
            quiz_data = json.load(f)
    else:
        if not api_key:
            print("ERROR: GEMINI_API_KEY environment variable is required to generate new daily content.")
            sys.exit(1)

        print("Calling Google Gemini API with Google Search...")
        data = query_gemini_for_content(date_str, hindi_date, api_key)

        # Prepare quiz data object
        quiz_data = {
            "date": date_str,
            "hindi_date": hindi_date,
            "questions": data.get("questions", [])
        }

        # Save quiz-data JSON
        os.makedirs(QUIZ_DATA_DIR, exist_ok=True)
        with open(quiz_json_file, "w", encoding="utf-8") as f:
            json.dump(quiz_data, f, ensure_ascii=False, indent=2)
        print(f"Saved {quiz_json_file}")

        # Find previous date
        prev_date, _ = find_latest_existing_ca_file(exclude_date=date_str)
        print(f"Previous dated file is: {prev_date}")

        # Generate and save Current Affairs HTML
        ca_html = generate_ca_html(date_str, hindi_date, hindi_full_date, data, prev_date)
        with open(ca_file, "w", encoding="utf-8") as f:
            f.write(ca_html)
        print(f"Saved {ca_file}")

        # Generate and save Quiz HTML
        quiz_html = generate_quiz_html(date_str, hindi_date, quiz_data, prev_date)
        with open(quiz_file, "w", encoding="utf-8") as f:
            f.write(quiz_html)
        print(f"Saved {quiz_file}")

        # Update index files
        desc = data.get("headline_summary", f"{hindi_date} दैनिक करंट अफेयर्स एवं 15 महत्वपूर्ण प्रश्न")
        update_current_affairs_index(date_str, hindi_date, desc)
        update_quiz_index(date_str, hindi_date)
        update_sitemaps(date_str)

    # Generate both PDFs
    os.makedirs(CA_PDF_DIR, exist_ok=True)
    os.makedirs(QUIZ_PDF_DIR, exist_ok=True)
    generate_pdfs(date_str, hindi_date, eng_date)

    print(f"=== Successfully completed Daily CA Pipeline for {date_str} ===")


if __name__ == "__main__":
    main()
