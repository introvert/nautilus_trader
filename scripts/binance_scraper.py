#!/usr/bin/env python3
"""Download Binance kline data for a symbol and year.

The resulting CSV is compatible with Nautilus Trader backtesting fixtures
which expect rows in the same format returned by the Binance kline API:

```
open_time, open, high, low, close, volume,
close_time, quote_asset_volume, number_of_trades,
taker_buy_base_asset_volume, taker_buy_quote_asset_volume, ignore
```

Example usage:

```
python scripts/binance_scraper.py --symbol BTCUSDT --year 2021 \
    --interval 1m --output btcusdt-1m-2021.csv
```

This will write `btcusdt-1m-2021.csv` to the current directory containing
minute bar data for the whole of 2021.
"""

from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime, timezone
from typing import Iterable, List

import requests


API_URL = "https://api.binance.com/api/v3/klines"


def interval_to_milliseconds(interval: str) -> int:
    """Return the interval duration in milliseconds."""
    unit = interval[-1]
    if not interval[:-1].isdigit():
        raise ValueError(f"Invalid interval: {interval}")
    amount = int(interval[:-1])
    multipliers = {
        "m": 60 * 1000,               # minutes
        "h": 60 * 60 * 1000,          # hours
        "d": 24 * 60 * 60 * 1000,     # days
        "w": 7 * 24 * 60 * 60 * 1000, # weeks
    }
    try:
        return amount * multipliers[unit]
    except KeyError as exc:
        raise ValueError(f"Unsupported interval unit: {unit}") from exc


def fetch_klines(symbol: str, start_ms: int, end_ms: int, interval: str) -> Iterable[List[str]]:
    """Generator yielding klines between `start_ms` and `end_ms`."""
    step = interval_to_milliseconds(interval)
    current = start_ms
    while current < end_ms:
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": 1000,
            "startTime": current,
        }
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        klines = response.json()
        if not klines:
            break
        for k in klines:
            yield k
        current = klines[-1][0] + step
        # Be gentle with the API
        time.sleep(0.1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Binance kline data for backtesting")
    parser.add_argument("--symbol", required=True, help="Trading pair symbol, e.g. BTCUSDT")
    parser.add_argument("--year", type=int, required=True, help="Year of data to download")
    parser.add_argument("--interval", default="1m", help="Kline interval, default 1m")
    parser.add_argument(
        "--output",
        help="Output CSV file name (defaults to <SYMBOL>-<INTERVAL>-<YEAR>.csv)",
    )
    parser.add_argument(
        "--start",
        help="Optional start date (YYYY-MM-DD). Defaults to 1st Jan of --year.",
    )
    parser.add_argument(
        "--end",
        help="Optional end date (YYYY-MM-DD). Defaults to 1st Jan of year+1.",
    )
    args = parser.parse_args()

    if args.start:
        start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    else:
        start = datetime(args.year, 1, 1, tzinfo=timezone.utc)

    if args.end:
        end = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)
    else:
        end = datetime(args.year + 1, 1, 1, tzinfo=timezone.utc)

    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)

    outfile = args.output or f"{args.symbol.upper()}-{args.interval}-{args.year}.csv"

    with open(outfile, "w", newline="") as f:
        writer = csv.writer(f)
        for kline in fetch_klines(args.symbol, start_ms, end_ms, args.interval):
            writer.writerow(kline[:12])

    print(f"Wrote data to {outfile}")


if __name__ == "__main__":
    main()
