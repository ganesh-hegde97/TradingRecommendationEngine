from io import StringIO
from pathlib import Path
import pandas as pd
from urllib.request import Request, urlopen
from python_app.config.settings import settings
from python_app.data.market_data import _clean_symbols


def load_nifty50_symbols(
    constituent_url: str = settings.NIFTY50_CONSTITUENT_URL,
) -> tuple[list[str], str]:
    """Return the current official Nifty 50 symbols, with a checked local fallback.

    The constituent CSV is fetched at runtime so semi-annual index changes do not require
    a code release. A fallback is deliberately labelled as a snapshot and should only be
    used when the official download is unavailable.
    """
    try:
        request = Request(constituent_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, settings.REQUEST_TIMEOUT) as response:
            frame = pd.read_csv(StringIO(response.read().decode("utf-8-sig")))
        symbol_column = next(
            (column for column in frame.columns if column.strip().lower() == "symbol"),
            None,
        )
        if symbol_column is None:
            raise ValueError("Official constituent file has no Symbol column.")
        symbols = _clean_symbols(frame[symbol_column].tolist())
        if len(symbols) != 50:
            raise ValueError(
                f"Official constituent file returned {len(symbols)} unique symbols, not 50."
            )
        return symbols, f"Official Nifty Indices constituent CSV: {constituent_url}"
    except Exception:
        fallback = Path(__file__).resolve().parents[1] / "data" / "nifty50_fallback.csv"
        symbols = _clean_symbols(pd.read_csv(fallback)["symbol"].tolist())
        if len(symbols) != 50:
            raise RuntimeError(
                "Bundled Nifty 50 fallback is not a valid 50-symbol list."
            )
        return (
            symbols,
            f"Bundled fallback snapshot — refresh from {settings.NIFTY50_OFFICIAL_PAGE}",
        )
