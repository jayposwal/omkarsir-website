#!/usr/bin/env python3
"""
Posts the first TG_POLL_COUNT (5) of the day's 15 Current Affairs MCQs to
the Telegram channel as native Telegram Quiz Polls (sendPoll, type=quiz) —
one poll per question, sent in quick succession, each with a short
(<=200 char) explanation shown after answering. After the polls, a closing
message points members to the website's quiz page (quiz/YYYY-MM-DD.html)
to solve the full 15-question quiz with detailed explanations and a score.
Finally, a branded PDF of all 15 questions (with answers + explanations)
is generated and sent as a downloadable Telegram document, so students can
save/print the full quiz.

Runs inside GitHub Actions (normal internet access) — NOT the Cowork
sandbox, which blocks api.telegram.org via its network allowlist.

Env vars required:
  TELEGRAM_BOT_TOKEN   - bot token from @BotFather
  TELEGRAM_CHAT_ID     - e.g. "@omkarsirofficial"
"""
import datetime
import glob
import json
import os
import re
import sys
import time
import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUIZ_DATA_DIR = os.path.join(REPO_ROOT, "quiz-data")
SITE_URL = "https://omkarsir.com"

TG_QUESTION_MAX = 300
TG_OPTION_MAX = 100
TG_EXPLANATION_MAX = 200
TG_POLL_COUNT = 5  # only first N questions go to Telegram as polls; full 15 live on the website quiz page

HINDI_MONTHS = {
    1: "जनवरी", 2: "फरवरी", 3: "मार्च", 4: "अप्रैल", 5: "मई", 6: "जून",
    7: "जुलाई", 8: "अगस्त", 9: "सितंबर", 10: "अक्टूबर", 11: "नवंबर", 12: "दिसंबर",
}


def eng_date_string(date_str):
    y, m, d = (int(x) for x in date_str.split("-"))
    return datetime.date(y, m, d).strftime("%d %B %Y").lstrip("0")


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
    poll_questions = questions[:TG_POLL_COUNT]

    # Intro message — sets expectation that only a preview (5) is here, full 15 on website
    intro = (
        f"📝 {hindi_date} — Daily Current Affairs Quiz\n\n"
        f"यहाँ शुरू के {len(poll_questions)} प्रश्न — जवाब देकर तुरंत सही उत्तर देखें।"
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
    for i, q in enumerate(poll_questions, start=1):
        diff_emoji = {"easy": "🟢", "medium": "🟠", "hard": "🔴"}.get(q["difficulty"], "")
        prefix = f"Q{i}/{len(poll_questions)} {diff_emoji} "
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

    # Closing message — points to the website for the full 15-question quiz
    closing = (
        f"🎯 आज के Current Affairs पर आधारित {len(questions)} सवालों की Quiz Solve करें:\n"
        f"🔗 {quiz_page_url}"
    )
    r = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data={"chat_id": chat_id, "text": closing},
        timeout=30,
    )
    print("Closing message status:", r.status_code, r.text[:300])
    r.raise_for_status()

    print(f"Posted {sent}/{len(poll_questions)} quiz polls (of {len(questions)} total questions) successfully to {chat_id}")

    # --- Downloadable PDF of the full 15-question quiz (with answers + explanations) ---
    time.sleep(1.5)
    pdf_path = os.path.join(REPO_ROOT, f"Quiz-{date_str}.pdf")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import generate_quiz_pdf  # noqa: E402

    font_regular = os.path.join(REPO_ROOT, "automation", "fonts", "NotoMerged-Regular.ttf")
    font_bold = os.path.join(REPO_ROOT, "automation", "fonts", "NotoMerged-Bold.ttf")
    html_str = generate_quiz_pdf.build_html(
        data, hindi_date, eng_date_string(date_str),
        font_regular, font_bold, SITE_URL.replace("https://", ""), quiz_page_url,
    )
    from weasyprint import HTML
    HTML(string=html_str, base_url=".").write_pdf(pdf_path)
    print("Generated quiz PDF:", pdf_path)

    pdf_caption = (
        f"📥 {hindi_date} — आज के {len(questions)} सवालों की Quiz PDF डाउनलोड करें\n"
        f"उत्तर व विस्तृत व्याख्या सहित — पढ़ो, Practice करो, Save रखो 📚"
    )
    with open(pdf_path, "rb") as f:
        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendDocument",
            data={"chat_id": chat_id, "caption": pdf_caption},
            files={"document": (os.path.basename(pdf_path), f, "application/pdf")},
            timeout=60,
        )
    print("PDF document status:", r.status_code, r.text[:300])
    r.raise_for_status()
    if not r.json().get("ok"):
        raise SystemExit(f"Telegram sendDocument failed for quiz PDF: {r.text}")
    print("Posted quiz PDF successfully to", chat_id)


if __name__ == "__main__":
    main()
