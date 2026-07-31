"""Tkinter controller and command-line entry point for the recommendation workflow."""

from __future__ import annotations

import argparse
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from python_app.config.logging_config import logger
from python_app.config.settings import settings
from python_app.exports.excel_export import export_workbook
from python_app.models import Recommendation
from python_app.services.recommendation_service import RecommendationService


class ScreenerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.service = RecommendationService()
        self.title("NSE Positive Stock Screener")
        self.geometry("1250x690")
        self.minsize(1000, 580)
        self.recommendations: list[Recommendation] = []
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
        headings = (
            "Symbol",
            "Company",
            "Last price (Rs)",
            "1M %",
            "3M %",
            "Score",
            "Decision",
            "Risk flags",
        )
        widths = (105, 245, 105, 80, 80, 80, 135, 340)
        for key, heading, width in zip(columns, headings, widths):
            self.tree.heading(key, text=heading)
            self.tree.column(
                key,
                width=width,
                anchor="w" if key in {"company", "flags"} else "center",
            )
        self.tree.tag_configure("recommend", foreground="#006100")
        self.tree.tag_configure("watch", foreground="#9C0006")
        self.tree.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        ttk.Label(self, textvariable=self.status, padding=(12, 4)).pack(fill="x")

    def load_demo(self) -> None:
        self.show_recommendations(
            self.service.screen_demo(),
            "Demo data loaded. Export it or fetch live data.",
        )

    def fetch_live(self) -> None:
        symbols = [
            item.strip() for item in self.symbols.get().split(",") if item.strip()
        ]
        self.status.set("Downloading price and fundamental data...")
        threading.Thread(
            target=self._custom_worker, args=(symbols,), daemon=True
        ).start()

    def fetch_nifty50(self) -> None:
        self.status.set("Loading Nifty 50 constituents and market data...")
        threading.Thread(target=self._nifty50_worker, daemon=True).start()

    def _custom_worker(self, symbols: list[str]) -> None:
        try:
            recommendations = self.service.screen_custom(symbols)
            self.after(
                0,
                lambda: self.show_recommendations(
                    recommendations,
                    f"Live data refreshed for {len(recommendations)} symbols.",
                ),
            )
        except Exception as exc:
            self.after(
                0, lambda: messagebox.showerror("Live data unavailable", str(exc))
            )

    def _nifty50_worker(self) -> None:
        try:
            recommendations, source, failures = self.service.screen_nifty50()
            suffix = f" {len(failures)} symbols skipped." if failures else ""
            self.after(
                0,
                lambda: self.show_recommendations(
                    recommendations,
                    f"Screened {len(recommendations)} Nifty 50 symbols. Universe: {source}.{suffix}",
                ),
            )
        except Exception as exc:
            self.after(
                0, lambda: messagebox.showerror("Nifty 50 screen unavailable", str(exc))
            )

    def show_recommendations(
        self, recommendations: list[Recommendation], status: str
    ) -> None:
        self.recommendations = recommendations
        for item in self.tree.get_children():
            self.tree.delete(item)
        for recommendation in recommendations:
            stock = recommendation.stock
            self.tree.insert(
                "",
                "end",
                values=(
                    stock.symbol,
                    stock.company_name,
                    f"{stock.last_price or 0:.2f}",
                    f"{stock.return_1m_pct or 0:.1f}",
                    f"{stock.return_3m_pct or 0:.1f}",
                    f"{recommendation.score:.1f}",
                    recommendation.decision,
                    recommendation.risk_flags,
                ),
                tags=("recommend" if recommendation.eligible else "watch",),
            )
        self.status.set(status)

    def export(self) -> None:
        if not self.recommendations:
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
            export_workbook(self.recommendations, output, "Python desktop UI")
            self.status.set(f"Exported: {output}")
            messagebox.showinfo("Excel exported", f"Saved to:\n{output}")
        except Exception as exc:
            messagebox.showerror("Excel export failed", str(exc))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NSE positive-stock screener desktop UI"
    )
    parser.add_argument(
        "--demo", action="store_true", help="Run a non-interactive demo export."
    )
    parser.add_argument(
        "--nifty50",
        action="store_true",
        help="Screen the Nifty 50 and export without opening the UI.",
    )
    args = parser.parse_args()
    service = RecommendationService()
    if args.demo:
        recommendations = service.screen_demo()
        output = (
            Path(__file__).resolve().parents[1]
            / settings.OUTPUT_DIRECTORY
            / "python_nse_recommendations.xlsx"
        )
        export_workbook(recommendations, output, "Python demo data")
        logger.info(
            "Exported %d candidates, %d recommendations: %s",
            len(recommendations),
            sum(item.eligible for item in recommendations),
            output,
        )
        return
    if args.nifty50:
        recommendations, source, failures = service.screen_nifty50()
        output = (
            Path(__file__).resolve().parents[1]
            / settings.OUTPUT_DIRECTORY
            / "nifty50_recommendations.xlsx"
        )
        export_workbook(recommendations, output, source)
        logger.info(
            "Screened %d Nifty 50 stocks; %d recommendations; %d skipped: %s",
            len(recommendations),
            sum(item.eligible for item in recommendations),
            len(failures),
            output,
        )
        return
    ScreenerApp().mainloop()


if __name__ == "__main__":
    main()
