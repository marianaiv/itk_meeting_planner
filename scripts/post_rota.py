#!/usr/bin/env python3
import csv, os, sys
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

# Config
TZ = ZoneInfo("Europe/Berlin")
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rota.csv")
WEBHOOK_URL = os.environ.get("MATTERMOST_WEBHOOK_URL")

if not WEBHOOK_URL:
    print("Error: MATTERMOST_WEBHOOK_URL env var not set", file=sys.stderr)
    sys.exit(2)

today_iso = datetime.now(TZ).date().isoformat()
posted_any = False

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["date"].strip() == today_iso:
            chair = row["chair"].strip()
            notes = row["notes"].strip()
            text = f"Today the meeting is chaired by {chair} and notes are taken by {notes}."
            r = requests.post(WEBHOOK_URL, json={"text": text}, timeout=10)
            if r.status_code // 100 != 2:
                print("Webhook error:", r.status_code, r.text, file=sys.stderr)
                sys.exit(1)
            print("Posted:", text)
            posted_any = True

if not posted_any:
    print("No rota entry for", today_iso)
