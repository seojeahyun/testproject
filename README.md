# testproject

토스증권 Open API로 국내 주식 RSI(14) 기반 자동매매를 하는 프로그램.

- 매수: RSI ≤ 30 (미보유 종목)
- 매도: RSI ≥ 33 **그리고** 현재가 ≥ 평단 × (1 + `min_profit_pct`) — 손실 구간에서는 팔지 않음
- 기본은 모의(dry-run). 실주문은 `config.yaml`의 `dry_run: false` **와** 환경변수 `LIVE_TRADING=true` 가 모두 필요

## 실행
```
pip install -r requirements.txt
cp .env.example .env   # 키 입력 후 export 하거나 환경변수로 설정
python main.py          # 매매 루프
streamlit run dashboard.py   # 현황 화면
pytest
```

## 주의
`bot/toss_client.py`의 API 경로·필드명(`PATHS`, `TODO`)은 공식 명세로 검증되지 않은 추정값입니다.
실주문 전에 공식 문서로 확인하고 소액으로 먼저 테스트하세요. 손실 구간 매도 금지 규칙은 하락 종목을 무기한 보유하게 됩니다.
