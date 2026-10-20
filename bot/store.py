import os
import sqlite3
import time


class Store:
    def __init__(self, path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS signals(ts REAL, symbol TEXT, rsi REAL, price REAL, qty INT, avg_cost REAL, signal TEXT);
        CREATE TABLE IF NOT EXISTS orders(ts REAL, symbol TEXT, side TEXT, qty INT, price REAL, dry_run INT, status TEXT, detail TEXT);
        CREATE TABLE IF NOT EXISTS positions(symbol TEXT PRIMARY KEY, qty INT, avg_cost REAL);
        CREATE TABLE IF NOT EXISTS errors(ts REAL, where_ TEXT, message TEXT);
        """)

    def add_signal(self, symbol, rsi, price, qty, avg_cost, signal):
        self.db.execute("INSERT INTO signals VALUES(?,?,?,?,?,?,?)", (time.time(), symbol, rsi, price, qty, avg_cost, signal))
        self.db.commit()

    def add_order(self, symbol, side, qty, price, dry_run, status, detail=""):
        self.db.execute("INSERT INTO orders VALUES(?,?,?,?,?,?,?,?)", (time.time(), symbol, side, qty, price, int(dry_run), status, detail))
        self.db.commit()

    def add_error(self, where, message):
        self.db.execute("INSERT INTO errors VALUES(?,?,?)", (time.time(), where, str(message)))
        self.db.commit()

    def position(self, symbol):
        r = self.db.execute("SELECT qty, avg_cost FROM positions WHERE symbol=?", (symbol,)).fetchone()
        return r if r else (0, 0.0)

    def set_position(self, symbol, qty, avg_cost):
        self.db.execute("INSERT OR REPLACE INTO positions VALUES(?,?,?)", (symbol, qty, avg_cost))
        self.db.commit()

    def spent_today(self):
        start = time.mktime(time.localtime()[:3] + (0, 0, 0, 0, 0, -1))
        r = self.db.execute("SELECT COALESCE(SUM(qty*price),0) FROM orders WHERE side='BUY' AND ts>=? AND status!='ERROR'", (start,)).fetchone()
        return r[0]
