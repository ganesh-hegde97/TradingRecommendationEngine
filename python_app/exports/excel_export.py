"""Pure-Python Excel export for the NSE recommendation screen."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from python_app.core.constants import FACTORS
from python_app.models import Recommendation

NAVY = "17365D"
BLUE = "1F4E78"
PALE_BLUE = "D9EAF7"
GREEN = "E2F0D9"
YELLOW = "FFF2CC"
RED = "FCE4D6"
THIN = Side(style="thin", color="D9E2F3")
SOURCE_COLUMNS = [
    "symbol",
    "company_name",
    "sector",
    "last_price",
    "return_1m_pct",
    "return_3m_pct",
    "price_vs_50dma_pct",
    "price_vs_200dma_pct",
    "revenue_growth_yoy_pct",
    "profit_growth_yoy_pct",
    "roe_pct",
    "debt_to_equity",
    "volume_ratio",
    "market_cap_cr",
    "source_url",
    "as_of_date",
]
SOURCE_HEADERS = [
    "Symbol",
    "Company",
    "Sector",
    "Last price (₹)",
    "1M return (%)",
    "3M return (%)",
    "Vs 50DMA (%)",
    "Vs 200DMA (%)",
    "Revenue growth YoY (%)",
    "Profit growth YoY (%)",
    "ROE (%)",
    "Debt / equity",
    "Volume ratio",
    "Market cap (₹ Cr)",
    "Source URL",
    "As-of date",
]


def _title(ws, cell_range: str, text: str) -> None:
    ws.merge_cells(cell_range)
    cell = ws[cell_range.split(":")[0]]
    cell.value = text
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.font = Font(bold=True, color="FFFFFF", size=16)
    cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[cell.row].height = 28


def _header(ws, row: int, start_col: int, end_col: int) -> None:
    for col in range(start_col, end_col + 1):
        cell = ws.cell(row, col)
        cell.fill = PatternFill("solid", fgColor=BLUE)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        cell.border = Border(left=THIN, right=THIN, bottom=THIN)
    ws.row_dimensions[row].height = 32


def _table_border(ws, min_row: int, max_row: int, min_col: int, max_col: int) -> None:
    for row in ws.iter_rows(
        min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col
    ):
        for cell in row:
            cell.border = Border(bottom=THIN)
            cell.alignment = Alignment(vertical="center")


def _set_widths(ws, widths: list[int]) -> None:
    for index, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(index)].width = width


def _export_record(recommendation: Recommendation) -> dict[str, object]:
    """Adapt typed results only at the workbook serialization boundary."""
    row = recommendation.stock.to_mapping()
    row.update(
        {
            "score": recommendation.score,
            "decision": recommendation.decision,
            "eligible": recommendation.eligible,
            "risk_flags": recommendation.risk_flags,
            "data_complete": "Missing required data" not in recommendation.reasons,
        }
    )
    return row


def export_workbook(
    recommendations: list[Recommendation], output_file: Path, source_label: str
) -> None:
    """Create a fully Python-generated, formula-driven audit workbook.

    Excel recalculates the formula sheets when opened. The Parameters sheet contains the
    editable weights and gates; All Candidates references those cells directly.
    """
    rows = [_export_record(recommendation) for recommendation in recommendations]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    recommendations = wb.active
    recommendations.title = "Recommendations"
    all_candidates = wb.create_sheet("All Candidates")
    parameters = wb.create_sheet("Parameters")
    source = wb.create_sheet("Source Data")
    checks = wb.create_sheet("Checks")
    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = False

    # Parameters
    _title(parameters, "A1:F1", "NSE Positive Stock Screener — Parameters")
    parameters.merge_cells("A2:F2")
    parameters["A2"] = (
        "Yellow cells are editable. Update them in Excel, then review the recalculated All Candidates sheet."
    )
    parameters["A2"].fill = PatternFill("solid", fgColor=YELLOW)
    parameters["A2"].font = Font(italic=True, color="1F2937")
    parameters["A2"].alignment = Alignment(wrap_text=True)
    parameter_headers = [
        "Factor",
        "Input field",
        "Weight",
        "Lower bound",
        "Upper bound",
        "Scoring rationale",
    ]
    for col, value in enumerate(parameter_headers, 1):
        parameters.cell(4, col, value)
    _header(parameters, 4, 1, 6)
    rationale = [
        "Recent price strength.",
        "Medium-term price strength.",
        "Trend confirmation against the 50-day moving average.",
        "Longer-term trend confirmation against the 200-day moving average.",
        "Fundamental top-line growth.",
        "Earnings growth.",
        "Profitability; higher is better.",
        "Lower leverage is better; the score is inverted.",
        "Current volume divided by its 20-day average.",
    ]
    for index, factor in enumerate(FACTORS, 5):
        parameters.cell(index, 1, factor.name)
        parameters.cell(index, 2, factor.key)
        parameters.cell(index, 3, factor.weight)
        parameters.cell(index, 4, factor.low)
        parameters.cell(index, 5, factor.high)
        parameters.cell(index, 6, rationale[index - 5])
        for col in (3, 4, 5):
            parameters.cell(index, col).fill = PatternFill("solid", fgColor=YELLOW)
            parameters.cell(index, col).font = Font(color="0000FF")
            parameters.cell(index, col).number_format = "0.0"
    _table_border(parameters, 4, 13, 1, 6)
    parameters["A16"], parameters["B16"] = "Eligibility gate", "Value"
    _header(parameters, 16, 1, 2)
    gates = [
        ("Minimum total score", 65),
        ("Minimum 1M return (%)", 0),
        ("Minimum 3M return (%)", 0),
        ("Minimum volume ratio", 1),
        ("Minimum price vs 50DMA (%)", 0),
        ("Minimum price vs 200DMA (%)", 0),
    ]
    for row_number, (label, value) in enumerate(gates, 17):
        parameters.cell(row_number, 1, label)
        parameters.cell(row_number, 2, value)
        parameters.cell(row_number, 2).fill = PatternFill("solid", fgColor=YELLOW)
        parameters.cell(row_number, 2).font = Font(color="0000FF")
    _table_border(parameters, 16, 22, 1, 2)
    parameters.merge_cells("A24:F26")
    parameters["A24"] = (
        "Important: this is an educational screening aid, not investment advice. Confirm data quality, valuation, corporate actions, liquidity, and suitability before any decision."
    )
    parameters["A24"].fill = PatternFill("solid", fgColor=RED)
    parameters["A24"].font = Font(bold=True, color="9C0006")
    parameters["A24"].alignment = Alignment(wrap_text=True, vertical="center")
    _set_widths(parameters, [28, 25, 14, 14, 14, 56])

    # Immutable source data supplied by Python.
    _title(source, "A1:P1", "Source Data — Imported Candidate Inputs")
    source.merge_cells("A2:P2")
    source["A2"] = (
        f"Source: {source_label}. Refresh data before making investment decisions."
    )
    source["A2"].fill = PatternFill("solid", fgColor=YELLOW)
    source["A2"].font = Font(italic=True, color="1F2937")
    for col, value in enumerate(SOURCE_HEADERS, 1):
        source.cell(4, col, value)
    _header(source, 4, 1, 16)
    for row_number, record in enumerate(rows, 5):
        for col, key in enumerate(SOURCE_COLUMNS, 1):
            source.cell(row_number, col, record.get(key))
    _table_border(source, 4, 4 + len(rows), 1, 16)
    for row_number in range(5, 5 + len(rows)):
        source.cell(row_number, 4).number_format = "₹#,##0.00"
        for col in range(5, 12):
            source.cell(row_number, col).number_format = "0.0;[Red](0.0);-"
        source.cell(row_number, 12).number_format = "0.00x"
        source.cell(row_number, 13).number_format = "0.00x"
        source.cell(row_number, 14).number_format = "#,##0"
    source.freeze_panes = "A5"
    _set_widths(
        source, [16, 28, 20, 14, 13, 13, 13, 13, 20, 20, 12, 14, 14, 18, 42, 14]
    )

    # Audit sheet: formula references use visible parameter cells and source values.
    _title(
        all_candidates,
        "A1:AA1",
        "All Candidates — Formula-Driven Score & Eligibility Audit",
    )
    all_candidates.merge_cells("A2:AA2")
    all_candidates["A2"] = (
        "Scores and eligibility below are Excel formulas. Filter this sheet to review every candidate and rejection reason."
    )
    all_candidates["A2"].fill = PatternFill("solid", fgColor=PALE_BLUE)
    all_candidates["A2"].font = Font(italic=True, color="1F2937")
    audit_headers = (
        SOURCE_HEADERS[:14]
        + [f"{factor.name} score" for factor in FACTORS]
        + ["Total score", "Eligibility", "Decision", "Risk flags"]
    )
    for col, value in enumerate(audit_headers, 1):
        all_candidates.cell(4, col, value)
    _header(all_candidates, 4, 1, 27)
    key_to_col = {
        factor.key: {
            "return_1m_pct": "E",
            "return_3m_pct": "F",
            "price_vs_50dma_pct": "G",
            "price_vs_200dma_pct": "H",
            "revenue_growth_yoy_pct": "I",
            "profit_growth_yoy_pct": "J",
            "roe_pct": "K",
            "debt_to_equity": "L",
            "volume_ratio": "M",
        }[factor.key]
        for factor in FACTORS
    }
    for index in range(len(rows)):
        excel_row, source_row = index + 5, index + 5
        for col in range(1, 15):
            all_candidates.cell(
                excel_row, col, f"='Source Data'!{get_column_letter(col)}{source_row}"
            )
            all_candidates.cell(excel_row, col).font = Font(color="008000")
        for score_index, factor in enumerate(FACTORS, 15):
            parameter_row = 5 + score_index - 15
            source_col = key_to_col[factor.key]
            normal = f"MAX(0,MIN(1,({source_col}{excel_row}-'Parameters'!$D${parameter_row})/('Parameters'!$E${parameter_row}-'Parameters'!$D${parameter_row})))"
            normal = f"(1-{normal})" if factor.key == "debt_to_equity" else normal
            all_candidates.cell(
                excel_row, score_index, f"='Parameters'!$C${parameter_row}*{normal}"
            )
        all_candidates.cell(excel_row, 24, f"=SUM(O{excel_row}:W{excel_row})")
        all_candidates.cell(
            excel_row,
            25,
            f"=IF(AND(X{excel_row}>='Parameters'!$B$17,E{excel_row}>'Parameters'!$B$18,F{excel_row}>'Parameters'!$B$19,M{excel_row}>='Parameters'!$B$20,G{excel_row}>'Parameters'!$B$21,H{excel_row}>'Parameters'!$B$22),\"ELIGIBLE\",\"NOT ELIGIBLE\")",
        )
        all_candidates.cell(
            excel_row, 26, f'=IF(Y{excel_row}="ELIGIBLE","RECOMMEND","WATCH / EXCLUDE")'
        )
        all_candidates.cell(
            excel_row,
            27,
            f'=IF(L{excel_row}>1.5,"High leverage; ","")&IF(K{excel_row}<10,"Low ROE; ","")&IF(M{excel_row}<1,"Below-average volume; ","")&IF(OR(E{excel_row}<=0,F{excel_row}<=0),"Momentum not positive; ","")&IF(OR(G{excel_row}<=0,H{excel_row}<=0),"Trend not positive","")',
        )
        for col in range(15, 28):
            all_candidates.cell(excel_row, col).font = Font(color="000000")
    _table_border(all_candidates, 4, 4 + len(rows), 1, 27)
    for row_number in range(5, 5 + len(rows)):
        all_candidates.cell(row_number, 4).number_format = "₹#,##0.00"
        for col in range(5, 12):
            all_candidates.cell(row_number, col).number_format = "0.0;[Red](0.0);-"
        all_candidates.cell(row_number, 12).number_format = "0.00x"
        all_candidates.cell(row_number, 13).number_format = "0.00x"
        all_candidates.cell(row_number, 14).number_format = "#,##0"
        all_candidates.cell(row_number, 24).number_format = "0.0"
        for col in range(15, 24):
            all_candidates.cell(row_number, col).number_format = "0.0"
    all_candidates.conditional_formatting.add(
        f"Y5:Y{4 + len(rows)}",
        CellIsRule(
            operator="equal",
            formula=['"ELIGIBLE"'],
            fill=PatternFill("solid", fgColor=GREEN),
        ),
    )
    all_candidates.conditional_formatting.add(
        f"Y5:Y{4 + len(rows)}",
        CellIsRule(
            operator="equal",
            formula=['"NOT ELIGIBLE"'],
            fill=PatternFill("solid", fgColor=RED),
        ),
    )
    all_candidates.auto_filter.ref = f"A4:AA{4 + len(rows)}"
    all_candidates.freeze_panes = "D5"
    _set_widths(
        all_candidates,
        [
            13,
            25,
            18,
            12,
            11,
            11,
            11,
            11,
            16,
            16,
            10,
            12,
            12,
            16,
            *([14] * 10),
            14,
            15,
            18,
        ],
    )

    # Snapshot of the current Python recommendation output.
    accepted = [row for row in rows if row.get("eligible")]
    _title(
        recommendations,
        "A1:N1",
        "NSE Positive Stock Screener — Current Recommendations",
    )
    recommendations.merge_cells("A2:N2")
    recommendations["A2"] = (
        "Current Python snapshot. Changing Parameters recalculates All Candidates; use it as the authoritative review sheet."
    )
    recommendations["A2"].fill = PatternFill("solid", fgColor=YELLOW)
    recommendations["A2"].font = Font(bold=True, color="7F6000")
    recommendations["A4"], recommendations["B4"] = "Candidates screened", len(rows)
    recommendations["A5"], recommendations["B5"] = "Recommended", len(accepted)
    recommendations["D4"], recommendations["E4"] = (
        "Model",
        "Positive trend + fundamentals",
    )
    for ref in ("A4", "A5", "D4"):
        recommendations[ref].fill = PatternFill("solid", fgColor=PALE_BLUE)
        recommendations[ref].font = Font(bold=True)
    recommendation_headers = [
        "Rank",
        "Symbol",
        "Company",
        "Sector",
        "Last price (₹)",
        "1M return (%)",
        "3M return (%)",
        "Vs 50DMA (%)",
        "Vs 200DMA (%)",
        "Revenue growth (%)",
        "ROE (%)",
        "Debt / equity",
        "Total score",
        "Risk flags",
    ]
    for col, value in enumerate(recommendation_headers, 1):
        recommendations.cell(8, col, value)
    _header(recommendations, 8, 1, 14)
    for row_number, record in enumerate(accepted, 9):
        values = [
            row_number - 8,
            record["symbol"],
            record["company_name"],
            record["sector"],
            record["last_price"],
            record["return_1m_pct"],
            record["return_3m_pct"],
            record["price_vs_50dma_pct"],
            record["price_vs_200dma_pct"],
            record["revenue_growth_yoy_pct"],
            record["roe_pct"],
            record["debt_to_equity"],
            record["score"],
            record["risk_flags"],
        ]
        for col, value in enumerate(values, 1):
            recommendations.cell(row_number, col, value)
    _table_border(recommendations, 8, max(9, 8 + len(accepted)), 1, 14)
    for row_number in range(9, 9 + len(accepted)):
        recommendations.cell(row_number, 5).number_format = "₹#,##0.00"
        for col in range(6, 12):
            recommendations.cell(row_number, col).number_format = "0.0;[Red](0.0);-"
        recommendations.cell(row_number, 12).number_format = "0.00x"
        recommendations.cell(row_number, 13).number_format = "0.0"
    recommendations.freeze_panes = "A9"
    _set_widths(
        recommendations, [18, 14, 28, 18, 14, 13, 13, 13, 13, 18, 12, 14, 13, 42]
    )

    # Checks
    _title(checks, "A1:F1", "Model Checks & Review Notes")
    for col, value in enumerate(
        ["Check", "Actual", "Expected", "Difference", "Status", "Review note"], 1
    ):
        checks.cell(3, col, value)
    _header(checks, 3, 1, 6)
    complete = sum(1 for row in rows if row.get("data_complete"))
    check_rows = [
        (
            "Weight total",
            sum(factor.weight for factor in FACTORS),
            100,
            0,
            "OK",
            "Weights should total 100.",
        ),
        (
            "Input rows",
            len(rows),
            "> 0",
            "",
            "OK" if rows else "FAIL",
            "At least one candidate is required.",
        ),
        (
            "Complete records",
            complete,
            len(rows),
            len(rows) - complete,
            "OK" if complete == len(rows) else "REVIEW",
            "Complete all required fields before relying on rank.",
        ),
        (
            "Recommendations",
            len(accepted),
            "Informational",
            "",
            "OK",
            "This is not a buy signal; review risk flags and current data.",
        ),
    ]
    for row_number, values in enumerate(check_rows, 4):
        for col, value in enumerate(values, 1):
            checks.cell(row_number, col, value)
    _table_border(checks, 3, 7, 1, 6)
    for cell in checks["E"][3:7]:
        cell.fill = PatternFill("solid", fgColor=GREEN if cell.value == "OK" else RED)
    checks.merge_cells("A10:F12")
    checks["A10"] = (
        "Model limitation: data may be incomplete or delayed. This workbook does not assess valuation, news, governance, event risk, sector cycles, or suitability."
    )
    checks["A10"].fill = PatternFill("solid", fgColor=RED)
    checks["A10"].font = Font(color="9C0006")
    checks["A10"].alignment = Alignment(wrap_text=True, vertical="center")
    _set_widths(checks, [24, 14, 14, 14, 14, 56])

    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    wb.calculation.calcMode = "auto"
    wb.save(output_file)
