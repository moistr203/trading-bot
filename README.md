# Trading Bot (Alpaca PAPER + Claude Code routines)

An AI agent that practice-trades US stocks with fake money. Claude wakes up 5 times a
weekday, researches, trades by strict rules, and writes everything it did into `memory/`.

**Paper only.** `scripts/alpaca.py` refuses any non-paper endpoint, and enforces the risk
limits in code (max 6 positions, max 20% per position, max 3 buys/week, no margin, no shorting,
stocks only, stops 5-10%). The agent cannot edit the scripts or rules (`.claude/settings.json`).

## Setup (one time)

1. **Alpaca paper keys.** alpaca.markets → log in → switch to the Paper account →
   API Keys → Generate. Copy the Key and Secret somewhere safe.
2. **Connect GitHub to Claude.** At claude.ai/code, install the Claude GitHub App and give it
   access to this repo only.
3. **Create a cloud environment** (claude.ai/code → environment settings → new environment, name it `trading-bot`):
   - Environment variables:
     ```
     ALPACA_API_KEY=<your paper key>
     ALPACA_SECRET_KEY=<your paper secret>
     ALPACA_ENDPOINT=https://paper-api.alpaca.markets/v2
     SEC_USER_AGENT=Your Name you@example.com
     ```
     (SEC requires a real name + email to read filings. Without it the bot skips SEC data.)
   - Network access: Custom, and add these domains:
     ```
     paper-api.alpaca.markets
     data.alpaca.markets
     query1.finance.yahoo.com
     query2.finance.yahoo.com
     feeds.finance.yahoo.com
     www.nasdaqtrader.com
     www.sec.gov
     data.sec.gov
     disclosures-clerk.house.gov
     ```
     (The first two are required to trade. The rest feed the scanner, news, earnings and Congress tools.)
   - Turn on **allow unrestricted branch pushes** if offered (otherwise pushes to `main` can fail silently).
4. **Create 5 routines** (Routines → New). For each: repo `moistr203/trading-bot`, branch `main`,
   environment `trading-bot`, timezone **America/Chicago**, and paste the one-line prompt:

   | Name | Schedule (cron) | Prompt |
   |---|---|---|
   | Trading pre-market | `0 6 * * 1-5` | `Run the routine in routines/pre-market.md exactly as written.` |
   | Trading market-open | `35 8 * * 1-5` | `Run the routine in routines/market-open.md exactly as written.` |
   | Trading midday | `0 12 * * 1-5` | `Run the routine in routines/midday.md exactly as written.` |
   | Trading daily summary | `10 15 * * 1-5` | `Run the routine in routines/daily-summary.md exactly as written.` |
   | Trading weekly review | `0 16 * * 5` | `Run the routine in routines/weekly-review.md exactly as written.` |

5. **Test.** Click **Run now** on "Trading daily summary". Then check:
   the run transcript shows an `account` result, and a new commit appears in this repo
   updating `memory/DAILY-SUMMARY.md`.

## Research tools
`.claude/skills/` holds 4 read-only tools from the Day Trader skill pack (MIT, by Jake Schincariol):
chart scanner (5,900 US stocks, daily setups), news monitor (Yahoo headlines + SEC 8-Ks),
earnings analyst (filed SEC numbers) and Congress trade tracker. They can't place orders;
all orders still go through the guarded `scripts/alpaca.sh`.

## Dashboard (live)
1. GitHub → this repo → Settings → General → Danger Zone → Change visibility → **Public**.
   (Only paper trades and notes become visible. Keys live in Claude's environment settings, never in the repo.)
2. Settings → Pages → Source: **Deploy from a branch**, Branch: **main**, Folder: **/docs** → Save.
3. After a minute it's live at **https://moistr203.github.io/trading-bot/**. Bookmark it or add it to your phone's home screen.
Every routine run updates `docs/data.json`, and the page refreshes itself every 5 minutes.

## WhatsApp updates (optional, free via CallMeBot)
1. Save **+34 684 783 708** in your phone contacts. In WhatsApp, send it: `I allow callmebot to send me messages`
2. It replies with your API key.
3. In the `trading-bot` environment add:
   ```
   WHATSAPP_PHONE=+1yourphonenumber
   CALLMEBOT_APIKEY=the key it sent you
   ```
   and add `api.callmebot.com` to the network allowlist.

## Watching it
- **Alpaca paper dashboard**: balance, positions, every order, live.
- **This repo**: `memory/DAILY-SUMMARY.md` (plain-English daily recap), `TRADE-LOG.md`
  (every order and why), `RESEARCH-LOG.md` (ideas and sources), `WEEKLY-REVIEW.md` (Fridays).
- **Routines page**: full transcript of each run.

## Stopping it
Pause or delete the routines. To also close everything, use the Alpaca paper dashboard.

## Local test (optional)
```
cp env.template .env   # fill in keys
set -a; source .env; set +a
bash scripts/alpaca.sh account
```
