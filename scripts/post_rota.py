#!/usr/bin/env python3
import csv, os, sys, argparse, io
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import requests

TZ = ZoneInfo("Europe/Berlin")
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rota.csv")

SHARE_URL = os.environ.get("ROTA_SHARE_URL", "https://syncandshare.desy.de/index.php/s/PXG3rfMC8ZtWSiW")
CSV_URL = os.environ.get("ROTA_CSV_URL", SHARE_URL.rstrip("/") + "/download")

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

def load_rows():
    # Try remote first
    try:
        resp = requests.get(CSV_URL, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        # Requests will decode based on headers; set a fallback if needed:
        resp.encoding = resp.encoding or "utf-8"
        return list(csv.DictReader(io.StringIO(resp.text)))
    except Exception as e:
        # Fallback to repo file if remote is down
        try:
            with open(CSV_PATH, newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except Exception:
            print(f"Failed to download rota CSV from {CSV_URL}: {e}", file=sys.stderr)
            raise

rows = load_rows()

match = next((r for r in rows if r["date"].strip() == target_iso), None)
if not match:
    print(f"No rota entry for {target_iso}. (Base={base.isoformat()}, advance={args.advance_days})")
    sys.exit(0)

chair = match["chair"].strip()
notes = match["notes"].strip()

weekday = target.strftime("%A")  # e.g., Monday
nice_when = f"{weekday} {target_iso}"

text = (
    "##### ‼️ Reminder\n"
    f"On {nice_when} the ITk detector meeting is chaired by 🪑 {chair} and minutes are taken by 📝 {notes} .\n"
    f"Please find a replacement if you can't attend."
)

r = requests.post(WEBHOOK_URL, json={"text": text}, timeout=10)
if r.status_code // 100 != 2:
    print("Webhook error:", r.status_code, r.text, file=sys.stderr)
    sys.exit(1)
print("Posted:", text)
