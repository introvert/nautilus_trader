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

"""Minimal example showing how to execute a backtest.

The script wires together configuration objects, points to the bundled
sample trade data under ``tests/test_data/binance`` and then launches the
``BacktestNode``.  Run it from the project root with::

    python examples/backtest/run_backtest.py

The test dataset ships with the repository so no additional download is
required.  Replace the paths or configuration to suit your own data and
strategies.
"""

from pathlib import Path

from nautilus_trader.backtest.config import (
    BacktestDataConfig,
    BacktestEngineConfig,
    BacktestRunConfig,
    BacktestVenueConfig,
)
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.config import ImportableStrategyConfig, LoggingConfig
from nautilus_trader.model.identifiers import TraderId


if __name__ == "__main__":
    # Strategy configuration
    strategy_cfg = ImportableStrategyConfig(
        strategy_path="nautilus_trader.examples.strategies.ema_cross:EMACross",
        config_path="nautilus_trader.examples.strategies.ema_cross:EMACrossConfig",
        config={
            "instrument_id": "BTCUSDT.BINANCE",
            "bar_type": "BTCUSDT.BINANCE-1-MINUTE-LAST-EXTERNAL",
            "fast_ema_period": 10,
            "slow_ema_period": 20,
            "trade_size": "0.01 BTC",
        },
    )

    # Data configuration pointing to bundled test data
    data_path = Path(__file__).resolve().parents[2] / "tests" / "test_data" / "binance"
    data_cfg = BacktestDataConfig(
        catalog_path=str(data_path),
        data_cls="nautilus_trader.model.data:TradeTick",
        instrument_id="BTCUSDT.BINANCE",
    )

    # Venue configuration
    venue_cfg = BacktestVenueConfig(
        name="BINANCE",
        oms_type="NETTING",
        account_type="CASH",
        base_currency="USDT",
        starting_balances=["1000 USDT", "1 BTC"],
    )

    # Engine configuration
    engine_cfg = BacktestEngineConfig(
        trader_id=TraderId("BACKTESTER-001"),
        logging=LoggingConfig(log_level="INFO"),
    )

    # Bundle everything into a run configuration
    run_cfg = BacktestRunConfig(
        engine=engine_cfg,
        strategies=[strategy_cfg],
        data=[data_cfg],
        venues=[venue_cfg],
    )

    # Launch the backtest
    node = BacktestNode(configs=[run_cfg])
    node.run()
