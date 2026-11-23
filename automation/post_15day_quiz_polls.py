#!/usr/bin/env python3
"""Post one verified three-question Telegram quiz slot for the 15-day campaign."""

import datetime as dt
import json
import os
import pathlib
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

BANK_DIR = pathlib.Path(__file__).with_name("quiz-bank-15days")
START = dt.date(2026, 11, 17)
END = dt.date(2026, 12, 6)


def main() -> None:
    today = dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()
    run_date = dt.date.fromisoformat(os.getenv("QUIZ_DATE", str(today)))
    slot = int(os.environ["QUIZ_SLOT"])
    if slot == 6:
        print("Slot 6 (Current Affairs) is permanently disabled.")
        return
    if not START <= run_date <= END:
        raise SystemExit(f"Date {run_date} is outside the approved campaign")
    if slot not in range(1, 9):
        raise SystemExit("QUIZ_SLOT must be 1 through 8")

    bank = BANK_DIR / f"{run_date}.json"
    questions = [q for q in json.loads(bank.read_text()) if q["slot"] == slot]
    if len(questions) != 3:
        raise SystemExit(f"Expected 3 questions, found {len(questions)}")

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "@omkarsirofficial").strip()
    dry_run = os.getenv("DRY_RUN") == "1"
    if not token and not dry_run:
        raise SystemExit("TELEGRAM_BOT_TOKEN is required")

    for q in questions:
        payload = {
            "chat_id": chat_id,
            "question": q["question"],
            "options": q["options"],
            "type": "quiz",
            "correct_option_id": q["answer"],
            "explanation": q["explanation"],
            "is_anonymous": True,
        }
        if dry_run:
            print(json.dumps(payload, ensure_ascii=False))
            continue
        request = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendPoll",
            data=json.dumps(payload, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            response = json.loads(urllib.request.urlopen(request, timeout=30).read())
        except urllib.error.HTTPError as exc:
            raise SystemExit(exc.read().decode("utf-8", "replace")) from exc
        if not response.get("ok"):
            raise SystemExit(response.get("description", "Telegram rejected the poll"))
        print(f"Posted {run_date} slot {slot}, question {q['question_in_slot']}: message {response['result']['message_id']}")


if __name__ == "__main__":
    main()
