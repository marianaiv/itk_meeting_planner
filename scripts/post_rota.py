#!/usr/bin/env python3
import csv, os, sys, argparse
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import requests

TZ = ZoneInfo("Europe/Berlin")
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rota.csv")
WEBHOOK_URL = os.environ.get("MATTERMOST_WEBHOOK_URL")

parser = argparse.ArgumentParser()
parser.add_argument("--date", help="Base ISO date (yyyy-mm-dd). Defaults to 'today' in Europe/Berlin.")
parser.add_argument("--advance-days", type=int, default=int(os.getenv("ADVANCE_DAYS", "0")),
                    help="How many days ahead to look up in the rota (e.g., 3 for Friday→Monday).")
args = parser.parse_args()

if not WEBHOOK_URL:
    print("Error: MATTERMOST_WEBHOOK_URL env var not set", file=sys.stderr)
    sys.exit(2)

base = date.fromisoformat(args.date) if args.date else datetime.now(TZ).date()
target = base + timedelta(days=args.advance_days)
target_iso = target.isoformat()

# Read CSV and look for meeting on target date
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

match = next((r for r in rows if r["date"].strip() == target_iso), None)
if not match:
    print(f"No rota entry for {target_iso}. (Base={base.isoformat()}, advance={args.advance_days})")
    sys.exit(0)

chair = match["chair"].strip()
notes = match["notes"].strip()

weekday = target.strftime("%A")  # e.g., Monday
nice_when = f"{weekday} {target_iso}"

text = f"🔔 Reminder: on {nice_when} the meeting is chaired by {chair} and notes are taken by {notes}."

r = requests.post(WEBHOOK_URL, json={"text": text}, timeout=10)
if r.status_code // 100 != 2:
    print("Webhook error:", r.status_code, r.text, file=sys.stderr)
    sys.exit(1)
print("Posted:", text)
