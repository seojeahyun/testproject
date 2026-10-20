import time

import yaml

from bot.store import Store
from bot.toss_client import TossClient
from bot.trader import is_live, run_once


def main():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    store = Store(cfg["db_path"])
    toss = TossClient()
    print("모드:", "실주문" if is_live(cfg) else "모의(dry-run)")
    while True:
        run_once(cfg, store, toss)
        time.sleep(cfg["interval_seconds"])


if __name__ == "__main__":
    main()
