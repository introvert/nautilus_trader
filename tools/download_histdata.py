#!/usr/bin/env python
"""Utility to download HistData FX tick data into a Parquet data catalog."""

import argparse
from pathlib import Path
import zipfile

import requests

from nautilus_trader.persistence.loaders import CSVTickDataLoader
from nautilus_trader.persistence.wranglers import QuoteTickDataWrangler
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.test_kit.providers import TestInstrumentProvider


def download_histdata(pair: str, year: int, month: int, dest: Path) -> Path:
    """Download HistData tick CSV for *pair* and return extracted CSV path."""
    pair_url = pair.lower().replace("/", "")
    url = (
        "https://www.histdata.com/download-free-forex-historical-data/"
        f"?/ascii/tick-data-quotes/{pair_url}/{year}/{month}"
    )
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / f"{pair_url}-{year}-{month}.zip"
    zip_path.write_bytes(response.content)

    with zipfile.ZipFile(zip_path) as zf:
        csv_name = zf.namelist()[0]
        zf.extract(csv_name, dest)
    return dest / csv_name


def load_ticks(csv_path: Path):
    """Load raw CSV ticks into a pandas DataFrame."""
    return CSVTickDataLoader.load(
        file_path=csv_path,
        index_col=0,
        names=["timestamp", "bid_price", "ask_price"],
        datetime_format="%Y%m%d %H%M%S%f",
        sep=";",
    )


def write_catalog(pair: str, ticks_df, catalog_path: Path) -> None:
    """Convert DataFrame to QuoteTick objects and store in a ParquetDataCatalog."""
    instrument = TestInstrumentProvider.default_fx_ccy(pair)
    wrangler = QuoteTickDataWrangler(instrument=instrument)
    ticks = wrangler.process(ticks_df)

    catalog = ParquetDataCatalog(catalog_path)
    catalog.write_data([instrument])
    catalog.write_data(ticks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download HistData ticks into a catalog")
    parser.add_argument("pair", help="Currency pair symbol, e.g. EUR/USD")
    parser.add_argument("year", type=int, help="Year to download")
    parser.add_argument("month", type=int, help="Month to download (1-12)")
    parser.add_argument("catalog", type=Path, help="Path to Parquet data catalog")
    parser.add_argument(
        "--data-dir", type=Path, default=Path("./data"), help="Directory to store raw downloads"
    )
    args = parser.parse_args()

    csv_path = download_histdata(args.pair, args.year, args.month, args.data_dir)
    ticks_df = load_ticks(csv_path)
    write_catalog(args.pair, ticks_df, args.catalog)
    print(f"Wrote {len(ticks_df)} ticks for {args.pair} to catalog at {args.catalog}")


if __name__ == "__main__":  # pragma: no cover
    main()
