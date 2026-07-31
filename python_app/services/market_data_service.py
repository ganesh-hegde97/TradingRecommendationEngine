"""Market Data Service

Acts as the single entry point for obtaining stock data.
RecommendationService should never call the data modules directly.
"""

from __future__ import annotations

from python_app.config.logging_config import logger
from python_app.data.demo_loader import load_demo_data
from python_app.data.market_data import download_nse_candidates
from python_app.data.nifty_loader import load_nifty50_symbols
from python_app.models import Stock


class MarketDataService:
    """Encapsulates all market-data retrieval."""

    def load_demo(self) -> list[Stock]:
        logger.info("Loading demo data")

        rows = load_demo_data()

        logger.info("Loaded %d demo records", len(rows))

        return rows

    def download_custom(self, symbols: list[str]) -> list[Stock]:
        logger.info(
            "Downloading market data for %d symbols",
            len(symbols),
        )

        rows = download_nse_candidates(symbols)

        logger.info(
            "Downloaded %d candidate records",
            len(rows),
        )

        return rows

    def download_nifty50(
        self,
    ) -> tuple[list[Stock], str, list[str]]:
        logger.info("Loading Nifty 50 universe")

        symbols, source = load_nifty50_symbols()

        failures: list[str] = []

        rows = download_nse_candidates(
            symbols,
            failures,
        )

        logger.info(
            "Downloaded %d Nifty50 stocks (%d skipped)",
            len(rows),
            len(failures),
        )

        return rows, source, failures
