#!/usr/bin/env python3
"""
Posts a weekly Hindi text digest of the current vacancy.html state to the
Telegram channel — open vacancies (with last dates), upcoming vacancies,
and a closed-count, plus a link to the full website page for details.

Runs inside GitHub Actions (normal internet access) — NOT the Cowork
sandbox, which blocks api.telegram.org via its network allowlist.

Env vars required:
  TELEGRAM_BOT_TOKEN   - bot token from @BotFather
  TELEGRAM_CHAT_ID     - e.g. "@omkarsirofficial"
"""
import os
import re
import datetime
import requests
from bs4 import BeautifulSoup

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VACANCY_HTML = os.path.join(REPO_ROOT, "vacancy.html")
SITE_URL = "https://omkarsir.com/vacancy.html"
MAX_LISTED_PER_SECTION = 15


def extract_cards():
    with open(VACANCY_HTML, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    cards = []
    for a in soup.select("a.vcard"):
        status = a.get("data-status", "")
        state = a.get("data-state", "")
        name_tag = a.find("h3")
        name = name_tag.get_text(strip=True) if name_tag else "?"
        last_date = ""
        for span in a.select(".vmeta span"):
            text = span.get_text(strip=True)
            if "अंतिम तिथि" in text:
                last_date = text.replace("📅", "").strip()
        cards.append({"status": status, "state": state, "name": name, "last_date": last_date})
    return cards


def build_message(cards):
    today = datetime.date.today()
    hindi_date = today.strftime("%d/%m/%Y")

    opens = [c for c in cards if c["status"] == "open"]
    upcoming = [c for c in cards if c["status"] == "upcoming"]
    closed = [c for c in cards if c["status"] == "closed"]

    lines = [f"📋 Weekly Vacancy Update — {hindi_date}", ""]

    if opens:
        lines.append(f"🟢 आवेदन जारी ({len(opens)}):")
        for c in opens[:MAX_LISTED_PER_SECTION]:
            detail = f" — {c['last_date']}" if c["last_date"] else ""
            lines.append(f"• {c['name']} ({c['state']}){detail}")
        if len(opens) > MAX_LISTED_PER_SECTION:
            lines.append(f"...और {len(opens) - MAX_LISTED_PER_SECTION} और website पर")
        lines.append("")

    if upcoming:
        lines.append(f"🟡 जल्द आने वाली ({len(upcoming)}):")
        for c in upcoming[:MAX_LISTED_PER_SECTION]:
            lines.append(f"• {c['name']} ({c['state']})")
        if len(upcoming) > MAX_LISTED_PER_SECTION:
            lines.append(f"...और {len(upcoming) - MAX_LISTED_PER_SECTION} और website पर")
        lines.append("")

    if closed:
        lines.append(f"🔴 {len(closed)} भर्तियां बंद हो चुकी हैं")
        lines.append("")

    lines.append(f"🔗 पूरी जानकारी व Apply लिंक: {SITE_URL}")
    return "\n".join(lines)[:4090]


def main():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        raise SystemExit("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env vars are required")

    cards = extract_cards()
    print(f"Extracted {len(cards)} vacancy cards")
    message = build_message(cards)
    print("--- message ---")
    print(message)

    resp = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data={"chat_id": chat_id, "text": message},
        timeout=30,
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
