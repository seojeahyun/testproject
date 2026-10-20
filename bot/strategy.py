"""매수/매도 신호. 조건은 함수 목록이라 규칙을 쉽게 추가할 수 있다."""
from dataclasses import dataclass


@dataclass
class Context:
    rsi: float
    price: float
    qty: int           # 보유 수량
    avg_cost: float    # 평단가
    cfg: dict


# 매수 조건: 모두 True 여야 매수
def buy_rsi_low(c):
    return c.rsi <= c.cfg["rsi"]["buy_below"]


def buy_not_holding(c):
    return c.qty == 0


# 매도 조건: 모두 True 여야 매도
def sell_rsi_recovered(c):
    return c.rsi >= c.cfg["rsi"]["sell_above"]


def sell_no_loss(c):
    """손해 보고 팔지 않는다: 평단 대비 min_profit_pct 이상일 때만."""
    need = c.avg_cost * (1 + c.cfg["risk"]["min_profit_pct"] / 100)
    return c.qty > 0 and c.price >= need


BUY_RULES = [buy_rsi_low, buy_not_holding]
SELL_RULES = [sell_rsi_recovered, sell_no_loss]


def decide(ctx):
    if ctx.qty > 0:
        return "SELL" if all(r(ctx) for r in SELL_RULES) else "HOLD"
    return "BUY" if all(r(ctx) for r in BUY_RULES) else "HOLD"
