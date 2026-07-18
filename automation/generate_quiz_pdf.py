#!/usr/bin/env python3
"""
Generates a branded, printable PDF from a New India Education daily Quiz
JSON (quiz-data/YYYY-MM-DD.json), for automated distribution (e.g.
Telegram). Uses WeasyPrint (Pango/HarfBuzz) for correct Devanagari shaping,
matching the same cover+branding style as generate_ca_pdf.py. Every
question is followed by its 4 options, the correct answer, and a detailed
explanation, so students can self-check after downloading.

Usage: python3 generate_quiz_pdf.py <path-to-quiz-json> <output-pdf-path> \
           --hindi-date "18 जुलाई 2026" --eng-date "18 July 2026" \
           --font-regular <ttf> --font-bold <ttf>
"""
import argparse
import json
import re

from weasyprint import HTML

APP_LINK = "https://play.google.com/store/apps/details?id=co.april2019.techa"

# The embedded Devanagari+Latin font has no emoji glyphs, so any emoji in
# question/option/explanation text (or in this template) renders as blank
# "tofu" boxes in the PDF — strip them, same approach as generate_ca_pdf.py.
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
    return EMOJI_RE.sub("", text or "").strip()


CATEGORY_META = {
    "National": ("राष्ट्रीय", "#1B2A6B"),
    "International": ("अंतर्राष्ट्रीय", "#00A651"),
    "Rajasthan": ("राजस्थान", "#FF6B00"),
    "Sujas": ("सुजस", "#1B2A6B"),
    "Economic": ("आर्थिक", "#00A651"),
    "Science-Defence-Tech": ("विज्ञान-रक्षा-तकनीक", "#FF6B00"),
    "Sports-Awards": ("खेल-पुरस्कार-व्यक्तित्व", "#1B2A6B"),
}

DIFFICULTY_META = {
    "easy": ("आसान", "#00A651"),
    "medium": ("मध्यम", "#FF6B00"),
    "hard": ("कठिन", "#D93025"),
}

OPT_LABELS = ["अ", "ब", "स", "द"]


def build_html(data, hindi_date, eng_date, font_regular, font_bold, site_url, quiz_page_url):
    questions = data["questions"]

    idx_rows = "".join(
        f'<div class="idx-row"><span class="dot" style="background:{color}"></span>{hindi}</div>'
        for hindi, color in {v[0]: v[1] for v in CATEGORY_META.values()}.items()
    )

    q_html = ""
    for i, q in enumerate(questions, start=1):
        cat_hindi, color = CATEGORY_META.get(q.get("category", ""), ("सामान्य", "#1B2A6B"))
        diff_hindi, diff_color = DIFFICULTY_META.get(q.get("difficulty", ""), ("", "#888"))
        opts_html = "".join(
            f'''<div class="opt{" correct" if idx == q["correct_index"] else ""}">
                  <span class="opt-label">{OPT_LABELS[idx]}</span>{strip_emoji(opt)}
                  {' <span class="tick">(सही उत्तर)</span>' if idx == q["correct_index"] else ""}
                </div>'''
            for idx, opt in enumerate(q["options"])
        )
        explanation = strip_emoji(q.get("explanation_full") or q.get("explanation_short", ""))
        q_html += f'''
        <div class="qblock">
          <div class="qhead">
            <span class="num" style="background:{color}">{i}</span>
            <span class="qtext">{strip_emoji(q["question"])}</span>
            <span class="tag" style="color:{diff_color}">{diff_hindi} &middot; {cat_hindi}</span>
          </div>
          <div class="opts">{opts_html}</div>
          <div class="ans"><b>व्याख्या:</b> {explanation}</div>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<style>
@font-face {{ font-family:'Noto'; src:url('{font_regular}'); font-weight:400; }}
@font-face {{ font-family:'Noto'; src:url('{font_bold}'); font-weight:700; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Noto', sans-serif; color:#222; font-size:15.5px; }}
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
  min-height: 120mm;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center; text-align:center;
  border-bottom: 2px solid #E8EAF0;
  padding-bottom: 14px;
  margin-bottom: 18px;
}}
.cover .brand {{ font-size:28px; font-weight:700; color:#1B2A6B; }}
.cover .brand a {{ border-bottom: 1px dotted #1B2A6B; }}
.cover .sub {{ font-size:14px; color:#777; margin-top:3px; }}
.cover .bar {{ width:64px; height:4px; background:linear-gradient(90deg,#FF6B00,#00A651); margin:14px auto; border-radius:4px; }}
.cover h1 {{ font-size:24px; color:#1B2A6B; font-weight:700; margin-top:6px; line-height:1.45; }}
.cover .cred {{ margin-top:12px; font-size:14px; font-weight:700; color:#FF6B00; max-width:500px; }}
.cover .link {{ margin-top:10px; font-size:13px; color:#1B2A6B; }}
.idx-box {{ margin-top:20px; text-align:left; width:420px; border:2px solid #E8EAF0; border-radius:12px; padding:14px 22px; }}
.idx-title {{ font-weight:700; color:#1B2A6B; font-size:16px; border-bottom:2px solid #eee; padding-bottom:8px; margin-bottom:8px; }}
.idx-row {{ font-size:15px; line-height:2.05; }}
.dot {{ display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:8px; }}

.qblock {{ margin-bottom:18px; page-break-inside:avoid; }}
.qhead {{ display:flex; align-items:flex-start; gap:10px; font-size:15.5px; line-height:1.7; margin-bottom:8px; }}
.num {{ flex:0 0 auto; width:24px; height:24px; border-radius:50%; color:#fff; font-size:13px; font-weight:700; text-align:center; line-height:24px; margin-top:1px; }}
.qtext {{ flex:1; font-weight:700; color:#222; }}
.tag {{ flex:0 0 auto; font-size:11px; color:#888; white-space:nowrap; }}
.opts {{ margin-left:34px; margin-bottom:8px; }}
.opt {{ font-size:14.5px; line-height:1.9; }}
.opt.correct {{ font-weight:700; color:#00A651; }}
.opt-label {{ display:inline-block; width:20px; font-weight:700; color:#1B2A6B; }}
.tick {{ font-size:12px; }}
.ans {{ margin-left:34px; background:#FFF3E8; border:1px solid #FFD0A0; border-radius:9px; padding:10px 14px; font-size:13.5px; line-height:1.75; color:#663c00; }}
</style>
</head>
<body>
<div class="wm">NEW INDIA EDUCATION</div>
<div class="footer-brand"><a href="{APP_LINK}">New India Education</a></div>

<div class="cover">
  <div class="brand"><a href="{APP_LINK}">New India Education</a><span style="color:#FF6B00">.</span></div>
  <div class="sub">{site_url} &nbsp;|&nbsp; NIEd</div>
  <div class="bar"></div>
  <h1>{hindi_date}<br>Daily Current Affairs Quiz — {len(questions)} प्रश्न</h1>
  <div class="cred">NCERT, RBSE की मूल पुस्तकों व प्रामाणिक स्रोतों से तैयार — विश्वसनीय एवं बेहतरीन Content</div>
  <div class="link">Online Quiz खेलें व Score पाएं: {quiz_page_url}</div>
  <div class="idx-box">
    <div class="idx-title">Index — इस PDF में शामिल विषय</div>
    {idx_rows}
  </div>
</div>
{q_html}
</body>
</html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("quiz_json")
    ap.add_argument("output_pdf")
    ap.add_argument("--hindi-date", required=True)
    ap.add_argument("--eng-date", required=True)
    ap.add_argument("--font-regular", required=True)
    ap.add_argument("--font-bold", required=True)
    ap.add_argument("--site-url", default="omkarsir.com")
    ap.add_argument("--quiz-page-url", required=True)
    args = ap.parse_args()

    with open(args.quiz_json, encoding="utf-8") as f:
        data = json.load(f)

    html_str = build_html(
        data, args.hindi_date, args.eng_date,
        args.font_regular, args.font_bold, args.site_url, args.quiz_page_url,
    )
    HTML(string=html_str, base_url=".").write_pdf(args.output_pdf)
    print("Wrote:", args.output_pdf)


if __name__ == "__main__":
    main()
