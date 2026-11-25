#!/usr/bin/env python3
"""Paper-only Alpaca wrapper with hard guardrails.

This is the ONLY way the agent talks to Alpaca. It refuses to run against
anything but the paper endpoint, and it enforces the risk rules in code so a
bad decision by the model cannot get past them.

Usage: bash scripts/alpaca.sh <command> [args]
  account                      equity, cash, buying power, day-trade count
  positions                    open positions with P/L
  orders [open|closed|all]     orders (default: open)
  clock                        is the market open, next open/close
  quote SYM                    latest trade price
  bars SYM [DAYS]              daily bars (default 30 days)
  buy SYM QTY                  market buy (guarded)
  trail SYM QTY PCT            GTC trailing-stop sell, PCT 5-10
  stop SYM QTY PRICE           GTC stop sell below current price
  sell SYM QTY                 market sell (cancels SYM's open orders first)
  close SYM                    close whole position (cancels SYM's orders first)
  cancel ORDER_ID              cancel one order
  weekcount                    buys placed this week (Mon-today, Chicago time)
  snapshot                     write docs/data.json for the public dashboard
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# ---- Hard limits (mirror CLAUDE.md; code wins if they ever disagree) ----
MAX_POSITIONS = 6
MAX_POSITION_PCT = 0.20
MAX_BUYS_PER_WEEK = 3
TRAIL_MIN, TRAIL_MAX = 5.0, 10.0
PDT_EQUITY = 25000
TZ = ZoneInfo("America/Chicago")


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def need_env(name):
    v = os.environ.get(name, "").strip()
    if not v:
        die(f"MISSING_ENV {name}: set it in the routine's environment settings. "
            "Do NOT create a .env file as a workaround.", 3)
    return v


KEY = need_env("ALPACA_API_KEY")
SECRET = need_env("ALPACA_SECRET_KEY")

_base = os.environ.get("ALPACA_ENDPOINT", "https://paper-api.alpaca.markets/v2").strip().rstrip("/")
if _base.endswith("/v2"):
    _base = _base[:-3]
if _base != "https://paper-api.alpaca.markets":
    die(f"REFUSED: ALPACA_ENDPOINT={_base} is not the paper endpoint. "
        "This bot is paper-only.", 2)
TRADE = _base + "/v2"
DATA = os.environ.get("ALPACA_DATA_ENDPOINT", "https://data.alpaca.markets").strip().rstrip("/")
if DATA.endswith("/v2"):
    DATA = DATA[:-3]
DATA += "/v2"


def call(method, url, body=None, ok404=False):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "APCA-API-KEY-ID": KEY,
        "APCA-API-SECRET-KEY": SECRET,
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt.strip() else {}
    except urllib.error.HTTPError as e:
        if ok404 and e.code == 404:
            return None
        die(f"HTTP {e.code} {method} {url.split('?')[0]}: {e.read().decode()[:500]}")
    except urllib.error.URLError as e:
        die(f"NETWORK_ERROR {method} {url.split('?')[0]}: {e.reason}. "
            "Check the environment's network allowlist includes "
            "paper-api.alpaca.markets and data.alpaca.markets.")


def t(path, method="GET", body=None, ok404=False):
    return call(method, TRADE + path, body, ok404)


def out(obj):
    print(json.dumps(obj, indent=2))


def sym_arg(s):
    s = s.strip().upper()
    if not s.replace(".", "").isalpha() or len(s) > 6:
        die(f"Bad symbol: {s}")
    return s


def int_arg(s, name="QTY"):
    try:
        v = int(s)
    except ValueError:
        die(f"{name} must be a whole number, got {s}")
    if v <= 0:
        die(f"{name} must be > 0")
    return v


def latest_price(sym):
    r = call("GET", f"{DATA}/stocks/{sym}/trades/latest?feed=iex")
    p = float(r["trade"]["p"])
    if p <= 0:
        die(f"No valid price for {sym}")
    return p


def held_qty(sym):
    p = t(f"/positions/{sym}", ok404=True)
    return 0 if p is None else int(float(p["qty"]))


def open_orders(sym=None):
    q = "?status=open&limit=500"
    if sym:
        q += "&symbols=" + sym
    return t("/orders" + q)


def cancel_symbol_orders(sym):
    n = 0
    for o in open_orders(sym):
        t(f"/orders/{o['id']}", "DELETE")
        n += 1
    return n


def week_buys():
    now = datetime.now(TZ)
    monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    after = urllib.parse.quote(monday.isoformat())
    orders = t(f"/orders?status=all&limit=500&after={after}")
    dead = {"canceled", "expired", "rejected"}
    return [o for o in orders if o["side"] == "buy" and o["status"] not in dead]


# ---------------- commands ----------------

def cmd_account(_):
    a = t("/account")
    out({k: a.get(k) for k in ("status", "equity", "last_equity", "cash", "buying_power",
                               "long_market_value", "daytrade_count", "pattern_day_trader")})


def cmd_positions(_):
    out([{
        "symbol": p["symbol"], "qty": p["qty"], "avg_entry": p["avg_entry_price"],
        "price": p["current_price"], "market_value": p["market_value"],
        "pl_pct": round(float(p["unrealized_plpc"]) * 100, 2),
        "pl_today_pct": round(float(p["unrealized_intraday_plpc"]) * 100, 2),
    } for p in t("/positions")])


def cmd_orders(args):
    status = args[0] if args else "open"
    if status not in ("open", "closed", "all"):
        die("orders [open|closed|all]")
    out([{k: o.get(k) for k in ("id", "symbol", "side", "type", "qty", "filled_qty",
                                 "filled_avg_price", "status", "trail_percent", "stop_price",
                                 "time_in_force", "submitted_at")}
         for o in t(f"/orders?status={status}&limit=100")])


def cmd_clock(_):
    out(t("/clock"))


def cmd_quote(args):
    if len(args) != 1:
        die("quote SYM")
    s = sym_arg(args[0])
    out({"symbol": s, "price": latest_price(s)})


def cmd_bars(args):
    if not args:
        die("bars SYM [DAYS]")
    s = sym_arg(args[0])
    days = int_arg(args[1], "DAYS") if len(args) > 1 else 30
    start = (datetime.now(timezone.utc) - timedelta(days=int(days * 1.6) + 5)).strftime("%Y-%m-%d")
    r = call("GET", f"{DATA}/stocks/{s}/bars?timeframe=1Day&start={start}&limit=1000&feed=iex")
    bars = (r.get("bars") or [])[-days:]
    out([{"date": b["t"][:10], "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
         for b in bars])


def cmd_weekcount(_):
    b = week_buys()
    out({"buys_this_week": len(b), "limit": MAX_BUYS_PER_WEEK,
         "symbols": [o["symbol"] for o in b]})


def cmd_buy(args):
    if len(args) != 2:
        die("buy SYM QTY")
    s, qty = sym_arg(args[0]), int_arg(args[1])

    asset = t(f"/assets/{s}", ok404=True)
    if not asset or asset.get("class") != "us_equity" or not asset.get("tradable"):
        die(f"REFUSED: {s} is not a tradable US stock.")
    if not t("/clock")["is_open"]:
        die("REFUSED: market is closed. Buys only while the market is open.")

    a = t("/account")
    equity, cash = float(a["equity"]), float(a["cash"])
    price = latest_price(s)
    cost = price * qty
    already = held_qty(s)
    existing_value = already * price
    positions = t("/positions")
    pending_buys = [o for o in open_orders() if o["side"] == "buy"]
    count_after = len({p["symbol"] for p in positions} | {o["symbol"] for o in pending_buys} | {s})
    weekly = len(week_buys())

    fails = []
    if count_after > MAX_POSITIONS:
        fails.append(f"positions after fill {count_after} > {MAX_POSITIONS}")
    if existing_value + cost > MAX_POSITION_PCT * equity:
        fails.append(f"position value ${existing_value + cost:,.0f} > 20% of equity (${MAX_POSITION_PCT * equity:,.0f})")
    if cost > cash:
        fails.append(f"cost ${cost:,.0f} > cash ${cash:,.0f} (no margin)")
    if weekly >= MAX_BUYS_PER_WEEK:
        fails.append(f"already {weekly} buys this week (max {MAX_BUYS_PER_WEEK})")
    if equity < PDT_EQUITY and int(a.get("daytrade_count", 0)) >= 3:
        fails.append("day-trade count at PDT limit")
    if fails:
        die("REFUSED buy " + s + ": " + "; ".join(fails))

    o = t("/orders", "POST", {"symbol": s, "qty": str(qty), "side": "buy",
                              "type": "market", "time_in_force": "day"})
    out({"placed": "buy", "symbol": s, "qty": qty, "est_price": price, "est_cost": round(cost, 2),
         "order_id": o["id"], "status": o["status"],
         "next_step": f"Once filled, set a stop: bash scripts/alpaca.sh trail {s} {qty} 10"})


def cmd_trail(args):
    if len(args) != 3:
        die("trail SYM QTY PCT")
    s, qty = sym_arg(args[0]), int_arg(args[1])
    try:
        pct = float(args[2])
    except ValueError:
        die("PCT must be a number")
    if not TRAIL_MIN <= pct <= TRAIL_MAX:
        die(f"REFUSED: trail percent must be {TRAIL_MIN}-{TRAIL_MAX}")
    if qty > held_qty(s):
        die(f"REFUSED: qty {qty} > shares held of {s}")
    o = t("/orders", "POST", {"symbol": s, "qty": str(qty), "side": "sell", "type": "trailing_stop",
                              "trail_percent": str(pct), "time_in_force": "gtc"})
    out({"placed": "trailing_stop", "symbol": s, "qty": qty, "trail_percent": pct,
         "order_id": o["id"], "status": o["status"]})


def cmd_stop(args):
    if len(args) != 3:
        die("stop SYM QTY PRICE")
    s, qty = sym_arg(args[0]), int_arg(args[1])
    try:
        sp = round(float(args[2]), 2)
    except ValueError:
        die("PRICE must be a number")
    if qty > held_qty(s):
        die(f"REFUSED: qty {qty} > shares held of {s}")
    if sp >= latest_price(s):
        die("REFUSED: stop price must be below the current price")
    o = t("/orders", "POST", {"symbol": s, "qty": str(qty), "side": "sell", "type": "stop",
                              "stop_price": str(sp), "time_in_force": "gtc"})
    out({"placed": "stop", "symbol": s, "qty": qty, "stop_price": sp,
         "order_id": o["id"], "status": o["status"]})


def cmd_sell(args):
    if len(args) != 2:
        die("sell SYM QTY")
    s, qty = sym_arg(args[0]), int_arg(args[1])
    held = held_qty(s)
    if qty > held:
        die(f"REFUSED: qty {qty} > shares held ({held}). No short selling.")
    if not t("/clock")["is_open"]:
        die("REFUSED: market is closed.")
    n = cancel_symbol_orders(s)
    o = t("/orders", "POST", {"symbol": s, "qty": str(qty), "side": "sell",
                              "type": "market", "time_in_force": "day"})
    out({"placed": "sell", "symbol": s, "qty": qty, "canceled_orders": n,
         "order_id": o["id"], "status": o["status"],
         "note": "If shares remain, re-place their stop." if qty < held else ""})


def cmd_close(args):
    if len(args) != 1:
        die("close SYM")
    s = sym_arg(args[0])
    if held_qty(s) == 0:
        die(f"No position in {s}")
    if not t("/clock")["is_open"]:
        die("REFUSED: market is closed.")
    n = cancel_symbol_orders(s)
    o = t(f"/positions/{s}", "DELETE")
    out({"closed": s, "canceled_orders": n, "order_id": o.get("id"), "status": o.get("status")})


def cmd_cancel(args):
    if len(args) != 1:
        die("cancel ORDER_ID")
    t(f"/orders/{args[0]}", "DELETE")
    out({"canceled": args[0]})


def _latest_entry(path, max_chars=4000):
    """First '## ' section of a memory file (newest entry), as plain text."""
    try:
        txt = open(path, encoding="utf-8").read()
    except OSError:
        return ""
    parts = txt.split("\n## ")
    if len(parts) < 2:
        return ""
    return ("## " + parts[1]).strip()[:max_chars]


def cmd_snapshot(_):
    """Write docs/data.json for the public dashboard. Never includes keys."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    a = t("/account")
    positions = t("/positions")
    opens = open_orders()
    closed = t("/orders?status=closed&limit=50&direction=desc")
    hist = t("/account/portfolio/history?period=3M&timeframe=1D")
    stops = {}
    for o in opens:
        if o["side"] == "sell" and o["type"] in ("trailing_stop", "stop"):
            stops[o["symbol"]] = {"type": o["type"], "trail_percent": o.get("trail_percent"),
                                  "stop_price": o.get("stop_price") or o.get("hwm")}
    pts = [(ts, eq) for ts, eq in zip(hist.get("timestamp") or [], hist.get("equity") or [])
           if eq is not None and float(eq) > 0]
    spy = []
    if pts:
        start = datetime.fromtimestamp(pts[0][0], timezone.utc).strftime("%Y-%m-%d")
        try:
            r = call("GET", f"{DATA}/stocks/SPY/bars?timeframe=1Day&start={start}&limit=1000&feed=iex")
            spy = [{"date": b["t"][:10], "close": b["c"]} for b in (r.get("bars") or [])]
        except SystemExit:
            spy = []
    mem = os.path.join(root, "memory")
    data = {
        "generated_at": datetime.now(TZ).isoformat(timespec="minutes"),
        "account": {k: a.get(k) for k in ("equity", "last_equity", "cash", "long_market_value",
                                          "buying_power", "daytrade_count")},
        "positions": [{
            "symbol": p["symbol"], "qty": p["qty"], "avg_entry": p["avg_entry_price"],
            "price": p["current_price"], "market_value": p["market_value"],
            "pl": p["unrealized_pl"], "pl_pct": round(float(p["unrealized_plpc"]) * 100, 2),
            "stop": stops.get(p["symbol"]),
        } for p in positions],
        "open_orders": [{k: o.get(k) for k in ("symbol", "side", "type", "qty", "trail_percent",
                                                "stop_price", "status", "submitted_at")} for o in opens],
        "recent_orders": [{k: o.get(k) for k in ("symbol", "side", "type", "qty", "filled_qty",
                                                  "filled_avg_price", "status", "filled_at", "submitted_at")}
                          for o in closed],
        "equity_history": [{"date": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d"), "equity": float(eq)}
                           for ts, eq in pts],
        "spy_history": spy,
        "buys_this_week": len(week_buys()),
        "limits": {"max_positions": MAX_POSITIONS, "max_position_pct": MAX_POSITION_PCT * 100,
                   "max_buys_per_week": MAX_BUYS_PER_WEEK},
        "latest": {
            "daily_summary": _latest_entry(os.path.join(mem, "DAILY-SUMMARY.md")),
            "research": _latest_entry(os.path.join(mem, "RESEARCH-LOG.md")),
            "weekly_review": _latest_entry(os.path.join(mem, "WEEKLY-REVIEW.md")),
        },
    }
    os.makedirs(os.path.join(root, "docs"), exist_ok=True)
    with open(os.path.join(root, "docs", "data.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    print(f"snapshot written: docs/data.json ({len(data['positions'])} positions, "
          f"{len(pts)} equity points)")


CMDS = {k[4:]: v for k, v in globals().items() if k.startswith("cmd_")}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        die(__doc__)
    CMDS[sys.argv[1]](sys.argv[2:])
