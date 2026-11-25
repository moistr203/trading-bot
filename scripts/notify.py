#!/usr/bin/env python3
"""Send the owner a phone notification. Telegram first, WhatsApp (CallMeBot) as a fallback.

Usage: bash scripts/notify.sh "message text"
Telegram needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the environment.
WhatsApp (optional) needs WHATSAPP_PHONE and CALLMEBOT_APIKEY.
If nothing is configured it prints a note and exits 0, so a run never fails
because of notifications. Never prints tokens, keys or phone numbers.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DASHBOARD = "https://moistr203.github.io/trading-bot/"


def env(name):
    return os.environ.get(name, "").strip()


def telegram(text):
    token, chat = env("TELEGRAM_BOT_TOKEN"), env("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return None
    body = json.dumps({"chat_id": chat, "text": text,
                       "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return "TELEGRAM_SENT" if json.loads(r.read().decode()).get("ok") else "TELEGRAM_FAILED: not ok"
    except urllib.error.HTTPError as e:
        try:
            desc = json.loads(e.read().decode()).get("description", "")
        except Exception:
            desc = ""
        return f"TELEGRAM_FAILED: HTTP {e.code} {desc}. Check the token and chat id, and that you pressed Start in the bot."
    except (urllib.error.URLError, OSError) as e:
        return f"TELEGRAM_FAILED: {getattr(e, 'reason', e)}. Check api.telegram.org is in the network allowlist."


def whatsapp(text):
    phone, key = env("WHATSAPP_PHONE"), env("CALLMEBOT_APIKEY")
    if not phone or not key:
        return None
    url = "https://api.callmebot.com/whatsapp.php?" + urllib.parse.urlencode(
        {"phone": phone, "text": text, "apikey": key})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            ok = r.status == 200 and "error" not in r.read().decode(errors="replace").lower()
            return "WHATSAPP_SENT" if ok else "WHATSAPP_FAILED: not accepted"
    except (urllib.error.URLError, OSError) as e:
        return f"WHATSAPP_FAILED: {getattr(e, 'reason', e)}"


if __name__ == "__main__":
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print('usage: notify.sh "message"')
        sys.exit(1)
    text = sys.argv[1].strip()
    if len(text) > 3500:
        text = text[:3480].rstrip() + "…"
    text += "\n\n" + DASHBOARD
    results = [r for r in (telegram(text), whatsapp(text)) if r]
    print("\n".join(results) if results else
          "NOTIFY_SKIPPED: no Telegram or WhatsApp settings in the environment.")
