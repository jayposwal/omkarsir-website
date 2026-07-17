#!/usr/bin/env python3
"""
Posts the day's 15 Current Affairs MCQs to the Telegram channel as native
Telegram Quiz Polls (sendPoll, type=quiz) — one poll per question, sent in
quick succession, each with a short (<=200 char) explanation shown after
answering. The full detailed explanation lives only on the website's quiz
page (quiz/YYYY-MM-DD.html), which is linked in an intro message first.

Runs inside GitHub Actions (normal internet access) — NOT the Cowork
sandbox, which blocks api.telegram.org via its network allowlist.

Env vars required:
  TELEGRAM_BOT_TOKEN   - bot token from @BotFather
  TELEGRAM_CHAT_ID     - e.g. "@omkarsirofficial"
"""
import glob
import json
import os
import re
import time
import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUIZ_DATA_DIR = os.path.join(REPO_ROOT, "quiz-data")
SITE_URL = "https://omkarsir.com"

TG_QUESTION_MAX = 300
TG_OPTION_MAX = 100
TG_EXPLANATION_MAX = 200


def find_latest_quiz_json():
    files = glob.glob(os.path.join(QUIZ_DATA_DIR, "????-??-??.json"))
    dated = []
    for f in files:
        base = os.path.basename(f)
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\.json$", base)
        if m:
            dated.append((m.group(1), f))
    if not dated:
        raise SystemExit("No dated quiz-data/YYYY-MM-DD.json files found")
    dated.sort(key=lambda t: t[0])
    return dated[-1]


def clip(text, limit):
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def main():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        raise SystemExit("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env vars are required")

    date_str, path = find_latest_quiz_json()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    questions = data["questions"]
    hindi_date = data.get("hindi_date", date_str)
    print(f"Loaded {len(questions)} questions for {hindi_date} from {path}")

    quiz_page_url = f"{SITE_URL}/quiz/{date_str}.html"

    # Intro message with link to the full website quiz (full explanations live there)
    intro = (
        f"📝 {hindi_date} — Daily Current Affairs Quiz ({len(questions)} प्रश्न)\n\n"
        f"नीचे एक-एक करके सभी प्रश्न आ रहे हैं — जवाब देकर तुरंत सही उत्तर देखें।\n"
        f"विस्तृत व्याख्या (detailed explanation) व स्कोर के लिए वेबसाइट पर क्विज़ दें:\n"
        f"🔗 {quiz_page_url}"
    )
    resp = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data={"chat_id": chat_id, "text": intro},
        timeout=30,
    )
    print("Intro message status:", resp.status_code, resp.text[:300])
    resp.raise_for_status()

    time.sleep(1.5)

    sent = 0
    for i, q in enumerate(questions, start=1):
        diff_emoji = {"easy": "🟢", "medium": "🟠", "hard": "🔴"}.get(q["difficulty"], "")
        prefix = f"Q{i}/{len(questions)} {diff_emoji} "
        question_text = clip(prefix + q["question"], TG_QUESTION_MAX)
        options = [clip(opt, TG_OPTION_MAX) for opt in q["options"]]
        explanation = clip(q.get("explanation_short", ""), TG_EXPLANATION_MAX)

        payload = {
            "chat_id": chat_id,
            "question": question_text,
            "options": json.dumps(options, ensure_ascii=False),
            "type": "quiz",
            "correct_option_id": q["correct_index"],
            "is_anonymous": True,
        }
        if explanation:
            payload["explanation"] = explanation

        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendPoll",
            data=payload,
            timeout=30,
        )
        ok = r.ok and r.json().get("ok")
        print(f"Q{i}: status={r.status_code} ok={ok} body={r.text[:200]}")
        if not ok:
            raise SystemExit(f"Telegram sendPoll failed for Q{i}: {r.text}")
        sent += 1
        time.sleep(1.5)  # stay safely under per-chat rate limits

    print(f"Posted {sent}/{len(questions)} quiz polls successfully to {chat_id}")


if __name__ == "__main__":
    main()
