#!/usr/bin/env python3
"""
Finds the latest dated Current Affairs page (current-affairs/YYYY-MM-DD.html),
generates its PDF via generate_ca_pdf.py, and posts it to the Telegram channel
along with a caption (meta description + website link).

Runs inside GitHub Actions (which has normal internet access) — NOT inside
the Cowork sandbox, which blocks api.telegram.org via its network allowlist.

Env vars required:
  TELEGRAM_BOT_TOKEN   - bot token from @BotFather
  TELEGRAM_CHAT_ID     - e.g. "@omkarsirofficial"
"""
import glob
import os
import re
import sys
import datetime
import requests
from bs4 import BeautifulSoup

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CA_DIR = os.path.join(REPO_ROOT, "current-affairs")
SITE_URL = "omkarsir.com"

HINDI_MONTHS = {
    1: "जनवरी", 2: "फरवरी", 3: "मार्च", 4: "अप्रैल", 5: "मई", 6: "जून",
    7: "जुलाई", 8: "अगस्त", 9: "सितंबर", 10: "अक्टूबर", 11: "नवंबर", 12: "दिसंबर",
}


def find_latest_dated_file():
    files = glob.glob(os.path.join(CA_DIR, "????-??-??.html"))
    dated = []
    for f in files:
        base = os.path.basename(f)
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})\.html$", base)
        if m:
            dated.append((base[:10], f))
    if not dated:
        raise SystemExit("No dated current-affairs/YYYY-MM-DD.html files found")
    dated.sort(key=lambda t: t[0])
    return dated[-1]  # (date_str, path)


def date_strings(date_str):
    y, m, d = (int(x) for x in date_str.split("-"))
    dt = datetime.date(y, m, d)
    hindi = f"{d} {HINDI_MONTHS[m]} {y}"
    eng = dt.strftime("%d %B %Y").lstrip("0")
    return hindi, eng


def extract_caption(html_path, date_str, page_url):
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""
    hindi_date, _ = date_strings(date_str)
    lines = [f"📰 {hindi_date} — Daily Current Affairs"]
    if desc:
        lines.append(desc)
    lines.append(f"\n🔗 पूरा पढ़ें: {page_url}")
    caption = "\n".join(lines)
    return caption[:1020]  # Telegram document caption limit is 1024 chars


def main():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        raise SystemExit("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env vars are required")

    date_str, html_path = find_latest_dated_file()
    hindi_date, eng_date = date_strings(date_str)
    print(f"Latest dated page: {html_path} ({hindi_date} / {eng_date})")

    pdf_path = os.path.join(REPO_ROOT, f"CA-{date_str}.pdf")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import generate_ca_pdf  # noqa: E402

    sections = generate_ca_pdf.extract_sections(html_path)
    font_regular = os.path.join(REPO_ROOT, "automation", "fonts", "NotoMerged-Regular.ttf")
    font_bold = os.path.join(REPO_ROOT, "automation", "fonts", "NotoMerged-Bold.ttf")
    html_str = generate_ca_pdf.build_html(
        sections, hindi_date, eng_date, font_regular, font_bold, SITE_URL
    )
    from weasyprint import HTML
    HTML(string=html_str, base_url=".").write_pdf(pdf_path)
    print("Generated PDF:", pdf_path)

    page_url = f"https://{SITE_URL}/current-affairs/{date_str}.html"
    caption = extract_caption(html_path, date_str, page_url)

    with open(pdf_path, "rb") as f:
        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendDocument",
            data={
                "chat_id": chat_id,
                "caption": caption,
            },
            files={"document": (os.path.basename(pdf_path), f, "application/pdf")},
            timeout=60,
        )
    print("Telegram response status:", resp.status_code)
    print("Telegram response body:", resp.text[:500])
    resp.raise_for_status()
    result = resp.json()
    if not result.get("ok"):
        raise SystemExit(f"Telegram API returned ok=false: {result}")
    print("Posted successfully to", chat_id)


if __name__ == "__main__":
    main()
