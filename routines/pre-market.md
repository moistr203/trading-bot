# Routine: pre-market (6:00 AM CT, Mon-Fri)

Read CLAUDE.md and every file in memory/ first. Follow CLAUDE.md exactly.

Step 0 (environment check): run `bash scripts/alpaca.sh account`.
If it prints MISSING_ENV, NETWORK_ERROR, or REFUSED about the endpoint: add a dated
"ALERT" line with the error at the top of memory/DAILY-SUMMARY.md, commit, push, and stop.
Do not create a .env file. Do not use curl. Do not work around it.

1. `bash scripts/alpaca.sh clock`. If today is not a trading day, write one line in RESEARCH-LOG.md and finish.
2. `positions` and `orders open`. Check every position has a stop order. List any that don't under
   "Stops to fix" in TRADE-LOG.md (market-open will fix them).
3. Web-search overnight news: market futures, big economic data today, and news on each position you hold.
   Flag anything that threatens a position (bad earnings, downgrade, lawsuit).
4. Find up to 3 new buy ideas with a real, specific catalyst. For each, check the buy checklist in CLAUDE.md
   using `bars` and `quote`. Skip anything reporting earnings in the next 2 trading days.
5. Write a dated entry at the top of RESEARCH-LOG.md: market mood, risks to current positions,
   ideas (with source URLs, entry/stop/target, and PASS or WATCH or BUY-AT-OPEN verdict).
   Do NOT place any orders in this routine.

Final step (always): 
git add memory/ && git commit -m "<routine name>: <date> <one-line summary>" && git push origin main
If the push is rejected: git pull --rebase origin main, then push again. Never force-push.
If there is nothing to commit, that is fine.
