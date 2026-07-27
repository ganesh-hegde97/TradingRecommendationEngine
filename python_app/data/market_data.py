"""NSE data adapter. Live downloads use yfinance's public Yahoo Finance endpoint."""

from __future__ import annotations
from datetime import date
from typing import Any


def _pct(current: float, previous: float) -> float:
    return round((current / previous - 1) * 100, 2)


def _clean_symbols(symbols: list[Any]) -> list[str]:
    return list(
        dict.fromkeys(
            str(symbol).strip().upper().removesuffix(".NS")
            for symbol in symbols
            if str(symbol).strip()
        )
    )


def download_nse_candidates(
    symbols: list[str], failures: list[str] | None = None
) -> list[dict[str, Any]]:
    """Fetch one year of daily pricing plus available company fundamentals for NSE tickers.

    Yahoo's fields can be absent for some tickers. Those rows stay visible but are flagged
    as incomplete and cannot be recommended until the data is reviewed or supplemented.
    """
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError(
            "Live data needs yfinance. Run: pip install -r requirements.txt"
        ) from exc

    results: list[dict[str, Any]] = []
    for supplied in symbols:
        symbol = supplied.strip().upper().removesuffix(".NS")
        if not symbol:
            continue
        try:
            results.append(_download_one_nse_candidate(yf, symbol))
        except Exception as exc:
            if failures is not None:
                failures.append(f"{symbol}: {exc}")
    if not results:
        raise RuntimeError(
            "Enter at least one NSE symbol, for example RELIANCE, TCS, INFY."
        )
    return results


def _download_one_nse_candidate(yf: Any, symbol: str) -> dict[str, Any]:
    ticker = yf.Ticker(f"{symbol}.NS")
    history = ticker.history(period="1y", auto_adjust=True)
    if history.empty or len(history) < 201:
        raise RuntimeError("insufficient daily-price history")
    close = history["Close"].dropna()
    volume = history["Volume"].dropna()
    info = ticker.info or {}
    last = float(close.iloc[-1])
    return {
        "symbol": symbol,
        "company_name": info.get("shortName") or symbol,
        "sector": info.get("sector") or "Not supplied",
        "last_price": round(last, 2),
        "return_1m_pct": _pct(last, float(close.iloc[-22])),
        "return_3m_pct": _pct(last, float(close.iloc[-64])),
        "price_vs_50dma_pct": _pct(last, float(close.tail(50).mean())),
        "price_vs_200dma_pct": _pct(last, float(close.tail(200).mean())),
        "revenue_growth_yoy_pct": _ratio_pct(info.get("revenueGrowth")),
        "profit_growth_yoy_pct": _ratio_pct(info.get("earningsGrowth")),
        "roe_pct": _ratio_pct(info.get("returnOnEquity")),
        "debt_to_equity": _debt_ratio(info.get("debtToEquity")),
        "volume_ratio": round(
            float(volume.iloc[-1]) / float(volume.tail(20).mean()), 2
        ),
        "market_cap_cr": _market_cap_cr(info.get("marketCap")),
        "source_url": f"https://finance.yahoo.com/quote/{symbol}.NS",
        "as_of_date": date.today().isoformat(),
    }


def _ratio_pct(value: Any) -> float | None:
    return round(float(value) * 100, 2) if value is not None else None


def _debt_ratio(value: Any) -> float | None:
    return round(float(value) / 100, 2) if value is not None else None


def _market_cap_cr(value: Any) -> float | None:
    return round(float(value) / 10_000_000, 2) if value is not None else None
