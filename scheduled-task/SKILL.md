---
name: atrium-schedule-to-webhook
description: Pull today + next 2 days of Atrium Workday schedules in parallel and post each day to its own CloudApper webhook
---

Run this exact command once and report its output lines (or the error):

python -I "C:\Users\jorge\OneDrive\Documents\Claude Projects\Atrium\push_schedule.py" --3days

It reads USERNAME, PASSWORD, WEBHOOK_URL, WEBHOOK_URL_2 and WEBHOOK_URL_3 from the .env in that folder, pulls today's, tomorrow's and the day-after's schedules from Atrium's Workday in three parallel calls (about 5 minutes; use a 15-minute timeout), and posts each day to its own CloudApper webhook.

Rules:
- Run it ONCE. Never retry on failure: repeated calls load Atrium's production Workday (they once disabled our integration user for excessive calls). Just report the error.
- A line ending in "accepted, reply timed out (workflow still running)" is a success.
- Do not print or echo the .env contents or any credentials.
- Do not modify the script or .env.
- Final answer: the three output lines (date, row count, webhook result) or the error.