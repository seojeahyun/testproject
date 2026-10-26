"""미국 주식 거래량 급증 + 가격 변화 작은 종목 스크리너.

조건: 기준일 거래량 >= 직전 N거래일 평균 거래량 * MULT, 그리고 |등락률| <= MAX_CHANGE(%)
사용: python us_volume_screener.py [--date YYYY-MM-DD] [--window 20] [--mult 3] [--max-change 3]
필요: pip install yfinance pandas
유니버스: NASDAQ Trader 상장 목록(ETF/테스트종목 제외)
"""
import argparse
import io
import urllib.request
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

URLS = [
    "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt",
    "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt",
]


def last_friday(today=None):
    d = today or date.today()
    return d - timedelta(days=(d.weekday() - 4) % 7)


def universe():
    frames = []
    for u in URLS:
        raw = urllib.request.urlopen(u, timeout=30).read().decode()
        df = pd.read_csv(io.StringIO(raw), sep="|")
        df = df[~df.iloc[:, 0].astype(str).str.startswith("File Creation")]
        sym = "Symbol" if "Symbol" in df else "ACT Symbol"
        df = df[(df["ETF"] == "N") & (df["Test Issue"] == "N")]
        frames.append(df[[sym, "Security Name"]].rename(columns={sym: "Symbol"}))
    uni = pd.concat(frames).drop_duplicates("Symbol")
    uni = uni[uni["Symbol"].str.fullmatch(r"[A-Z]{1,5}")]  # 우선주/워런트 등 제외
    return uni.set_index("Symbol")["Security Name"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=last_friday().isoformat())
    p.add_argument("--window", type=int, default=20)
    p.add_argument("--mult", type=float, default=3.0)
    p.add_argument("--max-change", type=float, default=3.0)
    p.add_argument("--min-volume", type=int, default=100000, help="평균 거래량 최소치")
    p.add_argument("--min-price", type=float, default=1.0)
    a = p.parse_args()

    target = pd.Timestamp(a.date)
    names = universe()
    tickers = list(names.index)
    start = (target - timedelta(days=a.window * 2 + 10)).strftime("%Y-%m-%d")
    end = (target + timedelta(days=1)).strftime("%Y-%m-%d")

    rows = []
    for i in range(0, len(tickers), 400):
        batch = tickers[i:i + 400]
        data = yf.download(batch, start=start, end=end, auto_adjust=False,
                           progress=False, group_by="column", threads=True)
        if data.empty:
            continue
        close, vol = data["Close"], data["Volume"]
        if target not in close.index:
            raise SystemExit(f"{a.date} 데이터가 없습니다(휴장일이거나 아직 미반영).")
        for t in close.columns:
            c, v = close[t].dropna(), vol[t].dropna()
            if target not in c.index or len(c) < a.window + 1:
                continue
            c, v = c[:target], v[:target]
            prev_vol = v.iloc[-a.window - 1:-1]
            avg = prev_vol.mean()
            if not avg or avg < a.min_volume or c.iloc[-1] < a.min_price:
                continue
            chg = (c.iloc[-1] / c.iloc[-2] - 1) * 100
            mult = v.iloc[-1] / avg
            if mult >= a.mult and abs(chg) <= a.max_change:
                rows.append((t, names[t], c.iloc[-1], chg, v.iloc[-1], avg, mult))

    out = pd.DataFrame(rows, columns=["Symbol", "Name", "Close", "Change%", "Volume", "AvgVolume", "VolMultiple"])
    out = out.sort_values("VolMultiple", ascending=False).round(2)
    fname = f"us_result_{a.date}.csv"
    out.to_csv(fname, index=False)
    print(out.to_string(index=False))
    print(f"\n{len(out)} stocks -> {fname}")


if __name__ == "__main__":
    main()
