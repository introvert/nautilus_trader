#!/usr/bin/env python3
# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2025 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

"""Utility script for downloading Binance historical bar data."""

from __future__ import annotations

import argparse
import asyncio
import time
from datetime import datetime, timezone

import pandas as pd

from nautilus_trader.adapters.binance.common.enums import BinanceAccountType
from nautilus_trader.adapters.binance.common.enums import BinanceKlineInterval
from nautilus_trader.adapters.binance.http.client import BinanceHttpClient
from nautilus_trader.adapters.binance.http.market import BinanceMarketHttpAPI
from nautilus_trader.adapters.binance.spot.enums import BinanceSpotEnumParser
from nautilus_trader.common.component import LiveClock
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AggregationSource
from nautilus_trader.model.identifiers import InstrumentId


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Binance historical bars for a symbol.",
    )
    parser.add_argument("symbol", help="Trading pair symbol, e.g. BTCUSDT")
    parser.add_argument(
        "--interval",
        default="1m",
        help="Binance kline interval (default: 1m)",
    )
    parser.add_argument(
        "--start",
        help="Start date (YYYY-MM-DD, UTC). Defaults to 1970-01-01.",
    )
    parser.add_argument(
        "--end",
        help="End date (YYYY-MM-DD, UTC). Defaults to now.",
    )
    parser.add_argument(
        "--output",
        default="binance_bars.csv",
        help="Output CSV filename (default: binance_bars.csv)",
    )
    return parser.parse_args()


async def _download(
    symbol: str,
    interval: BinanceKlineInterval,
    start: datetime,
    end: datetime,
    output: str,
) -> None:
    clock = LiveClock()
    client = BinanceHttpClient(
        clock=clock,
        api_key="",
        api_secret="",
        base_url="https://api.binance.com",
    )
    api = BinanceMarketHttpAPI(client, BinanceAccountType.SPOT)

    parser = BinanceSpotEnumParser()
    instrument_id = InstrumentId.from_str(f"{symbol}.BINANCE")
    spec = parser.parse_binance_kline_interval_to_bar_spec(interval)
    bar_type = BarType(instrument_id, spec, AggregationSource.EXTERNAL)

    start_ms = int(start.replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = int(end.replace(tzinfo=timezone.utc).timestamp() * 1000)

    bars = await api.request_binance_bars(
        bar_type=bar_type,
        ts_init=time.time_ns(),
        interval=interval,
        start_time=start_ms,
        end_time=end_ms,
        limit=1000,
    )

    df = pd.DataFrame([bar.to_dict() for bar in bars])
    if not df.empty:
        df["ts_event"] = pd.to_datetime(df["ts_event"], unit="ns")
    df.to_csv(output, index=False)


def main() -> None:
    args = _parse_args()
    interval = BinanceKlineInterval(args.interval)
    start = (
        datetime.strptime(args.start, "%Y-%m-%d")
        if args.start
        else datetime(1970, 1, 1)
    )
    end = (
        datetime.strptime(args.end, "%Y-%m-%d")
        if args.end
        else datetime.utcnow()
    )
    asyncio.run(
        _download(
            symbol=args.symbol,
            interval=interval,
            start=start,
            end=end,
            output=args.output,
        )
    )


if __name__ == "__main__":
    main()
