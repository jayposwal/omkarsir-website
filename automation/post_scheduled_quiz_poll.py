#!/usr/bin/env python3
"""Post one of five daily Telegram quiz polls for a limited campaign."""

import datetime
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUIZ_DATA_DIR = os.path.join(REPO_ROOT, "quiz-data")
SITE_URL = "https://omkarsir.com"

CAMPAIGN_START = datetime.date(2026, 11, 15)
CAMPAIGN_END = datetime.date(2026, 12, 14)
SLOTS_PER_DAY = 5

TG_QUESTION_MAX = 300
TG_OPTION_MAX = 100
TG_EXPLANATION_MAX = 200


def ist_today():
    override = os.environ.get("TARGET_DATE", "").strip()
    if override:
        return datetime.date.fromisoformat(override)
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).date()


def clip(text, limit):
    text = str(text or "")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def available_quizzes(up_to_date):
    quizzes = []
    for path in glob.glob(os.path.join(QUIZ_DATA_DIR, "????-??-??.json")):
        match = re.match(r"^(\d{4}-\d{2}-\d{2})\.json$", os.path.basename(path))
        if not match:
            continue
        quiz_date = datetime.date.fromisoformat(match.group(1))
        if quiz_date <= up_to_date:
            quizzes.append((quiz_date, path))
    return sorted(quizzes, reverse=True)


def select_quiz(run_date):
    today_path = os.path.join(QUIZ_DATA_DIR, f"{run_date.isoformat()}.json")
    if os.path.exists(today_path):
        return run_date, today_path, True

    quizzes = available_quizzes(run_date)
    if not quizzes:
        raise SystemExit("No dated quiz-data JSON files are available")

    # Rotate through the 30 most recent archive quizzes, one complete set per day.
    pool = quizzes[:30]
    campaign_day = (run_date - CAMPAIGN_START).days
    source_date, path = pool[campaign_day % len(pool)]
    return source_date, path, False


def post_form(url, data):
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(data).encode("utf-8"),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    result = json.loads(body)
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API rejected the request: {body}")
    return result


def send_message(api_base, chat_id, message, dry_run):
    if dry_run:
        print("DRY RUN sendMessage:", message)
        return
    post_form(
        f"{api_base}/sendMessage",
        {"chat_id": chat_id, "text": message},
    )


def send_poll(api_base, chat_id, payload, dry_run):
    if dry_run:
        print("DRY RUN sendPoll:", json.dumps(payload, ensure_ascii=False, indent=2))
        return
    post_form(f"{api_base}/sendPoll", payload)


def main():
    run_date = ist_today()
    if not CAMPAIGN_START <= run_date <= CAMPAIGN_END:
        print(
            f"No-op: {run_date} is outside campaign "
            f"{CAMPAIGN_START} through {CAMPAIGN_END}."
        )
        return

    try:
        slot = int(os.environ.get("TG_QUIZ_SLOT", ""))
    except ValueError as exc:
        raise SystemExit("TG_QUIZ_SLOT must be an integer from 1 to 5") from exc
    if slot not in range(1, SLOTS_PER_DAY + 1):
        raise SystemExit("TG_QUIZ_SLOT must be an integer from 1 to 5")

    dry_run = os.environ.get("DRY_RUN", "").lower() in {"1", "true", "yes"}
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not dry_run and (not bot_token or not chat_id):
        raise SystemExit("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")

    source_date, path, is_fresh = select_quiz(run_date)
    with open(path, encoding="utf-8") as quiz_file:
        data = json.load(quiz_file)
    questions = data.get("questions", [])
    if len(questions) < SLOTS_PER_DAY:
        raise SystemExit(f"Quiz file has only {len(questions)} questions: {path}")

    question = questions[slot - 1]
    source_date_str = source_date.isoformat()
    quiz_page_url = f"{SITE_URL}/quiz/{source_date_str}.html"
    api_base = f"https://api.telegram.org/bot{bot_token}" if bot_token else "DRY_RUN"

    if slot == 1:
        freshness_note = (
            "आज के Current Affairs पर आधारित"
            if is_fresh
            else "चुने हुए परीक्षा-उपयोगी सवालों के साथ"
        )
        send_message(
            api_base,
            chat_id,
            "📝 आज की Daily Practice Quiz\n\n"
            f"{freshness_note} — सुबह से शाम तक 5 Quiz Polls।",
            dry_run,
        )

    difficulty_emoji = {
        "easy": "🟢",
        "medium": "🟠",
        "hard": "🔴",
    }.get(str(question.get("difficulty", "")).lower(), "🧠")
    poll_payload = {
        "chat_id": chat_id,
        "question": clip(
            f"Q{slot}/{SLOTS_PER_DAY} {difficulty_emoji} {question['question']}",
            TG_QUESTION_MAX,
        ),
        "options": json.dumps(
            [clip(option, TG_OPTION_MAX) for option in question["options"]],
            ensure_ascii=False,
        ),
        "type": "quiz",
        "correct_option_id": int(question["correct_index"]),
        "is_anonymous": True,
    }
    explanation = clip(question.get("explanation_short", ""), TG_EXPLANATION_MAX)
    if explanation:
        poll_payload["explanation"] = explanation

    send_poll(api_base, chat_id, poll_payload, dry_run)
    print(f"Posted slot {slot}/{SLOTS_PER_DAY} using {os.path.basename(path)}")

    if slot == SLOTS_PER_DAY:
        send_message(
            api_base,
            chat_id,
            "🎯 आज की practice पूरी! सभी 15 सवाल और विस्तृत व्याख्या यहाँ देखें:\n"
            f"🔗 {quiz_page_url}",
            dry_run,
        )


if __name__ == "__main__":
    try:
        main()
    except (urllib.error.URLError, RuntimeError) as exc:
        print(f"Telegram request failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
