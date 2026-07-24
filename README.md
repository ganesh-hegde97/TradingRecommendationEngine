# NSE Positive Stock Screener — Python

A Python-only desktop application that screens NSE candidates with positive technical momentum and basic fundamental strength. It is a research aid, not investment advice.

## Python components

- `python_app/app.py` — Tkinter desktop UI.
- `python_app/market_data.py` — optional NSE data download through `yfinance` (`.NS` tickers).
- `python_app/scoring.py` — transparent, testable scoring and eligibility rules.
- `python_app/excel_export.py` — direct Python Excel export using `openpyxl`; there is no Node.js dependency.

The workbook has five review sheets:

- **Recommendations** — current UI shortlist.
- **All Candidates** — every candidate with formula-driven score components and decision.
- **Parameters** — editable weights, score bounds, and recommendation gates.
- **Source Data** — imported data values and source reference.
- **Checks** — model completeness and weight-total checks.

Changing yellow inputs on **Parameters** recalculates **All Candidates** in Excel. The Recommendations tab is a snapshot from the Python run; use All Candidates after changing parameters.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m python_app.app
```

The UI can load bundled demo data immediately. Select **Screen Nifty 50** to retrieve the current constituent list from the official Nifty Indices CSV, validate its 50 symbols, and screen that universe. If the official download is unavailable, a clearly labelled bundled fallback is used. You can also enter NSE symbols without `.NS` (for example `RELIANCE, TCS, INFY`) and select **Screen custom**. `yfinance` is used for public Yahoo Finance data, which can be delayed or incomplete.

## Test without opening the UI

```powershell
python -m python_app.app --demo
```

The command writes `outputs/python_nse_recommendations.xlsx`.

To run the Nifty 50 screen without the UI:

```powershell
python -m python_app.app --nifty50
```

## Model

The 100-point model evaluates 1- and 3-month momentum, price relative to 50/200-day moving averages, revenue and profit growth, ROE, debt-to-equity, and volume ratio. A recommendation also needs positive momentum, a positive trend, above-average volume, complete inputs, and a score of at least 65.

The supplied demo CSV is fabricated. Before acting on any output, refresh data, confirm corporate actions and fundamentals, assess valuation and liquidity, and consider your objectives and risk tolerance.
