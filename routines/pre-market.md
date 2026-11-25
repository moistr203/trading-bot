# Routine: pre-market (6:00 AM CT, Mon-Fri)

Read CLAUDE.md and every file in memory/ first. Follow CLAUDE.md exactly.

Step 0 (environment check): run `bash scripts/alpaca.sh account`.
If it prints MISSING_ENV, NETWORK_ERROR, or REFUSED about the endpoint: add a dated
"ALERT" line with the error at the top of memory/DAILY-SUMMARY.md, commit, push, and stop.
Do not create a .env file. Do not use curl. Do not work around it.

1. `bash scripts/alpaca.sh clock`. If today is not a trading day, write one line in RESEARCH-LOG.md and finish.
2. `positions` and `orders open`. Check every position has a stop order. List any that don't under
   "Stops to fix" in TRADE-LOG.md (market-open will fix them).
3. News on what you hold: `python3 .claude/skills/trader-news/news.py --tickers <held symbols> --hours 24`,
   plus a web search for market futures and today's big economic data.
   Flag anything that threatens a position (`!` 8-K, earnings, downgrade, lawsuit).
4. Scan: if `trader/universe.txt` is missing or older than 7 days, run
   `python3 .claude/skills/trader-scanner/scan.py universe`. Then
   `python3 .claude/skills/trader-scanner/scan.py daily --show 40`.
   Keep only `breakout_20d`, `bull_flag`, `reclaim_ma20` hits, most traded first, top 15.
   If the scanner fails, fall back to web search for today's movers and say so.
5. News on the top 15: `python3 .claude/skills/trader-news/news.py --tickers <those symbols> --hours 48`.
   Keep the ones with a real, specific catalyst. Open the story or filing to confirm it.
6. For the survivors (max 5): `python3 .claude/skills/trader-analyst/facts.py SYM` for earnings quality,
   and check the next earnings date (news/web). Skip anything reporting in the next 2 trading days.
   Optional: `python3 .claude/skills/trader-pelosi/ptr.py new` and note any Congress buys of these names.
7. Run the full buy checklist in CLAUDE.md on the best 1-3 using `bars` and `quote` (and `bars <sector ETF>`).
8. Write a dated entry at the top of RESEARCH-LOG.md: market mood, risks to current positions,
   scanner stats (scanned / hits kept), ideas with source URLs, setup name, entry/stop/target,
   and PASS or WATCH or BUY-AT-OPEN verdict.
   Do NOT place any orders in this routine.

Final step (always): 
git add memory/ trader/ && git commit -m "<routine name>: <date> <one-line summary>" && git push origin main
If the push is rejected: git pull --rebase origin main, then push again. Never force-push.
If there is nothing to commit, that is fine.
