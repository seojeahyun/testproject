"""토스증권 Open API 클라이언트.

확인된 것(블로그 자료 기준): 기준 URL, OAuth2 Client Credentials(form-urlencoded),
GET /api/v1/accounts, 헤더 X-Tossinvest-Account(accountSeq), 허용 IP 등록 필요.
확인되지 않은 것: 토큰·시세·캔들·주문 경로와 필드명. 아래 PATHS 는 추정값이므로
공식 문서(OpenAPI 명세)를 보고 반드시 고쳐야 한다.
"""
import os
import time

import requests

BASE_URL = "https://openapi.tossinvest.com"
PATHS = {  # TODO: 공식 명세로 검증
    "token": "/oauth2/token",
    "accounts": "/api/v1/accounts",
    "candles": "/api/v1/stocks/{symbol}/candles",
    "price": "/api/v1/stocks/{symbol}/price",
    "positions": "/api/v1/accounts/positions",
    "orders": "/api/v1/orders",
}


class TossError(Exception):
    pass


class TossClient:
    def __init__(self, client_id=None, client_secret=None):
        self.client_id = client_id or os.environ.get("TOSS_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("TOSS_CLIENT_SECRET")
        self._token = None
        self._exp = 0
        self._account_seq = None

    def _request(self, method, key, auth=True, **kw):
        headers = kw.pop("headers", {})
        if auth:
            headers["Authorization"] = f"Bearer {self._get_token()}"
        path = PATHS[key].format(**kw.pop("fmt", {}))
        r = requests.request(method, BASE_URL + path, headers=headers, timeout=10, **kw)
        if r.status_code == 403:
            raise TossError("403: 허용 IP 등록 여부를 확인하세요")
        if not r.ok:
            raise TossError(f"{r.status_code}: {r.text[:200]}")
        return r.json()

    def _get_token(self):
        if self._token and time.time() < self._exp - 60:
            return self._token
        if not (self.client_id and self.client_secret):
            raise TossError("TOSS_CLIENT_ID / TOSS_CLIENT_SECRET 이 설정되지 않았습니다")
        j = self._request("POST", "token", auth=False, data={
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        })
        self._token = j["access_token"]
        self._exp = time.time() + int(j.get("expires_in", 3600))
        return self._token

    def account_headers(self):
        if self._account_seq is None:
            accounts = self._request("GET", "accounts")
            items = accounts.get("data", accounts) if isinstance(accounts, dict) else accounts
            self._account_seq = items[0]["accountSeq"]  # TODO: 필드 구조 검증
        return {"X-Tossinvest-Account": str(self._account_seq)}

    def candles(self, symbol, count=100):
        """일봉 종가 목록(오래된 순). TODO: 응답 구조 검증."""
        j = self._request("GET", "candles", fmt={"symbol": symbol}, params={"interval": "1d", "count": count})
        rows = j.get("data", j)
        return [float(x["close"]) for x in rows]

    def price(self, symbol):
        j = self._request("GET", "price", fmt={"symbol": symbol})
        return float(j.get("data", j)["price"])

    def holdings(self):
        """{symbol: (qty, avg_cost)}. TODO: 응답 구조 검증."""
        j = self._request("GET", "positions", headers=self.account_headers())
        return {p["symbol"]: (int(p["quantity"]), float(p["averagePrice"])) for p in j.get("data", j)}

    def order(self, symbol, side, qty, price=None):
        body = {"symbol": symbol, "side": side, "quantity": qty,
                "orderType": "LIMIT" if price else "MARKET"}  # TODO: 필드 검증
        if price:
            body["price"] = price
        return self._request("POST", "orders", headers=self.account_headers(), json=body)
