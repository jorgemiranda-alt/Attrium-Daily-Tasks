"""Pull Atrium schedule blocks from Workday RaaS and POST them to CloudApper webhooks.

Usage:
  python push_schedule.py --3days                   today, tomorrow, day after: 3 parallel Workday calls,
                                                    each day posted to its own workflow (WEBHOOK_URL, _2, _3)
  python push_schedule.py [START] [END] [WEBHOOK]   one call for a date range (YYYY-MM-DD; default today)
Config: USERNAME, PASSWORD, WEBHOOK_URL, WEBHOOK_URL_2, WEBHOOK_URL_3 from a .env next to this script,
else environment variables (cloud). No retries: Atrium's Workday is sensitive to load. Stdlib only.
"""
import base64, datetime, http.client, json, os, pathlib, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

dotenv = pathlib.Path(__file__).with_name(".env")
env = dict(l.split("=", 1) for l in dotenv.read_text().splitlines() if "=" in l) if dotenv.exists() else {}
cfg = lambda k: (env.get(k) or os.environ[k]).strip()  # .env first: Windows always sets its own USERNAME
REPORT = "https://wd5-services1.myworkday.com/ccx/service/customreport2/atriumhospitality/saikiran.doddaka/Schedule_blocks_-_Cloudapper"


def fetch(start, end):
    q = urllib.parse.urlencode({"Start_Date": f"{start}-00:00", "End_Date": f"{end}-00:00", "format": "json"})
    auth = base64.b64encode(f"{cfg('USERNAME')}:{cfg('PASSWORD')}".encode()).decode()
    req = urllib.request.Request(f"{REPORT}?{q}", headers={"Authorization": f"Basic {auth}"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=900))["Report_Entry"]
    except Exception as e:  # say which stage failed; never retry
        raise RuntimeError(f"Workday fetch {start}..{end} failed: {type(e).__name__}: {e}") from e


def post(hook, rows):
    req = urllib.request.Request(hook, data=json.dumps({"Report_Entry": rows}).encode(), headers={"Content-Type": "application/json"})
    try:
        return urllib.request.urlopen(req, timeout=120).status
    except TimeoutError:  # CloudApper keeps processing (~50-70 rows/min) after the reply times out
        return "accepted, reply timed out (workflow still running)"
    except (http.client.RemoteDisconnected, ConnectionResetError):  # CloudApper dropped the connection mid-processing
        return "connection dropped by CloudApper (workflow likely still running; verify shifts in CloudApper)"
    except Exception as e:  # report per webhook instead of crashing the other days' posts
        return f"webhook post FAILED: {type(e).__name__}: {e}"


def split_days(per_day):
    """Each shift goes to exactly one day: overnight shifts appear in two days' reports, and two
    workflows creating the same shift at the same time would make a duplicate."""
    seen, out = set(), []
    for rows in per_day:
        keep = []
        for r in rows:
            k = (r.get("Employee_ID"), r.get("Position_ID"), r.get("Start_Date_Time"), r.get("End_Date_Time"))
            if k not in seen:
                seen.add(k); keep.append(r)
        out.append(keep)
    return out


if __name__ == "__main__" and sys.argv[1:2] == ["--3days"]:
    today = datetime.date.today()
    days = [(today + datetime.timedelta(i)).isoformat() for i in range(3)]
    hooks = [cfg("WEBHOOK_URL"), cfg("WEBHOOK_URL_2"), cfg("WEBHOOK_URL_3")]
    with ThreadPoolExecutor(3) as ex:
        per_day = split_days(list(ex.map(lambda d: fetch(d, d), days)))
        results = list(ex.map(post, hooks, per_day))
    for d, rows, res in zip(days, per_day, results):
        print(f"{d}: {len(rows)} rows -> webhook {res}")
elif __name__ == "__main__":
    start = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    end = sys.argv[2] if len(sys.argv) > 2 else start
    rows = fetch(start, end)
    print(f"{start}..{end}: {len(rows)} rows -> webhook {post(sys.argv[3] if len(sys.argv) > 3 else cfg('WEBHOOK_URL'), rows)}")

assert split_days([[{"Employee_ID": 1, "Start_Date_Time": "a"}], [{"Employee_ID": 1, "Start_Date_Time": "a"}, {"Employee_ID": 2}]]) == [[{"Employee_ID": 1, "Start_Date_Time": "a"}], [{"Employee_ID": 2}]]
