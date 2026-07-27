# -*- coding: utf-8 -*-
"""
Checks the omkarsir-comments Firestore project for new PENDING comments that
haven't been notified yet, sends a Telegram DM to the admin for each one,
then marks them notified:true so they aren't repeated on the next run.

Required environment variables:
  FIREBASE_ADMIN_EMAIL, FIREBASE_ADMIN_PASSWORD  -- same login used for admin-comments.html
  FIREBASE_WEB_API_KEY                            -- public web API key (not secret, same as in admin-comments.html)
  TELEGRAM_BOT_TOKEN                              -- existing bot token (same one used for daily quiz)
  ADMIN_TELEGRAM_CHAT_ID                          -- Omkar Sir's personal Telegram chat id (not a secret, just an id)
"""
import os, sys, json, requests

PROJECT_ID = "omkarsir-comments"
FIREBASE_WEB_API_KEY = os.environ.get("FIREBASE_WEB_API_KEY", "AIzaSyBalM_wgEhegoReyANDLiSHRvwi7n4zIUk")

def fail(msg):
    print(f"::error::{msg}")
    sys.exit(0)  # exit 0 so the workflow doesn't show as a hard failure for missing-secret situations

def sign_in():
    email = os.environ.get("FIREBASE_ADMIN_EMAIL")
    password = os.environ.get("FIREBASE_ADMIN_PASSWORD")
    if not email or not password:
        fail("FIREBASE_ADMIN_EMAIL / FIREBASE_ADMIN_PASSWORD secrets missing — comment-watch skipped.")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    r = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=20)
    if r.status_code != 200:
        fail(f"Firebase sign-in failed: {r.status_code} {r.text[:300]}")
    return r.json()["idToken"]

def list_pending_comments(id_token):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents:runQuery"
    body = {
        "structuredQuery": {
            "from": [{"collectionId": "comments"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "status"},
                    "op": "EQUAL",
                    "value": {"stringValue": "pending"}
                }
            },
            "limit": 200
        }
    }
    r = requests.post(url, headers={"Authorization": f"Bearer {id_token}"}, json=body, timeout=20)
    if r.status_code != 200:
        fail(f"Firestore query failed: {r.status_code} {r.text[:300]}")
    out = []
    for row in r.json():
        doc = row.get("document")
        if not doc:
            continue
        fields = doc.get("fields", {})
        already_notified = fields.get("notified", {}).get("booleanValue", False)
        if already_notified:
            continue
        doc_id = doc["name"].split("/")[-1]
        out.append({
            "id": doc_id,
            "pageId": fields.get("pageId", {}).get("stringValue", ""),
            "name": fields.get("name", {}).get("stringValue", ""),
            "text": fields.get("text", {}).get("stringValue", ""),
        })
    return out

def mark_notified(id_token, doc_id):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/comments/{doc_id}?updateMask.fieldPaths=notified"
    body = {"fields": {"notified": {"booleanValue": True}}}
    requests.patch(url, headers={"Authorization": f"Bearer {id_token}"}, json=body, timeout=20)

def send_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("ADMIN_TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        fail("TELEGRAM_BOT_TOKEN / ADMIN_TELEGRAM_CHAT_ID secrets missing — comment-watch skipped.")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=20)
    if r.status_code != 200:
        print(f"Telegram send failed: {r.status_code} {r.text[:300]}")

def main():
    id_token = sign_in()
    pending = list_pending_comments(id_token)
    if not pending:
        print("No new pending comments.")
        return
    for c in pending:
        msg = (
            f"💬 <b>नया Comment आया है</b>\n\n"
            f"📄 Page: {c['pageId']}\n"
            f"🧑 Name: {c['name']}\n"
            f"📝 {c['text']}\n\n"
            f"Approve/Reject: https://omkarsir.com/admin-comments.html"
        )
        send_telegram(msg)
        mark_notified(id_token, c["id"])
        print(f"Notified for comment {c['id']}")

if __name__ == "__main__":
    main()
