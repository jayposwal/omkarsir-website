#!/usr/bin/env python3
"""
Generates a branded, printable PDF from a New India Education daily
Current Affairs HTML page (current-affairs/YYYY-MM-DD.html), for automated
distribution (e.g. Telegram). Uses WeasyPrint (Pango/HarfBuzz) for correct
Devanagari shaping, with a cover+index page, running header/footer,
page numbers and a diagonal watermark via CSS Paged Media.

Usage: python3 generate_ca_pdf.py <path-to-dated-html> <output-pdf-path> \
           --hindi-date "18 जुलाई 2026" --eng-date "18 July 2026" \
           --font-regular <ttf> --font-bold <ttf>
"""
import argparse
import re
from bs4 import BeautifulSoup
from weasyprint import HTML

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
            # Keep <b> tags, strip everything else (drop nested tags' other attrs)
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
        items_html = "".join(f'<div class="item">{it}</div>' for it in s["items"])
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
body {{ font-family:'Noto', sans-serif; color:#222; font-size:11.5px; }}
b {{ font-weight:700; color:#1B2A6B; }}

@page {{
  size: A4;
  margin: 24mm 14mm 18mm 14mm;
  @top-left {{ content: "omkarsir.com  |  New India Education"; font-size:8px; color:#8a8a94; font-family:'Noto'; }}
  @top-right {{ content: "{eng_date}"; font-size:8px; color:#8a8a94; font-family:'Noto'; }}
  @bottom-left {{ content: "omkarsir.com"; font-size:8px; color:#8a8a94; font-family:'Noto'; }}
  @bottom-center {{ content: "Page " counter(page) " of " counter(pages); font-size:8px; color:#8a8a94; font-family:'Noto'; }}
  @bottom-right {{ content: "New India Education"; font-size:8px; color:#8a8a94; font-family:'Noto'; }}
}}
@page cover {{ margin:0; }}

.cover {{
  page: cover; height:297mm; display:flex; flex-direction:column;
  align-items:center; justify-content:center; text-align:center;
  page-break-after: always;
}}
.cover .brand {{ font-size:28px; font-weight:700; color:#1B2A6B; }}
.cover .sub {{ font-size:12px; color:#777; margin-top:4px; }}
.cover .bar {{ width:70px; height:4px; background:linear-gradient(90deg,#FF6B00,#00A651); margin:22px auto; border-radius:4px; }}
.cover h1 {{ font-size:24px; color:#1B2A6B; font-weight:700; margin-top:6px; line-height:1.5; }}
.cover .cred {{ margin-top:16px; font-size:11.5px; font-weight:700; color:#FF6B00; max-width:480px; }}
.idx-box {{ margin-top:44px; text-align:left; width:400px; border:2px solid #E8EAF0; border-radius:12px; padding:20px 26px; }}
.idx-title {{ font-weight:700; color:#1B2A6B; font-size:14px; border-bottom:2px solid #eee; padding-bottom:9px; margin-bottom:10px; }}
.idx-row {{ font-size:12.5px; line-height:2.1; }}
.dot {{ display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:8px; }}
.cover .footnote {{ margin-top:40px; font-size:9.5px; color:#aaa; max-width:420px; }}

.section {{ margin-bottom:14px; page-break-inside:avoid; }}
.section h2 {{ font-size:14.5px; color:#1B2A6B; font-weight:700; border-left:4px solid; padding-left:10px; margin-bottom:8px; }}
.section h2 .eng {{ font-size:11px; color:#888; font-weight:400; }}
.item {{ font-size:11px; line-height:1.65; text-align:justify; margin-bottom:8px; padding-bottom:8px; border-bottom:1px dashed #eee; }}
.item:last-of-type {{ border-bottom:none; }}
.kw {{ background:#FFF3E8; border:1px solid #FFD0A0; border-radius:8px; padding:8px 12px; font-size:9.5px; color:#663c00; margin-top:6px; }}

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
</style>
</head>
<body>
<div class="wm">NEW INDIA EDUCATION</div>
<div class="cover">
  <div class="brand">New India Education<span style="color:#FF6B00">.</span></div>
  <div class="sub">{site_url} &nbsp;|&nbsp; NIEd</div>
  <div class="bar"></div>
  <h1>{hindi_date}<br>Daily Current Affairs</h1>
  <div class="cred">पिछले 8 सालों से Rajasthan GK पढ़ाने वाले सबसे Trusted Teacher — 6 लाख+ Students</div>
  <div class="idx-box">
    <div class="idx-title">Index — इस PDF में शामिल विषय</div>
    {index_rows}
  </div>
  <div class="footnote">&copy; New India Education — {site_url} — कृपया इस PDF को शेयर करते समय source क्रेडिट बनाए रखें।</div>
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
