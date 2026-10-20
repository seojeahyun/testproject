import datetime as dt
import os

from . import strategy
from .data import fetch_closes
from .rsi import compute_rsi


def market_open(cfg, now=None):
    now = now or dt.datetime.now()
    if now.weekday() >= 5:
        return False
    return cfg["risk"]["market_open"] <= now.strftime("%H:%M") <= cfg["risk"]["market_close"]


def is_live(cfg):
    return (not cfg["dry_run"]) and os.environ.get("LIVE_TRADING", "").lower() == "true"


def run_once(cfg, store, toss=None):
    live = is_live(cfg)
    if live and toss is not None:
        try:  # 실제 보유 현황으로 동기화
            for sym, (q, a) in toss.holdings().items():
                store.set_position(sym, q, a)
        except Exception as e:
            store.add_error("holdings", e)
            return
    for sym in cfg["symbols"]:
        try:
            closes, _ = fetch_closes(sym, toss)
            rsi = compute_rsi(closes, cfg["rsi"]["period"])
            if rsi is None:
                continue
            price = closes[-1]
            if toss is not None:
                try:
                    price = toss.price(sym)
                except Exception:
                    pass
            qty, avg = store.position(sym)
            signal = strategy.decide(strategy.Context(rsi, price, qty, avg, cfg))
            store.add_signal(sym, rsi, price, qty, avg, signal)
            if signal == "HOLD" or not market_open(cfg):
                continue
            _execute(cfg, store, toss, live, sym, signal, price, qty, avg)
        except Exception as e:
            store.add_error(sym, e)


def _execute(cfg, store, toss, live, sym, signal, price, qty, avg):
    if signal == "BUY":
        budget = min(cfg["order"]["buy_amount_krw"], cfg["order"]["max_daily_krw"] - store.spent_today())
        n = int(budget // price)
        if n < 1:
            return
        side, order_qty = "BUY", n
    else:
        side, order_qty = "SELL", qty
    status, detail = "DRY_RUN", ""
    if live:
        try:
            detail = str(toss.order(sym, side, order_qty))
            status = "SENT"
        except Exception as e:
            status, detail = "ERROR", str(e)
    store.add_order(sym, side, order_qty, price, not live, status, detail)
    if status in ("DRY_RUN", "SENT"):  # 모의 모드에서도 포지션을 가상으로 추적
        if side == "BUY":
            store.set_position(sym, order_qty, price)
        else:
            store.set_position(sym, 0, 0.0)
