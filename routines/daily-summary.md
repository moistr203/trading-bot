# Routine: daily-summary (3:10 PM CT, Mon-Fri, after the close)

Read CLAUDE.md and every file in memory/ first. Follow CLAUDE.md exactly.

Step 0 (environment check): run `bash scripts/alpaca.sh account`.
If it prints MISSING_ENV, NETWORK_ERROR, or REFUSED about the endpoint: add a dated
"ALERT" line with the error at the top of memory/DAILY-SUMMARY.md, commit, push, and stop.
Do not create a .env file. Do not use curl. Do not work around it.

1. `account`, `positions`, `orders open`, `orders closed`.
2. Check every position still has a stop order. Note any that don't under "Stops to fix" in TRADE-LOG.md.
3. Write a dated entry at the top of memory/DAILY-SUMMARY.md, in plain English for a beginner:
   - Equity now, change today (equity vs last_equity) in $ and %, total change since Day 0 in TRADE-LOG.md.
   - Each position: shares, entry, price now, P/L %, stop level.
   - What the bot did today and why (one or two sentences per action), or "No trades today" and why.
   - Buys used this week (`weekcount`) and anything to watch tomorrow.

Notify (always): `bash scripts/notify.sh "<Trading bot, date: equity, today's $ and %, positions with P/L, what it did today in one line>"`.
Keep messages short and plain English. Notification problems never stop the run.

Final step (always):
bash scripts/alpaca.sh snapshot   (updates the dashboard; if it fails, note it and continue)
git add memory/ trader/ docs/data.json && git commit -m "<routine name>: <date> <one-line summary>" && git push origin main
If the push is rejected: git pull --rebase origin main, then push again. Never force-push.
If there is nothing to commit, that is fine.
