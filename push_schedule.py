"""Pull Atrium schedule blocks from Workday RaaS for a date range and POST them to WEBHOOK_URL.

Usage: python push_schedule.py [START_DATE] [END_DATE] [WEBHOOK_URL]   (YYYY-MM-DD; default: today .. today; webhook default from config)
Credentials: env vars USERNAME, PASSWORD, WEBHOOK_URL (cloud), else a .env file next to this script (local).
One report call per run, no retries: Atrium's Workday is sensitive to load. Stdlib only.
"""
import base64, datetime, json, os, pathlib, sys, urllib.parse, urllib.request

dotenv = pathlib.Path(__file__).with_name(".env")
env = dict(l.split("=", 1) for l in dotenv.read_text().splitlines() if "=" in l) if dotenv.exists() else {}
cfg = lambda k: (env.get(k) or os.environ[k]).strip()  # .env first: Windows always sets its own USERNAME

start = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
end = sys.argv[2] if len(sys.argv) > 2 else start

q = urllib.parse.urlencode({"Start_Date": f"{start}-00:00", "End_Date": f"{end}-00:00", "format": "json"})
url = f"https://wd5-services1.myworkday.com/ccx/service/customreport2/atriumhospitality/saikiran.doddaka/Schedule_blocks_-_Cloudapper?{q}"
auth = base64.b64encode(f"{cfg('USERNAME')}:{cfg('PASSWORD')}".encode()).decode()
req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
rows = json.load(urllib.request.urlopen(req, timeout=900))["Report_Entry"]

body = json.dumps({"Report_Entry": rows}).encode()  # same shape Workday returns
hook = sys.argv[3] if len(sys.argv) > 3 else cfg("WEBHOOK_URL")  # optional override, e.g. a parallel workflow
post = urllib.request.Request(hook,data=body, headers={"Content-Type": "application/json"})
try:
    status = urllib.request.urlopen(post, timeout=120).status
except TimeoutError:  # CloudApper keeps processing (~70 rows/min) after the reply times out
    status = "accepted, reply timed out (workflow still running)"
print(f"{start}..{end}: {len(rows)} rows -> webhook {status}")
