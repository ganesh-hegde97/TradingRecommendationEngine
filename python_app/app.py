"""Runnable Tkinter UI for NSE positive-stock screening."""

from __future__ import annotations

import argparse
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

import args

from python_app.config.settings import settings
from python_app.config.logging_config import logger
from python_app.services.recommendation_service import RecommendationService
from python_app.exports.excel_export import export_workbook


class ScreenerApp(tk.Tk):
    service = RecommendationService()

    if args.demo:
        rows = service.screen_demo()

    elif args.nifty50:
        rows, source, failures = service.screen_nifty50()

    def __init__(self) -> None:
        super().__init__()
        self.title("NSE Positive Stock Screener")
        self.geometry("1250x690")
        self.minsize(1000, 580)
        self.rows: list[dict] = []
        self.status = tk.StringVar(
            value="Screen the current Nifty 50, enter a custom subset, or load demo data."
        )
        self.symbols = tk.StringVar(value="RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK")
        self._build()

    def _build(self) -> None:
        controls = ttk.Frame(self, padding=12)
        controls.pack(fill="x")
        ttk.Label(controls, text="NSE symbols:").grid(row=0, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.symbols, width=64).grid(
            row=0, column=1, padx=8, sticky="ew"
        )
        ttk.Button(controls, text="Screen Nifty 50", command=self.fetch_nifty50).grid(
            row=0, column=2, padx=4
        )
        ttk.Button(controls, text="Screen custom", command=self.fetch_live).grid(
            row=0, column=3, padx=4
        )
        ttk.Button(controls, text="Load demo", command=self.load_demo).grid(
            row=0, column=4, padx=4
        )
        ttk.Button(controls, text="Export Excel", command=self.export).grid(
            row=0, column=5, padx=4
        )
        controls.columnconfigure(1, weight=1)
        ttk.Label(
            controls,
            text="Nifty 50 uses the official constituent CSV with a validated fallback; price/fundamental data uses Yahoo Finance/yfinance.",
            foreground="#7F6000",
        ).grid(row=1, column=0, columnspan=6, pady=(8, 0), sticky="w")

        columns = (
            "symbol",
            "company",
            "price",
            "one_month",
            "three_month",
            "score",
            "decision",
            "flags",
        )
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=22)
        headings = {
            "symbol": "Symbol",
            "company": "Company",
            "price": "Last price (₹)",
            "one_month": "1M %",
            "three_month": "3M %",
            "score": "Score",
            "decision": "Decision",
            "flags": "Risk flags",
        }
        widths = {
            "symbol": 105,
            "company": 245,
            "price": 105,
            "one_month": 80,
            "three_month": 80,
            "score": 80,
            "decision": 135,
            "flags": 340,
        }
        for key in columns:
            self.tree.heading(key, text=headings[key])
            self.tree.column(
                key,
                width=widths[key],
                anchor="w" if key in {"company", "flags"} else "center",
            )
        self.tree.tag_configure("recommend", foreground="#006100")
        self.tree.tag_configure("watch", foreground="#9C0006")
        self.tree.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        ttk.Label(self, textvariable=self.status, padding=(12, 4)).pack(fill="x")

    def load_demo(self) -> None:
        self.show_rows(
            score_candidates(load_demo_data()),
            "Demo data loaded. Export it or fetch live data.",
        )

    def fetch_live(self) -> None:
        symbols = [
            item.strip() for item in self.symbols.get().split(",") if item.strip()
        ]
        self.status.set("Downloading price and fundamental data…")
        threading.Thread(
            target=self._fetch_worker, args=(symbols,), daemon=True
        ).start()

    def fetch_nifty50(self) -> None:
        self.status.set(
            "Loading Nifty 50 constituents, then downloading data for up to 50 stocks…"
        )
        threading.Thread(target=self._nifty50_worker, daemon=True).start()

    def _nifty50_worker(self) -> None:
        try:
            symbols, source = load_nifty50_symbols()
            failures: list[str] = []
            rows = score_candidates(download_nse_candidates(symbols, failures))
            suffix = (
                f" {len(failures)} symbols skipped due to unavailable data."
                if failures
                else ""
            )
            self.after(
                0,
                lambda: self.show_rows(
                    rows,
                    f"Screened {len(rows)} Nifty 50 symbols. Universe: {source}.{suffix}",
                ),
            )
        except Exception as exc:
            self.after(
                0, lambda: messagebox.showerror("Nifty 50 screen unavailable", str(exc))
            )
            self.after(
                0,
                lambda: self.status.set(
                    "Nifty 50 download failed. Check yfinance/network access and retry."
                ),
            )

    def _fetch_worker(self, symbols: list[str]) -> None:
        try:
            rows = score_candidates(download_nse_candidates(symbols))
            self.after(
                0,
                lambda: self.show_rows(
                    rows, f"Live data refreshed for {len(rows)} symbols."
                ),
            )
        except Exception as exc:  # surfaced in the UI without terminating it
            self.after(
                0, lambda: messagebox.showerror("Live data unavailable", str(exc))
            )
            self.after(
                0,
                lambda: self.status.set(
                    "Live download failed. Use demo data or install yfinance."
                ),
            )

    def show_rows(self, rows: list[dict], status: str) -> None:
        self.rows = rows
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    stock.symbol,
                    stock.company_name,
                    f"{stock.last_price:.2f}",
                    f"{stock.return_1m_pct:.1f}",
                    f"{stock.return_3m_pct:.1f}",
                    f"{row['score']:.1f}",
                    row["decision"],
                    row["risk_flags"],
                ),
                tags=("recommend" if row["eligible"] else "watch",),
            )
        self.status.set(status)

    def export(self) -> None:
        if not self.rows:
            messagebox.showinfo(
                "Nothing to export", "Load demo data or fetch live data first."
            )
            return
        output = (
            Path(__file__).resolve().parents[1]
            / settings.OUTPUT_DIRECTORY
            / f"nse_recommendations_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        )
        try:
            export_workbook(self.rows, output, "Python desktop UI")
            self.status.set(f"Exported: {output}")
            messagebox.showinfo("Excel exported", f"Saved to:\n{output}")
        except Exception as exc:
            messagebox.showerror("Excel export failed", str(exc))


def main() -> None:
    service = RecommendationService()

    parser = argparse.ArgumentParser(
        description="NSE positive-stock screener desktop UI"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a non-interactive demo export, useful for validation.",
    )
    parser.add_argument(
        "--nifty50",
        action="store_true",
        help="Screen the current Nifty 50 and export the workbook without opening the UI.",
    )
    args = parser.parse_args()
    if args.demo:
        rows = service.screen_demo()
        output = (
            Path(__file__).resolve().parents[1]
            / settings.OUTPUT_DIRECTORY
            / "python_nse_recommendations.xlsx"
        )
        export_workbook(rows, output, "Python demo data")
        logger.info(
            f"Exported {len(rows)} candidates, {sum(row['eligible'] for row in rows)} recommendations: {output}"
        )
        return
    if args.nifty50:
        symbols, source = service.screen_nifty50()
        failures: list[str] = []
        rows = score_candidates(download_nse_candidates(symbols, failures))
        output = (
            Path(__file__).resolve().parents[1]
            / settings.OUTPUT_DIRECTORY
            / "nifty50_recommendations.xlsx"
        )
        export_workbook(rows, output, source)
        logger.info(
            f"Screened {len(rows)} Nifty 50 symbols; {sum(row['eligible'] for row in rows)} recommendations; {len(failures)} skipped: {output}"
        )
        return
    ScreenerApp().mainloop()


if __name__ == "__main__":
    main()
