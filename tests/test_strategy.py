from bot.strategy import Context, decide

CFG = {"rsi": {"buy_below": 30, "sell_above": 33}, "risk": {"min_profit_pct": 0.5}}


def test_buy_when_oversold():
    assert decide(Context(28, 100, 0, 0, CFG)) == "BUY"


def test_no_buy_when_not_oversold():
    assert decide(Context(40, 100, 0, 0, CFG)) == "HOLD"


def test_sell_when_recovered_with_profit():
    assert decide(Context(34, 102, 5, 100, CFG)) == "SELL"


def test_never_sell_at_loss():
    assert decide(Context(60, 95, 5, 100, CFG)) == "HOLD"


def test_hold_if_rsi_not_recovered():
    assert decide(Context(31, 110, 5, 100, CFG)) == "HOLD"
