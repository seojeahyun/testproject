"""한국(KOSPI/KOSDAQ) 거래량 급증 + 가격 변화 작은 종목 스크리너.

조건: 기준일 거래량 >= 직전 N거래일 평균 거래량 * MULT, 그리고 |등락률| <= MAX_CHANGE(%)
사용: python kr_volume_screener.py [--date YYYYMMDD] [--window 20] [--mult 3] [--max-change 3]
필요: pip install pykrx pandas
(KRX 정보데이터시스템이 로그인을 요구하면 환경변수 KRX_ID, KRX_PW를 설정하세요.)
"""
import argparse
from datetime import date, datetime, timedelta

import pandas as pd
from pykrx import stock


def last_friday(today=None):
    d = today or date.today()
    return d - timedelta(days=(d.weekday() - 4) % 7)


def snapshot(day):
    df = stock.get_market_ohlcv_by_ticker(day, market="ALL")
    if df.empty or df["거래량"].sum() == 0:
        return None  # 휴장일
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=last_friday().strftime("%Y%m%d"))
    p.add_argument("--window", type=int, default=20)
    p.add_argument("--mult", type=float, default=3.0)
    p.add_argument("--max-change", type=float, default=3.0)
    p.add_argument("--min-volume", type=int, default=10000, help="평균 거래량 최소치(잡주 제외)")
    a = p.parse_args()

    target = datetime.strptime(a.date, "%Y%m%d").date()
    today_df = snapshot(a.date)
    if today_df is None:
        raise SystemExit(f"{a.date}은 휴장일이거나 데이터가 없습니다.")

    vols, d = [], target - timedelta(days=1)
    while len(vols) < a.window and (target - d).days < a.window * 3:
        if d.weekday() < 5:
            df = snapshot(d.strftime("%Y%m%d"))
            if df is not None:
                vols.append(df["거래량"].rename(d))
        d -= timedelta(days=1)
    avg = pd.concat(vols, axis=1).mean(axis=1)

    out = today_df.join(avg.rename("평균거래량"), how="inner")
    out["거래량배수"] = out["거래량"] / out["평균거래량"]
    out = out[
        (out["평균거래량"] >= a.min_volume)
        & (out["거래량배수"] >= a.mult)
        & (out["등락률"].abs() <= a.max_change)
    ]
    out.insert(0, "종목명", [stock.get_market_ticker_name(t) for t in out.index])
    out = out[["종목명", "종가", "등락률", "거래량", "평균거래량", "거래량배수"]]
    out = out.sort_values("거래량배수", ascending=False).round(2)

    fname = f"kr_result_{a.date}.csv"
    out.to_csv(fname, encoding="utf-8-sig")
    print(out.to_string())
    print(f"\n{len(out)}개 종목 -> {fname}")


if __name__ == "__main__":
    main()
