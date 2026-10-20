import sqlite3

import pandas as pd
import streamlit as st
import yaml

from bot.trader import is_live

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
st.set_page_config(page_title="RSI 자동매매 현황", layout="wide")
st.title("RSI 자동매매 현황")
st.caption(f"모드: {'🔴 실주문' if is_live(cfg) else '🟢 모의(dry-run)'} · 매수 RSI≤{cfg['rsi']['buy_below']} · 매도 RSI≥{cfg['rsi']['sell_above']} (손실 구간 매도 금지)")

try:
    db = sqlite3.connect(cfg["db_path"])
    q = lambda sql: pd.read_sql(sql, db)
    st.subheader("종목별 최신 신호")
    st.dataframe(q("SELECT symbol, rsi, price, qty, avg_cost, signal, datetime(ts,'unixepoch','localtime') AS time FROM signals WHERE ts IN (SELECT MAX(ts) FROM signals GROUP BY symbol)"), use_container_width=True)
    st.subheader("보유 종목")
    st.dataframe(q("SELECT * FROM positions WHERE qty>0"), use_container_width=True)
    st.subheader("주문 이력")
    st.dataframe(q("SELECT datetime(ts,'unixepoch','localtime') AS time, symbol, side, qty, price, dry_run, status, detail FROM orders ORDER BY ts DESC LIMIT 100"), use_container_width=True)
    st.subheader("오류")
    st.dataframe(q("SELECT datetime(ts,'unixepoch','localtime') AS time, where_, message FROM errors ORDER BY ts DESC LIMIT 50"), use_container_width=True)
except Exception as e:
    st.info(f"아직 데이터가 없습니다. 먼저 main.py 를 실행하세요. ({e})")
