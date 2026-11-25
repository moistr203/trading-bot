#!/usr/bin/env python3
"""Send a WhatsApp message to the owner via CallMeBot (free, personal use).

Usage: bash scripts/notify.sh "message text"
Needs WHATSAPP_PHONE (with country code, e.g. +15551234567) and CALLMEBOT_APIKEY
in the environment. If either is missing it prints a note and exits 0, so a run
never fails because of notifications. Never prints the key or the phone number.
"""
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DASHBOARD = "https://moistr203.github.io/trading-bot/"

if len(sys.argv) < 2 or not sys.argv[1].strip():
    print("usage: notify.sh \"message\"")
    sys.exit(1)

phone = os.environ.get("WHATSAPP_PHONE", "").strip()
key = os.environ.get("CALLMEBOT_APIKEY", "").strip()
if not phone or not key:
    print("NOTIFY_SKIPPED: WHATSAPP_PHONE or CALLMEBOT_APIKEY not set.")
    sys.exit(0)

text = sys.argv[1].strip()
if len(text) > 1200:
    text = text[:1180].rstrip() + "…"
text += "\n\n" + DASHBOARD

url = "https://api.callmebot.com/whatsapp.php?" + urllib.parse.urlencode(
    {"phone": phone, "text": text, "apikey": key})
try:
    with urllib.request.urlopen(url, timeout=30) as r:
        body = r.read().decode(errors="replace").lower()
        ok = r.status == 200 and "error" not in body
except (urllib.error.URLError, OSError) as e:
    print(f"NOTIFY_FAILED: {getattr(e, 'reason', e)}. Check api.callmebot.com is in the network allowlist.")
    sys.exit(0)
print("NOTIFY_SENT" if ok else "NOTIFY_FAILED: CallMeBot did not accept the message (check phone/apikey).")
