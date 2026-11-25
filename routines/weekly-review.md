# Routine: weekly-review (4:00 PM CT, Fridays)

Read CLAUDE.md and every file in memory/ first. Follow CLAUDE.md exactly.

Step 0 (environment check): run `bash scripts/alpaca.sh account`.
If it prints MISSING_ENV, NETWORK_ERROR, or REFUSED about the endpoint: add a dated
"ALERT" line with the error at the top of memory/DAILY-SUMMARY.md, commit, push, and stop.
Do not create a .env file. Do not use curl. Do not work around it.

1. `account`, `positions`, `orders closed`. Read this week's entries in TRADE-LOG.md, RESEARCH-LOG.md, DAILY-SUMMARY.md.
2. Write a dated entry at the top of memory/WEEKLY-REVIEW.md:
   - Equity start of week vs now, $ and %. Compare with SPY over the same week (`bars SPY 6`).
   - Every closed trade: entry, exit, P/L %, was the catalyst right?
   - Win rate, average win, average loss.
   - Any rule broken or any REFUSED message, and why it happened.
   - Sector losing streaks (2 losses in a row -> that sector is paused 2 weeks; note the end date).
   - 1-3 lessons, plain English.
3. Append the lessons (dated) under "Lessons" in memory/TRADING-STRATEGY.md. Do not change the hard rules.

Notify (always): `bash scripts/notify.sh "<Week recap: equity change vs SPY, trades, win rate, top lesson>"`.
Keep messages short and plain English. Notification problems never stop the run.

Final step (always):
bash scripts/alpaca.sh snapshot   (updates the dashboard; if it fails, note it and continue)
git add memory/ trader/ docs/data.json && git commit -m "<routine name>: <date> <one-line summary>" && git push origin main
If the push is rejected: git pull --rebase origin main, then push again. Never force-push.
If there is nothing to commit, that is fine.
Cleanup: if `git branch --show-current` starts with `claude/`, make sure the commit is on origin/main
(`git push origin HEAD:main` if it isn't), then delete that run branch: `git push origin --delete <that branch>`.
Never delete `main` or any branch not created by this run.
