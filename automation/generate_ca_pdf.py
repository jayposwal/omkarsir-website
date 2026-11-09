#!/usr/bin/env python3
"""
automation/generate_ca_pdf.py

Generates a branded, publication-grade daily Current Affairs PDF matching
the official New India Education / Omkar Sir multi-page layout:
1. Cover Header with navy banner & subheader
2. 'आज की विषय सूची' (Table of Contents) with colored section badges and headline summaries
3. 6 Section Banners (National, International, Economic, Science & Defence, Sports, Rajasthan & Sujas)
4. Pointwise numbered cards with bold keywords and peach '🎯 परीक्षा के लिए:' boxes
5. '📌 परीक्षा हेतु मुख्य तथ्य' two-column takeaway tables at the end of each section
6. Page headers & footers with running page counters (पृष्ठ X / Y)
7. Final page closing callout to the daily online interactive quiz
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
import tempfile
from bs4 import BeautifulSoup

try:
    from weasyprint import HTML
    HAVE_WEASYPRINT = True
except Exception:
    HAVE_WEASYPRINT = False

EMOJI_RE = re.compile(
    "["
    "\U0001F1E0-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F000-\U0001F0FF"
    "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE0F"
    "\U0000200D"
    "]+",
    flags=re.UNICODE,
)

HINDI_MONTHS = {
    1: "जनवरी", 2: "फरवरी", 3: "मार्च", 4: "अप्रैल", 5: "मई", 6: "जून",
    7: "जुलाई", 8: "अगस्त", 9: "सितंबर", 10: "अक्टूबर", 11: "नवंबर", 12: "दिसंबर",
}
HINDI_DAYS = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]


def strip_emoji(text):
    return EMOJI_RE.sub("", text).strip()


SECTIONS_CONFIG = [
    {
        "id": "national",
        "num": 1,
        "icon": "🇮🇳",
        "hindi": "राष्ट्रीय घटनाक्रम",
        "eng": "National",
        "color": "#1B2A6B",
    },
    {
        "id": "international",
        "num": 2,
        "icon": "🌍",
        "hindi": "अंतरराष्ट्रीय घटनाक्रम",
        "eng": "International",
        "color": "#0B7FB3",
    },
    {
        "id": "economic",
        "num": 3,
        "icon": "💰",
        "hindi": "आर्थिक घटनाक्रम",
        "eng": "Economy",
        "color": "#B8860B",
    },
    {
        "id": "science",
        "num": 4,
        "icon": "🔬",
        "hindi": "विज्ञान, रक्षा एवं प्रौद्योगिकी",
        "eng": "Science & Defence",
        "color": "#6A3FB5",
    },
    {
        "id": "sports",
        "num": 5,
        "icon": "🏆",
        "hindi": "खेल, पुरस्कार एवं व्यक्तित्व",
        "eng": "Sports & Awards",
        "color": "#C2185B",
    },
    {
        "id": "rajasthan",
        "num": 6,
        "icon": "🗺️",
        "hindi": "राजस्थान एवं सुजस",
        "eng": "Rajasthan & Sujas",
        "color": "#FF6B00",
    },
]


def extract_data_from_html(html_path):
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Attempt to extract YYYY-MM-DD from canonical or filename
    base = os.path.basename(html_path)
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", base)
    date_str = m.group(1) if m else "2026-11-09"

    y, mo, d = (int(x) for x in date_str.split("-"))
    dt = datetime.date(y, mo, d)
    day_name = HINDI_DAYS[dt.weekday()]
    hindi_date = f"{d} {HINDI_MONTHS[mo]} {y}"

    sections_data = []
    total_items_count = 0
    item_counter = 1

    for conf in SECTIONS_CONFIG:
        sec_id = conf["id"]
        block = soup.find(["section", "div"], id=sec_id)
        if not block and sec_id == "science":
            block = soup.find(["section", "div"], id="sdt")
        if not block and sec_id == "rajasthan":
            block = soup.find(["section", "div"], class_=re.compile(r"raj-sec"))

        if not block:
            continue

        items = []
        cards = block.select("article.card, div.card")
        if cards:
            for card in cards:
                h3 = card.select_one("h3")
                h3_text = h3.get_text().strip() if h3 else ""
                h3_text = strip_emoji(h3_text)

                bullets = []
                for li in card.select("ul li"):
                    b_html = "".join(str(c) for c in li.children)
                    bullets.append(b_html.strip())

                exam = card.select_one(".exam")
                exam_text = ""
                if exam:
                    exam_text = exam.get_text().strip()
                    exam_text = re.sub(r"^🎯\s*(?:परीक्षा\s*के\s*लिए\s*[:：]?)?\s*", "", exam_text)
                    exam_text = strip_emoji(exam_text)

                items.append({
                    "item_num": item_counter,
                    "title": h3_text,
                    "bullets": bullets,
                    "exam": exam_text
                })
                item_counter += 1
        else:
            for item in block.select(".ca-item"):
                p = item.select_one("p")
                if p:
                    b_html = "".join(str(c) for c in p.children)
                    items.append({
                        "item_num": item_counter,
                        "title": "",
                        "bullets": [b_html.strip()],
                        "exam": ""
                    })
                    item_counter += 1

        takeaways = []
        kw_lis = block.select(".kw li")
        if kw_lis:
            for li in kw_lis:
                strong = li.find("strong")
                if strong:
                    key = strong.get_text().strip()
                    val = li.get_text().replace(key, "").strip()
                    val = re.sub(r"^[:：]\s*", "", val)
                    takeaways.append({"key": key, "val": val})
                else:
                    takeaways.append({"key": "तथ्य", "val": li.get_text().strip()})

        total_items_count += len(items)
        sections_data.append({
            "conf": conf,
            "items": items,
            "takeaways": takeaways
        })

    return {
        "date_str": date_str,
        "hindi_date": hindi_date,
        "day_name": day_name,
        "total_items": total_items_count,
        "sections": sections_data
    }


def build_exact_styled_html(data, font_reg, font_bold):
    hindi_date = data["hindi_date"]
    day_name = data["day_name"]
    total_items = data["total_items"]
    date_str = data["date_str"]

    toc_rows_html = []
    for sec in data["sections"]:
        conf = sec["conf"]
        titles = [it["title"] for it in sec["items"] if it["title"]]
        summary_line = " • ".join(titles[:4])
        if len(titles) > 4:
            summary_line += " • आदि"

        row = f"""
        <div class="toc-row">
          <div class="toc-head">
            <span class="toc-badge" style="background:{conf['color']};">{conf['num']}</span>
            <span class="toc-cat-title" style="color:{conf['color']};">{conf['icon']} {conf['hindi']} ({len(sec['items'])})</span>
          </div>
          <div class="toc-summary">{summary_line}</div>
        </div>
        """
        toc_rows_html.append(row)

    sections_html = []
    for sec in data["sections"]:
        conf = sec["conf"]
        banner = f"""
        <div class="sec-banner" style="background:{conf['color']};">
          <div class="sec-banner-left">खंड {conf['num']} &nbsp; {conf['icon']} {conf['hindi']}</div>
          <div class="sec-banner-right">{conf['eng']} • {len(sec['items'])} खबरें</div>
        </div>
        """

        items_html = []
        for it in sec["items"]:
            bullets_li = "".join(f'<li><span class="bullet-dot">•</span><span class="bullet-txt">{b}</span></li>' for b in it["bullets"])
            exam_box = ""
            if it["exam"]:
                exam_box = f"""
                <div class="exam-box">
                  <span class="exam-icon">🎯</span>
                  <span class="exam-label">परीक्षा के लिए:</span> {it['exam']}
                </div>
                """

            card = f"""
            <div class="news-item">
              <div class="item-header">
                <span class="item-circle" style="background:{conf['color']};">{it['item_num']}</span>
                <span class="item-title">{it['title']}</span>
              </div>
              <ul class="item-bullets">
                {bullets_li}
              </ul>
              {exam_box}
            </div>
            """
            items_html.append(card)

        takeaways_html = ""
        if sec["takeaways"]:
            rows = "".join(
                f'<tr><td class="t-key">{t["key"]}</td><td class="t-val">{t["val"]}</td></tr>'
                for t in sec["takeaways"]
            )
            takeaways_html = f"""
            <div class="takeaways-box">
              <div class="takeaways-title">📌 परीक्षा हेतु मुख्य तथ्य</div>
              <table class="takeaways-table">
                {rows}
              </table>
            </div>
            """

        sec_block = f"""
        <div class="section-container">
          {banner}
          <div class="items-list">
            {"".join(items_html)}
          </div>
          {takeaways_html}
        </div>
        """
        sections_html.append(sec_block)

    full_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<title>दैनिक करंट अफेयर्स — {hindi_date}</title>
<style>
@font-face {{
  font-family: 'NotoDeva';
  src: url('{font_reg}');
  font-weight: 400;
}}
@font-face {{
  font-family: 'NotoDeva';
  src: url('{font_bold}');
  font-weight: 700;
}}

@page {{
  size: A4;
  margin: 16mm 12mm 14mm 12mm;
  @top-left {{
    content: "Omkar Sir | New India Education";
    font-family: 'NotoDeva', system-ui, sans-serif;
    font-size: 8pt;
    font-weight: 700;
    color: #1B2A6B;
  }}
  @top-right {{
    content: "दैनिक करंट अफेयर्स — {hindi_date}";
    font-family: 'NotoDeva', system-ui, sans-serif;
    font-size: 8pt;
    font-weight: 700;
    color: #FF6B00;
  }}
  @bottom-left {{
    content: "omkarsir.com";
    font-family: 'NotoDeva', system-ui, sans-serif;
    font-size: 8pt;
    font-weight: 700;
    color: #1B2A6B;
  }}
  @bottom-right {{
    content: "पृष्ठ " counter(page) " / " counter(pages);
    font-family: 'NotoDeva', system-ui, sans-serif;
    font-size: 8pt;
    color: #666666;
  }}
}}

@page:first {{
  @top-left {{ content: none; }}
  @top-right {{ content: none; }}
}}

* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

body {{
  font-family: 'NotoDeva', 'Mukta', 'Noto Sans Devanagari', system-ui, sans-serif;
  color: #1F2937;
  font-size: 9.8pt;
  line-height: 1.55;
  background: #ffffff;
}}

b {{
  font-weight: 700;
  color: #111827;
}}

/* Header Banner Page 1 */
.brand-pill {{
  display: inline-block;
  background: #1B2A6B;
  color: #ffffff;
  padding: 3px 12px;
  border-radius: 4px;
  font-size: 9pt;
  font-weight: 700;
  margin-bottom: 6px;
}}

.hero-box {{
  background: linear-gradient(135deg, #1B2A6B 0%, #20337A 100%);
  color: #ffffff;
  border-radius: 8px;
  padding: 12px 16px;
  text-align: center;
  border-bottom: 3.5px solid #FF6B00;
  margin-bottom: 12px;
}}

.hero-box h1 {{
  font-size: 18pt;
  font-weight: 800;
  margin: 0;
  color: #ffffff;
}}

.hero-box h1 span {{
  color: #FFB070;
}}

.hero-sub {{
  margin-top: 5px;
  font-size: 9.5pt;
  opacity: 0.95;
  font-weight: 600;
  color: #F3F4F6;
}}

/* TOC Box */
.toc-box {{
  background: #FFFDF8;
  border: 1.2px solid #EADCC5;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 14px;
}}

.toc-title {{
  font-size: 11.5pt;
  font-weight: 800;
  color: #1B2A6B;
  border-bottom: 1px solid #FFD2B0;
  padding-bottom: 4px;
  margin-bottom: 8px;
}}

.toc-row {{
  margin-bottom: 6px;
}}

.toc-head {{
  display: flex;
  align-items: center;
  gap: 7px;
}}

.toc-badge {{
  display: inline-block;
  color: #ffffff;
  width: 17px;
  height: 17px;
  border-radius: 3px;
  text-align: center;
  line-height: 17px;
  font-size: 8.5pt;
  font-weight: 800;
}}

.toc-cat-title {{
  font-size: 10pt;
  font-weight: 800;
}}

.toc-summary {{
  font-size: 8.5pt;
  color: #4B5563;
  margin-left: 24px;
  line-height: 1.35;
  margin-top: 1px;
}}

.toc-footer-note {{
  text-align: center;
  font-size: 8pt;
  color: #6B7280;
  border-top: 1px dashed #E5E7EB;
  padding-top: 5px;
  margin-top: 6px;
}}

/* Section Banners */
.sec-banner {{
  color: #ffffff;
  border-radius: 6px;
  padding: 6px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0 10px 0;
  page-break-after: avoid;
  break-after: avoid;
}}

.sec-banner-left {{
  font-size: 11.5pt;
  font-weight: 800;
}}

.sec-banner-right {{
  background: rgba(255, 255, 255, 0.22);
  border-radius: 14px;
  padding: 2px 10px;
  font-size: 8.5pt;
  font-weight: 700;
}}

/* News Item Cards */
.news-item {{
  margin-bottom: 13px;
  page-break-inside: avoid;
  break-inside: avoid;
}}

.item-header {{
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 4px;
}}

.item-circle {{
  display: inline-block;
  color: #ffffff;
  width: 19px;
  height: 19px;
  border-radius: 50%;
  text-align: center;
  line-height: 19px;
  font-size: 9pt;
  font-weight: 800;
  flex-shrink: 0;
  margin-top: 1px;
}}

.item-title {{
  font-size: 11pt;
  font-weight: 800;
  color: #1B2A6B;
  line-height: 1.35;
}}

.item-bullets {{
  margin: 3px 0 5px 27px;
  padding: 0;
  list-style: none;
}}

.item-bullets li {{
  font-size: 9.3pt;
  line-height: 1.48;
  color: #222222;
  margin-bottom: 3px;
  display: flex;
  align-items: flex-start;
}}

.bullet-dot {{
  color: #FF6B00;
  font-weight: bold;
  margin-right: 6px;
  flex-shrink: 0;
  font-size: 11pt;
  line-height: 1.1;
}}

.bullet-txt {{
  flex: 1;
}}

.exam-box {{
  margin-left: 27px;
  background: #FFF5EE;
  border-left: 3.5px solid #FF6B00;
  border-radius: 4px;
  padding: 5px 9px;
  font-size: 8.8pt;
  line-height: 1.45;
  color: #1F2937;
}}

.exam-icon {{
  margin-right: 2px;
}}

.exam-label {{
  font-weight: 800;
  color: #C2410C;
}}

/* Key Takeaways Box */
.takeaways-box {{
  border: 1.2px solid #FFD2B0;
  border-radius: 7px;
  background: #FFFFFF;
  margin: 10px 0 16px 27px;
  padding: 7px 10px;
  page-break-inside: avoid;
  break-inside: avoid;
}}

.takeaways-title {{
  font-size: 9.5pt;
  font-weight: 800;
  color: #C2410C;
  margin-bottom: 5px;
}}

.takeaways-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 8.8pt;
}}

.takeaways-table tr {{
  border-top: 1px solid #F3F4F6;
}}

.takeaways-table tr:first-child {{
  border-top: none;
}}

.t-key {{
  width: 27%;
  padding: 3.5px 5px;
  font-weight: 700;
  color: #1B2A6B;
  vertical-align: top;
}}

.t-val {{
  padding: 3.5px 5px;
  color: #374151;
  line-height: 1.4;
}}

/* Closing Box */
.closing-box {{
  background: #1B2A6B;
  color: #ffffff;
  border-radius: 7px;
  padding: 10px 14px;
  text-align: center;
  margin-top: 18px;
  page-break-inside: avoid;
  break-inside: avoid;
}}

.closing-title {{
  font-size: 10pt;
  font-weight: 700;
}}

.closing-title a {{
  color: #FFB070;
  text-decoration: underline;
}}

.closing-sub {{
  font-size: 8.5pt;
  opacity: 0.88;
  margin-top: 3px;
}}
</style>
</head>
<body>

<div class="brand-pill">🎓 Omkar Sir | New India Education</div>

<div class="hero-box">
  <h1>📰 दैनिक करंट अफेयर्स — <span>{hindi_date}</span></h1>
  <div class="hero-sub">{day_name} • 6 खंड • {total_items} महत्त्वपूर्ण खबरें • UPSC • State PCS • RAS • SSC • पटवार • पुलिस</div>
</div>

<div class="toc-box">
  <div class="toc-title">📑 आज की विषय सूची</div>
  {"".join(toc_rows_html)}
  <div class="toc-footer-note">हर खबर के नीचे 🎯 परीक्षा बिंदु • हर खंड के अंत में मुख्य तथ्य</div>
</div>

{"".join(sections_html)}

<div class="closing-box">
  <div class="closing-title">✍️ पढ़ लिया? अब आज की Quiz दें: <a href="https://omkarsir.com/quiz/{date_str}.html">omkarsir.com/quiz/{date_str}.html</a></div>
  <div class="closing-sub">Omkar Sir | New India Education — प्रतिदिन नए करंट अफेयर्स</div>
</div>

</body>
</html>"""
    return full_html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html_path")
    ap.add_argument("output_pdf")
    ap.add_argument("--hindi-date", required=False)
    ap.add_argument("--eng-date", required=False)
    ap.add_argument("--font-regular", required=False)
    ap.add_argument("--font-bold", required=False)
    ap.add_argument("--site-url", default="omkarsir.com")
    args = ap.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_reg = args.font_regular or os.path.join(repo_root, "automation", "fonts", "NotoMerged-Regular.ttf")
    font_bold = args.font_bold or os.path.join(repo_root, "automation", "fonts", "NotoMerged-Bold.ttf")

    data = extract_data_from_html(args.html_path)
    print(f"Extracted {len(data['sections'])} sections, {data['total_items']} items for {data['hindi_date']}")

    html_str = build_exact_styled_html(data, font_reg, font_bold)

    # 1. Try WeasyPrint first
    if HAVE_WEASYPRINT:
        try:
            HTML(string=html_str, base_url=".").write_pdf(args.output_pdf)
            print("Wrote (via WeasyPrint):", args.output_pdf)
            return
        except Exception as e:
            print(f"WeasyPrint failed ({e}), falling back to Chrome headless...")

    # 2. Chrome headless fallback
    chrome_candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "google-chrome",
        "chromium",
    ]
    chrome_bin = None
    for cand in chrome_candidates:
        if cand.startswith("/") and os.path.exists(cand):
            chrome_bin = cand
            break
        elif not cand.startswith("/"):
            import shutil
            if shutil.which(cand):
                chrome_bin = cand
                break

    if not chrome_bin:
        raise RuntimeError("Neither WeasyPrint nor Google Chrome found for PDF generation.")

    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as tf:
        tf.write(html_str)
        tf_path = tf.name

    try:
        cmd = [
            chrome_bin,
            "--headless",
            "--disable-gpu",
            "--disable-background-networking",
            "--no-pdf-header-footer",
            f"--print-to-pdf={args.output_pdf}",
            tf_path,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if res.returncode != 0:
            raise RuntimeError(f"Chrome PDF generation failed: {res.stderr}")
        print("Wrote (via Chrome headless):", args.output_pdf)
    finally:
        if os.path.exists(tf_path):
            os.remove(tf_path)


if __name__ == "__main__":
    main()
