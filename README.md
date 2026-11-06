# Attrium-Daily-Tasks

`push_schedule.py` pulls Atrium's Workday "Schedule blocks - Cloudapper" report for a date range and POSTs the rows as JSON to a webhook.

```bash
python push_schedule.py                        # today
python push_schedule.py 2026-11-06 2026-11-12  # date range, one call
```

Set `USERNAME`, `PASSWORD`, `WEBHOOK_URL` as environment variables (or in a local `.env`, which is git-ignored).
Each run makes one ~3-minute report call and never retries; do not run it in parallel against production.
