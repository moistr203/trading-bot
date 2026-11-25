# Routine: midday (12:00 PM CT, Mon-Fri)

Read CLAUDE.md and every file in memory/ first. Follow CLAUDE.md exactly.

Step 0 (environment check): run `bash scripts/alpaca.sh account`.
If it prints MISSING_ENV, NETWORK_ERROR, or REFUSED about the endpoint: add a dated
"ALERT" line with the error at the top of memory/DAILY-SUMMARY.md, commit, push, and stop.
Do not create a .env file. Do not use curl. Do not work around it.

1. `clock`. If closed, finish.
2. `positions` and `orders open`.
3. For each position:
   - At -7% or worse from entry: `close SYM`. Log it.
   - At +20% or more: tighten trail to 5% (cancel old stop, place `trail SYM QTY 5`) unless that breaks the 3% rule.
   - At +15% or more: tighten trail to 7% the same way.
   - Missing a stop: place one now.
4. `python3 .claude/skills/trader-news/news.py --tickers <held symbols> --hours 6`, then confirm anything
   important with web search. If there is clearly bad news (fraud, guidance cut,
   major downgrade), close it and log why.
5. Do NOT open new positions at midday unless a BUY-AT-OPEN idea from today's research log could not be
   bought at open and still passes the full checklist.
6. Log any action in TRADE-LOG.md. If nothing needed doing, write one line saying so.

Notify: only if you closed a position or tightened a stop, send `bash scripts/notify.sh "<what and why>"`.
Keep messages short and plain English. Notification problems never stop the run.

Final step (always):
bash scripts/alpaca.sh snapshot   (updates the dashboard; if it fails, note it and continue)
git add memory/ trader/ docs/data.json && git commit -m "<routine name>: <date> <one-line summary>" && git push origin main
If the push is rejected: git pull --rebase origin main, then push again. Never force-push.
If there is nothing to commit, that is fine.
