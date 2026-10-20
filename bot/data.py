def fetch_closes(symbol, toss=None, count=100):
    """종가 목록(오래된 순). 토스 API 우선, 실패하면 yfinance 로 대체."""
    if toss is not None:
        try:
            closes = toss.candles(symbol, count)
            if closes:
                return closes, "toss"
        except Exception:
            pass
    import yfinance as yf
    for suffix in (".KS", ".KQ"):
        df = yf.Ticker(symbol + suffix).history(period="6mo")
        if not df.empty:
            return df["Close"].tolist(), "yfinance"
    raise RuntimeError(f"{symbol}: 시세 데이터를 가져오지 못했습니다")
