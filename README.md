# Attrium-Daily-Tasks

`push_schedule.py` pulls Atrium's Workday "Schedule blocks - Cloudapper" report for a date range and POSTs the rows as JSON to a webhook.

```bash
python push_schedule.py                        # today
python push_schedule.py 2026-11-06 2026-11-12  # date range, one call
python push_schedule.py --3days                # today, tomorrow, day after; one webhook per day
```

Set `USERNAME`, `PASSWORD`, `WEBHOOK_URL` (plus `WEBHOOK_URL_2`, `WEBHOOK_URL_3` for `--3days`) as environment variables (or in a local `.env`, which is git-ignored).
Each report call takes ~3 minutes and is never retried. `--3days` runs its three Workday calls sequentially (about 9-10 minutes total), never in parallel; only the three webhook posts run in parallel.
