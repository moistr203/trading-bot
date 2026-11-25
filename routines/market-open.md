# Routine: market-open (8:35 AM CT, Mon-Fri)

Read CLAUDE.md and every file in memory/ first. Follow CLAUDE.md exactly.

Step 0 (environment check): run `bash scripts/alpaca.sh account`.
If it prints MISSING_ENV, NETWORK_ERROR, or REFUSED about the endpoint: add a dated
"ALERT" line with the error at the top of memory/DAILY-SUMMARY.md, commit, push, and stop.
Do not create a .env file. Do not use curl. Do not work around it.

1. `clock`. If the market is not open, write one line in TRADE-LOG.md and finish.
2. Fix stops first: for every position without a stop order (see `orders open` and "Stops to fix"),
   place `trail SYM QTY 10`. If refused, place `stop SYM QTY <entry * 0.90>`. Log each one.
3. Cut losers: any position at -7% or worse from entry -> `close SYM`. Log why.
4. Read today's RESEARCH-LOG.md entry. For each BUY-AT-OPEN idea, re-check the buy checklist with a fresh
   `quote` (skip it if it gapped up more than 8% or broke its planned stop level).
   Size per CLAUDE.md, then `buy SYM QTY`. If REFUSED, log it and stop buying.
5. For each buy, wait ~1 minute, check `orders all` for the fill, then place `trail SYM QTY 10`.
   If it hasn't filled, add it to "Stops to fix".
6. Log every order in TRADE-LOG.md (time, symbol, qty, fill price, stop, target, reason).

Final step (always): 
git add memory/ trader/ && git commit -m "<routine name>: <date> <one-line summary>" && git push origin main
If the push is rejected: git pull --rebase origin main, then push again. Never force-push.
If there is nothing to commit, that is fine.
