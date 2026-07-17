#!/usr/bin/env python3
"""
Generates a branded, printable PDF from a New India Education daily
Current Affairs HTML page (current-affairs/YYYY-MM-DD.html), for automated
distribution (e.g. Telegram). Uses WeasyPrint (Pango/HarfBuzz) for correct
Devanagari shaping, with a compact half-page cover+index (content starts
on the same first page), numbered pointwise items, running header/footer,
page numbers and a diagonal watermark via CSS Paged Media. Every mention of
"New India Education" links to the app.

Usage: python3 generate_ca_pdf.py <path-to-dated-html> <output-pdf-path> \
           --hindi-date "18 जुलाई 2026" --eng-date "18 July 2026" \
           --font-regular <ttf> --font-bold <ttf>
"""
import argparse
import re
from bs4 import BeautifulSoup
from weasyprint import HTML

APP_LINK = "https://play.google.com/store/apps/details?id=co.april2019.techa"

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


def strip_emoji(text):
    return EMOJI_RE.sub("", text).strip()


SECTION_META = [
    ("national", "राष्ट्रीय", "National", "#1B2A6B"),
    ("international", "अंतर्राष्ट्रीय", "International", "#00A651"),
    ("rajasthan", "राजस्थान", "Rajasthan", "#FF6B00"),
    ("sujas", "सुजस", "Sujas", "#1B2A6B"),
    ("economic", "आर्थिक", "Economic", "#00A651"),
    ("sdt", "विज्ञान-रक्षा-तकनीक", "Science-Defence-Tech", "#FF6B00"),
    ("sports", "खेल-पुरस्कार-व्यक्तित्व", "Sports-Awards", "#1B2A6B"),
]


def extract_sections(html_path):
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    sections = []
    for sec_id, hindi_name, eng_name, color in SECTION_META:
        block = soup.find("div", id=sec_id)
        if not block:
            continue
        items = []
        for item in block.select(".ca-item p"):
            inner = "".join(str(c) for c in item.children)
            inner = re.sub(r"</?p[^>]*>", "", inner)
            items.append(strip_emoji(inner))
        kw = block.select_one(".kw-box")
        kw_text = ""
        if kw:
            kw_text = strip_emoji("".join(str(c) for c in kw.children))
            kw_text = re.sub(r"^\s*[:：]?\s*", "", kw_text)
        sections.append({
            "id": sec_id, "hindi": hindi_name, "eng": eng_name,
            "color": color, "items": items, "kw": kw_text,
        })
    return sections


def build_html(sections, hindi_date, eng_date, font_regular, font_bold, site_url):
    index_rows = "".join(
        f'<div class="idx-row"><span class="dot" style="background:{s["color"]}"></span>{s["hindi"]} ({s["eng"]})</div>'
        for s in sections
    )
    section_html = ""
    for s in sections:
        items_html = "".join(
            f'''<div class="item">
                  <span class="num" style="background:{s["color"]}">{i}</span>
                  <span class="item-text">{it}</span>
                </div>'''
            for i, it in enumerate(s["items"], start=1)
        )
        kw_html = f'<div class="kw">{s["kw"]}</div>' if s["kw"] else ""
        section_html += f'''
        <div class="section">
          <h2 style="border-left-color:{s["color"]}"><span class="dot" style="background:{s["color"]}"></span>{s["hindi"]} <span class="eng">({s["eng"]})</span></h2>
          {items_html}
          {kw_html}
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<style>
@font-face {{ font-family:'Noto'; src:url('{font_regular}'); font-weight:400; }}
@font-face {{ font-family:'Noto'; src:url('{font_bold}'); font-weight:700; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Noto', sans-serif; color:#222; font-size:16px; }}
b {{ font-weight:700; color:#1B2A6B; }}
a {{ color:inherit; text-decoration:none; }}

@page {{
  size: A4;
  margin: 22mm 9mm 16mm 9mm;
  @top-left {{ content: "omkarsir.com"; font-size:9.5px; color:#8a8a94; font-family:'Noto'; }}
  @top-right {{ content: "{eng_date}"; font-size:9.5px; color:#8a8a94; font-family:'Noto'; }}
  @bottom-left {{ content: "omkarsir.com"; font-size:9.5px; color:#8a8a94; font-family:'Noto'; }}
  @bottom-center {{ content: "Page " counter(page) " of " counter(pages); font-size:9.5px; color:#8a8a94; font-family:'Noto'; }}
}}

.footer-brand {{
  position: fixed;
  bottom: 7mm;
  right: 9mm;
  font-size: 9.5px;
  color: #8a8a94;
}}
.footer-brand a {{ text-decoration:underline; }}

.wm {{
  position: fixed;
  top: 46%;
  left: 12%;
  font-size: 42px;
  color: rgba(27,42,107,0.055);
  font-weight: 700;
  transform: rotate(-32deg);
  z-index: -1;
  white-space: nowrap;
}}

.cover {{
  min-height: 125mm;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center; text-align:center;
  border-bottom: 2px solid #E8EAF0;
  padding-bottom: 14px;
  margin-bottom: 16px;
}}
.cover .brand {{ font-size:28px; font-weight:700; color:#1B2A6B; }}
.cover .brand a {{ border-bottom: 1px dotted #1B2A6B; }}
.cover .sub {{ font-size:14px; color:#777; margin-top:3px; }}
.cover .bar {{ width:64px; height:4px; background:linear-gradient(90deg,#FF6B00,#00A651); margin:14px auto; border-radius:4px; }}
.cover h1 {{ font-size:24px; color:#1B2A6B; font-weight:700; margin-top:6px; line-height:1.45; }}
.cover .cred {{ margin-top:12px; font-size:14px; font-weight:700; color:#FF6B00; max-width:500px; }}
.idx-box {{ margin-top:20px; text-align:left; width:420px; border:2px solid #E8EAF0; border-radius:12px; padding:14px 22px; }}
.idx-title {{ font-weight:700; color:#1B2A6B; font-size:16px; border-bottom:2px solid #eee; padding-bottom:8px; margin-bottom:8px; }}
.idx-row {{ font-size:15px; line-height:2.05; }}
.dot {{ display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:8px; }}

.section {{ margin-bottom:16px; }}
.section h2 {{ font-size:19px; color:#1B2A6B; font-weight:700; border-left:4px solid; padding-left:10px; margin-bottom:12px; }}
.section h2 .eng {{ font-size:14px; color:#888; font-weight:400; }}
.item {{ display:flex; gap:10px; font-size:15.5px; line-height:1.85; text-align:justify; margin-bottom:14px; padding-bottom:14px; border-bottom:1px dashed #eee; page-break-inside:avoid; }}
.item:last-of-type {{ border-bottom:none; }}
.num {{ flex:0 0 auto; width:22px; height:22px; border-radius:50%; color:#fff; font-size:12.5px; font-weight:700; text-align:center; line-height:22px; margin-top:1px; }}
.item-text {{ flex:1; }}
.kw {{ background:#FFF3E8; border:1px solid #FFD0A0; border-radius:9px; padding:12px 15px; font-size:13px; line-height:1.7; color:#663c00; margin-top:6px; }}
</style>
</head>
<body>
<div class="wm">NEW INDIA EDUCATION</div>
<div class="footer-brand"><a href="{APP_LINK}">New India Education</a></div>

<div class="cover">
  <div class="brand"><a href="{APP_LINK}">New India Education</a><span style="color:#FF6B00">.</span></div>
  <div class="sub">{site_url} &nbsp;|&nbsp; NIEd</div>
  <div class="bar"></div>
  <h1>{hindi_date}<br>Daily Current Affairs</h1>
  <div class="cred">पिछले 8 सालों से Rajasthan GK पढ़ाने वाले सबसे Trusted Teacher — 6 लाख+ Students</div>
  <div class="idx-box">
    <div class="idx-title">Index — इस PDF में शामिल विषय</div>
    {index_rows}
  </div>
</div>
{section_html}
</body>
</html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html_path")
    ap.add_argument("output_pdf")
    ap.add_argument("--hindi-date", required=True)
    ap.add_argument("--eng-date", required=True)
    ap.add_argument("--font-regular", required=True)
    ap.add_argument("--font-bold", required=True)
    ap.add_argument("--site-url", default="omkarsir.com")
    args = ap.parse_args()

    sections = extract_sections(args.html_path)
    print(f"Extracted {len(sections)} sections, "
          f"{sum(len(s['items']) for s in sections)} total items")
    html_str = build_html(sections, args.hindi_date, args.eng_date,
                           args.font_regular, args.font_bold, args.site_url)
    HTML(string=html_str, base_url=".").write_pdf(args.output_pdf)
    print("Wrote:", args.output_pdf)


if __name__ == "__main__":
    main()
