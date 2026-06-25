from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Sequence, Tuple
from xml.sax.saxutils import escape as xml_escape

from src.calculations import selected_objects


try:
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except Exception:  # pragma: no cover
    colors = None
    HexColor = None
    TA_CENTER = 1
    TA_LEFT = 0
    A4 = None
    landscape = None
    getSampleStyleSheet = None
    ParagraphStyle = None
    SimpleDocTemplate = None
    PageBreak = None
    Paragraph = None
    Spacer = None
    Table = None
    TableStyle = None
    mm = 1


PALETTE = {
    "bg": "#07111f",
    "card": "#101c2f",
    "card2": "#0b1727",
    "cyan": "#00d9ff",
    "cyan_soft": "#12384c",
    "orange": "#ff9900",
    "yellow": "#f0b900",
    "pink": "#ff517c",
    "green": "#60ff9b",
    "muted": "#94a7bf",
    "text": "#f4f8ff",
    "line": "#21435c",
    "white": "#ffffff",
    "danger_bg": "#402033",
    "warn_bg": "#3d3517",
    "good_bg": "#123426",
    "neutral_bg": "#0d2132",
}


def _require_reportlab() -> None:
    if SimpleDocTemplate is None:
        raise RuntimeError(
            "PDF export requires reportlab. Add `reportlab>=4.2.0` to requirements.txt "
            "and redeploy the Streamlit app."
        )


def _c(name: str):
    return HexColor(PALETTE[name])


def _clean(value: Any) -> str:
    text = "" if value is None else str(value)
    replacements = {
        "∞": "Infinity",
        "–": "-",
        "—": "-",
        "≥": ">=",
        "≤": "<=",
        "±": "+/-",
        "×": "x",
        "→": "->",
        "•": "-",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def _esc(value: Any) -> str:
    return xml_escape(_clean(value))


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _fmt(value: Any, decimals: int = 1) -> str:
    number = _num(value)

    if decimals == 0:
        return f"{round(number):,.0f}"

    return f"{number:,.{decimals}f}"


def _styles() -> Dict[str, Any]:
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=30,
            textColor=_c("white"),
            alignment=TA_LEFT,
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=_c("muted"),
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
        "section": ParagraphStyle(
            "ReportSection",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=_c("cyan"),
            alignment=TA_LEFT,
            spaceBefore=10,
            spaceAfter=8,
        ),
        "subsection": ParagraphStyle(
            "ReportSubSection",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=_c("white"),
            alignment=TA_LEFT,
            spaceBefore=8,
            spaceAfter=5,
        ),
        "normal": ParagraphStyle(
            "ReportNormal",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=_c("text"),
            alignment=TA_LEFT,
        ),
        "small": ParagraphStyle(
            "ReportSmall",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=_c("muted"),
            alignment=TA_LEFT,
        ),
        "small_white": ParagraphStyle(
            "ReportSmallWhite",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=_c("white"),
            alignment=TA_LEFT,
        ),
        "center": ParagraphStyle(
            "ReportCenter",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=_c("white"),
            alignment=TA_CENTER,
        ),
        "sld_card": ParagraphStyle(
            "SldCard",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.7,
            leading=8.5,
            textColor=_c("text"),
            alignment=TA_LEFT,
        ),
        "sld_title": ParagraphStyle(
            "SldTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=_c("white"),
            alignment=TA_CENTER,
        ),
    }


def _p(text: Any, style: Any) -> Any:
    return Paragraph(_esc(text), style)


def _rich(text: str, style: Any) -> Any:
    return Paragraph(text, style)


def _page_background(canvas, doc) -> None:
    width, height = landscape(A4)
    canvas.saveState()

    canvas.setFillColor(_c("bg"))
    canvas.rect(0, 0, width, height, fill=1, stroke=0)

    canvas.setStrokeColor(_c("cyan"))
    canvas.setLineWidth(0.45)
    canvas.line(18 * mm, height - 13 * mm, width - 18 * mm, height - 13 * mm)

    canvas.setFillColor(_c("muted"))
    canvas.setFont("Helvetica", 7)
    canvas.drawString(18 * mm, 10 * mm, "BESS Scenario Analysis Report")
    canvas.drawRightString(width - 18 * mm, 10 * mm, f"Page {doc.page}")

    canvas.restoreState()


def _table(data: Sequence[Sequence[Any]], col_widths: Optional[Sequence[float]] = None) -> Any:
    return Table(data, colWidths=col_widths, repeatRows=1)


def _table_base_style(header_rows: int = 1) -> List[Tuple[Any, ...]]:
    style: List[Tuple[Any, ...]] = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("LEADING", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), _c("text")),
        ("GRID", (0, 0), (-1, -1), 0.25, _c("line")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 0), (-1, -1), _c("card2")),
    ]

    if header_rows > 0:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, header_rows - 1), _c("card")),
                ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), _c("cyan")),
                ("FONTNAME", (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
            ]
        )

    return style


def _metric_value(result: Dict[str, Any], key: str) -> float:
    calc = result.get("calc", {})

    mapping = {
        "energy": calc.get("container_mwh", 0),
        "power": calc.get("power_kw", 0),
        "current": calc.get("dc_bus_current_a", 0),
        "duration": calc.get("duration_h", 0),
        "containers": calc.get("containers_per_pcs", 0),
        "utilisation": calc.get("pcs_utilization", 0),
        "max_racks": calc.get("max_racks_per_pcs", 0),
    }

    return _num(mapping.get(key))


def _metric_display(result: Dict[str, Any], key: str) -> str:
    calc = result.get("calc", {})

    if key == "energy":
        return f"{_fmt(calc.get('container_mwh'), 2)} MWh"
    if key == "power":
        return f"{_fmt(calc.get('power_kw'), 0)} kW"
    if key == "current":
        return f"{_fmt(calc.get('dc_bus_current_a'), 1)} A"
    if key == "duration":
        return f"{_fmt(calc.get('duration_h'), 1)} h"
    if key == "containers":
        return f"{int(round(_num(calc.get('containers_per_pcs'))))}"
    if key == "utilisation":
        return f"{_fmt(calc.get('pcs_utilization'), 1)} %"
    if key == "max_racks":
        return f"{int(round(_num(calc.get('max_racks_per_pcs'))))}"

    return "-"


def _best_result(results: List[Dict[str, Any]], key: str) -> Optional[Dict[str, Any]]:
    if not results:
        return None

    if key in ["energy", "power", "duration", "containers", "max_racks"]:
        return max(results, key=lambda result: _metric_value(result, key))

    if key == "current":
        return min(results, key=lambda result: _metric_value(result, key))

    if key == "utilisation":
        feasible = [result for result in results if _metric_value(result, key) <= 105]
        pool = feasible if feasible else results
        return min(pool, key=lambda result: abs(_metric_value(result, key) - 85))

    return results[0]


def _status_color(result: Dict[str, Any], key: str, best: Optional[Dict[str, Any]]) -> Any:
    value = _metric_value(result, key)
    util = _metric_value(result, "utilisation")

    if key == "power":
        if util > 105:
            return _c("danger_bg")
        if util >= 95:
            return _c("warn_bg")
        return _c("good_bg")

    if key == "current":
        if value >= 3000:
            return _c("danger_bg")
        if value >= 2400:
            return _c("warn_bg")
        return _c("good_bg")

    if key == "duration":
        if value < 2:
            return _c("danger_bg")
        if value < 3:
            return _c("warn_bg")
        if best is result:
            return _c("good_bg")
        return _c("neutral_bg")

    if key == "utilisation":
        if value > 105:
            return _c("danger_bg")
        if value >= 95:
            return _c("warn_bg")
        return _c("good_bg")

    if key in ["energy", "containers", "max_racks"]:
        if best is result:
            return _c("good_bg")
        return _c("neutral_bg")

    return _c("neutral_bg")


def _cover_page(story: List[Any], project_name: str, results: List[Dict[str, Any]], styles: Dict[str, Any]) -> None:
    story.append(_p("BESS Scenario Analysis Report", styles["title"]))
    story.append(
        _rich(
            f"<font color='{PALETTE['muted']}'>Project:</font> "
            f"<font color='{PALETTE['white']}'><b>{_esc(project_name)}</b></font>",
            styles["subtitle"],
        )
    )
    story.append(_p(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["subtitle"]))
    story.append(_p(f"Enabled scenarios: {len(results)}", styles["subtitle"]))
    story.append(Spacer(1, 12))

    rows = [["Scenario", "C-rate", "Container", "PCS"]]

    for result in results:
        rows.append(
            [
                f"Scenario {result['index'] + 1}",
                result.get("c_rate_label", ""),
                result.get("container_label", ""),
                result.get("pcs_label", ""),
            ]
        )

    table = _table(
        [[_p(cell, styles["normal"]) for cell in row] for row in rows],
        col_widths=[90, 70, 330, 190],
    )
    table.setStyle(TableStyle(_table_base_style()))
    story.append(table)
    story.append(Spacer(1, 14))

    highlights = _summary_highlights(results)
    highlight_rows = [
        ["Highest Energy", "Lowest DC Current", "Best PCS Utilisation", "Longest Duration"],
        [
            highlights["highest_energy"],
            highlights["lowest_current"],
            highlights["best_utilisation"],
            highlights["longest_duration"],
        ],
    ]

    highlight_table = _table(
        [[_p(cell, styles["center"]) for cell in row] for row in highlight_rows],
        col_widths=[170, 170, 170, 170],
    )
    highlight_table.setStyle(
        TableStyle(
            _table_base_style()
            + [
                ("BACKGROUND", (0, 1), (-1, 1), _c("good_bg")),
                ("TEXTCOLOR", (0, 1), (-1, 1), _c("green")),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(highlight_table)
    story.append(Spacer(1, 18))

    story.append(
        _p(
            "This report contains scenario inputs, calculated outputs, conditional comparison, "
            "scenario details, report-style SLDs, and engineering notes.",
            styles["normal"],
        )
    )


def _summary_highlights(results: List[Dict[str, Any]]) -> Dict[str, str]:
    highest_energy = _best_result(results, "energy")
    lowest_current = _best_result(results, "current")
    best_util = _best_result(results, "utilisation")
    longest_duration = _best_result(results, "duration")

    return {
        "highest_energy": _metric_display(highest_energy, "energy") if highest_energy else "-",
        "lowest_current": _metric_display(lowest_current, "current") if lowest_current else "-",
        "best_utilisation": _metric_display(best_util, "utilisation") if best_util else "-",
        "longest_duration": _metric_display(longest_duration, "duration") if longest_duration else "-",
    }


def _toc(story: List[Any], results: List[Dict[str, Any]], styles: Dict[str, Any]) -> None:
    story.append(_p("Table of Contents", styles["section"]))

    rows = [
        ["1", "Executive Summary"],
        ["2", "Scenario Input Summary"],
        ["3", "Scenario Output Comparison"],
    ]

    number = 4
    for result in results:
        rows.append([str(number), f"Scenario {result['index'] + 1} Details"])
        rows.append([f"{number}.1", "Selected System"])
        rows.append([f"{number}.2", "Equipment Parameters"])
        rows.append([f"{number}.3", "Single Line Diagram"])
        rows.append([f"{number}.4", "Electrical Connection Path"])
        number += 1

    rows.append([str(number), "Engineering Notes and Assumptions"])

    table = _table(
        [[_p(cell, styles["normal"]) for cell in row] for row in rows],
        col_widths=[70, 600],
    )
    table.setStyle(TableStyle(_table_base_style(header_rows=0)))
    story.append(table)


def _scenario_input_summary(story: List[Any], results: List[Dict[str, Any]], styles: Dict[str, Any]) -> None:
    story.append(_p("Scenario Input Summary", styles["section"]))

    rows = [["Scenario", "Enabled", "C-rate", "Container", "PCS"]]

    for result in results:
        rows.append(
            [
                f"Scenario {result['index'] + 1}",
                "Yes",
                result.get("c_rate_label", ""),
                result.get("container_label", ""),
                result.get("pcs_label", ""),
            ]
        )

    table = _table(
        [[_p(cell, styles["normal"]) for cell in row] for row in rows],
        col_widths=[75, 55, 60, 325, 165],
    )
    table.setStyle(TableStyle(_table_base_style()))
    story.append(table)


def _comparison_table(story: List[Any], results: List[Dict[str, Any]], styles: Dict[str, Any]) -> None:
    story.append(_p("Scenario Output Comparison", styles["section"]))
    story.append(
        _p(
            "Conditional formatting: green = good or best, yellow = acceptable/watch, red = high or overload.",
            styles["small"],
        )
    )
    story.append(Spacer(1, 5))

    metrics = [
        ("energy", "Total Energy"),
        ("power", "Power @ C-rate"),
        ("current", "DC Bus Current"),
        ("duration", "Duration"),
        ("containers", "Containers / PCS"),
        ("utilisation", "PCS Utilisation"),
        ("max_racks", "Max Racks / PCS"),
    ]

    header = ["Metric"] + [f"Scenario {result['index'] + 1}" for result in results]
    data = [[_p(cell, styles["center"]) for cell in header]]

    table_styles = _table_base_style()

    for row_index, (key, label) in enumerate(metrics, start=1):
        best = _best_result(results, key)
        row = [_p(label, styles["normal"])]

        for result in results:
            row.append(_p(_metric_display(result, key), styles["center"]))

        data.append(row)

        for col_index, result in enumerate(results, start=1):
            table_styles.append(("BACKGROUND", (col_index, row_index), (col_index, row_index), _status_color(result, key, best)))

    available_width = 680
    metric_width = 150
    scenario_width = (available_width - metric_width) / max(len(results), 1)

    table = _table(data, col_widths=[metric_width] + [scenario_width] * len(results))
    table.setStyle(TableStyle(table_styles))
    story.append(table)


def _scenario_section(story: List[Any], result: Dict[str, Any], styles: Dict[str, Any]) -> None:
    scenario_no = result["index"] + 1
    story.append(_p(f"Scenario {scenario_no} Details", styles["section"]))

    _selected_system_table(story, result, styles)
    story.append(Spacer(1, 8))
    _kpi_table(story, result, styles)
    story.append(Spacer(1, 8))
    _equipment_table(story, result, styles)
    story.append(Spacer(1, 10))
    _sld_report(story, result, styles)
    story.append(Spacer(1, 8))
    _connection_path_report(story, result, styles)


def _selected_system_table(story: List[Any], result: Dict[str, Any], styles: Dict[str, Any]) -> None:
    story.append(_p("Selected System", styles["subsection"]))

    rows = [
        ["Field", "Value"],
        ["Scenario", f"Scenario {result['index'] + 1}"],
        ["C-rate", result.get("c_rate_label", "")],
        ["Container", result.get("container_label", "")],
        ["PCS", result.get("pcs_label", "")],
    ]

    table = _table(
        [[_p(cell, styles["normal"]) for cell in row] for row in rows],
        col_widths=[120, 560],
    )
    table.setStyle(TableStyle(_table_base_style()))
    story.append(table)


def _kpi_table(story: List[Any], result: Dict[str, Any], styles: Dict[str, Any]) -> None:
    story.append(_p("Calculated Output", styles["subsection"]))

    calc = result.get("calc", {})

    rows = [
        ["Container Energy", "Power @ C-rate", "DC Bus Current", "Containers / PCS", "Duration", "PCS Utilisation"],
        [
            f"{_fmt(calc.get('container_mwh'), 2)} MWh",
            f"{_fmt(calc.get('power_kw'), 0)} kW",
            f"{_fmt(calc.get('dc_bus_current_a'), 1)} A",
            f"{int(round(_num(calc.get('containers_per_pcs'))))}",
            f"{_fmt(calc.get('duration_h'), 1)} h",
            f"{_fmt(calc.get('pcs_utilization'), 1)} %",
        ],
    ]

    table = _table(
        [[_p(cell, styles["center"]) for cell in row] for row in rows],
        col_widths=[113, 113, 113, 113, 113, 113],
    )
    table.setStyle(
        TableStyle(
            _table_base_style()
            + [
                ("BACKGROUND", (0, 1), (-1, 1), _c("neutral_bg")),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(table)


def _equipment_table(story: List[Any], result: Dict[str, Any], styles: Dict[str, Any]) -> None:
    story.append(_p("Equipment Parameters", styles["subsection"]))

    objs = selected_objects(result["working_db"])
    cell = objs["cell"]
    pack = objs["pack"]
    rack = objs["rack"]
    container = objs["container"]
    pcs = objs["pcs"]
    calc = result.get("calc", {})

    rows = [
        ["Component", "Parameter", "Value"],
        ["Cell", "Chemistry", cell.get("chemistry", "LFP")],
        ["Cell", "Nominal Voltage", f"{_fmt(cell.get('nominal_voltage_v'), 2)} V"],
        ["Cell", "Capacity", f"{_fmt(cell.get('capacity_ah'), 0)} Ah"],
        ["Pack", "Configuration", pack.get("configuration", f"{pack.get('cells_parallel', 1)}P{pack.get('cells_series', 104)}S")],
        ["Pack", "Energy", f"{_fmt(calc.get('pack_kwh'), 1)} kWh"],
        ["Rack/String", "Modules per String", rack.get("modules_per_string", rack.get("packs_series", 4))],
        ["Rack/String", "Voltage", f"{_fmt(calc.get('rack_v'), 1)} V"],
        ["Rack/String", "Energy", f"{_fmt(calc.get('rack_kwh'), 1)} kWh"],
        ["Container", "Racks per Container", container.get("racks_per_container", "-")],
        ["Container", "DC Window", calc.get("dc_window_text", "-")],
        ["Container", "Cooling", container.get("cooling", "Liquid Cooling")],
        ["PCS", "Rating", f"{_fmt(pcs.get('rating_kva'), 0)} kVA"],
        ["PCS", "AC Voltage", f"{_fmt(pcs.get('ac_voltage_v'), 0)} V"],
        ["PCS", "Efficiency", f"{_fmt(pcs.get('efficiency_percent'), 1)} %"],
    ]

    table = _table(
        [[_p(cell_value, styles["normal"]) for cell_value in row] for row in rows],
        col_widths=[120, 190, 370],
    )
    table.setStyle(TableStyle(_table_base_style()))
    story.append(table)


def _sld_card_text(title: str, rows: List[Tuple[str, str]], styles: Dict[str, Any]) -> Any:
    lines = [f"<b>{_esc(title)}</b>"]
    for label, value in rows:
        lines.append(f"<font color='{PALETTE['muted']}'>{_esc(label)}:</font> <b>{_esc(value)}</b>")

    return _rich("<br/>".join(lines), styles["sld_card"])


def _sld_report(story: List[Any], result: Dict[str, Any], styles: Dict[str, Any]) -> None:
    story.append(_p("Single Line Diagram", styles["subsection"]))

    objs = selected_objects(result["working_db"])
    cell = objs["cell"]
    pack = objs["pack"]
    rack = objs["rack"]
    container = objs["container"]
    pcs = objs["pcs"]
    calc = result.get("calc", {})

    cards = [
        _sld_card_text(
            "CELL",
            [
                ("Capacity", f"{_fmt(cell.get('capacity_ah'), 0)} Ah"),
                ("Voltage", f"{_fmt(cell.get('nominal_voltage_v'), 2)} V"),
                ("Energy", f"{_fmt(calc.get('cell_kwh'), 3)} kWh"),
            ],
            styles,
        ),
        _p("->", styles["center"]),
        _sld_card_text(
            "PACK",
            [
                ("Config", pack.get("configuration", f"{pack.get('cells_parallel', 1)}P{pack.get('cells_series', 104)}S")),
                ("Voltage", f"{_fmt(calc.get('pack_v'), 1)} V"),
                ("Energy", f"{_fmt(calc.get('pack_kwh'), 1)} kWh"),
            ],
            styles,
        ),
        _p("->", styles["center"]),
        _sld_card_text(
            "RACK / STRING",
            [
                ("Voltage", f"{_fmt(calc.get('rack_v'), 0)} V"),
                ("Energy", f"{_fmt(calc.get('rack_kwh'), 0)} kWh"),
                ("Modules", str(rack.get("modules_per_string", rack.get("packs_series", 4)))),
            ],
            styles,
        ),
        _p("->", styles["center"]),
        _sld_card_text(
            "CONTAINER",
            [
                ("Energy", f"{_fmt(calc.get('container_mwh'), 2)} MWh"),
                ("Bus V", calc.get("dc_window_text", "-")),
                ("Bus I", f"{_fmt(calc.get('dc_bus_current_a'), 1)} A"),
            ],
            styles,
        ),
        _p("->", styles["center"]),
        _sld_card_text(
            "PCS",
            [
                ("Rating", f"{_fmt(pcs.get('rating_kva'), 0)} kVA"),
                ("AC", f"{_fmt(pcs.get('ac_voltage_v'), 0)} V"),
                ("Eff", f"{_fmt(pcs.get('efficiency_percent'), 1)} %"),
            ],
            styles,
        ),
        _p("->", styles["center"]),
        _sld_card_text(
            "AC GRID",
            [
                ("Connection", "3-phase"),
                ("Voltage", f"{_fmt(pcs.get('ac_voltage_v'), 0)} V"),
                ("Std", "UL 1741"),
            ],
            styles,
        ),
    ]

    widths = [82, 16, 82, 16, 95, 16, 96, 16, 82, 16, 82]
    table = _table([cards], col_widths=widths)
    table_style = _table_base_style(header_rows=0)

    for col in [0, 2, 4, 6, 8, 10]:
        table_style.extend(
            [
                ("BACKGROUND", (col, 0), (col, 0), _c("card")),
                ("BOX", (col, 0), (col, 0), 0.65, _c("cyan")),
                ("VALIGN", (col, 0), (col, 0), "TOP"),
            ]
        )

    for col in [1, 3, 5, 7, 9]:
        table_style.extend(
            [
                ("BACKGROUND", (col, 0), (col, 0), _c("bg")),
                ("TEXTCOLOR", (col, 0), (col, 0), _c("cyan")),
                ("FONTNAME", (col, 0), (col, 0), "Helvetica-Bold"),
            ]
        )

    table.setStyle(TableStyle(table_style))
    story.append(table)


def _connection_path_report(story: List[Any], result: Dict[str, Any], styles: Dict[str, Any]) -> None:
    story.append(_p("Electrical Connection Path", styles["subsection"]))

    objs = selected_objects(result["working_db"])
    rack = objs["rack"]
    container = objs["container"]
    pcs = objs["pcs"]
    protection = objs["protection"]
    calc = result.get("calc", {})

    pack_fuse = protection.get("pack_fuse", {}).get("rating_a", 400)
    rack_hvcb = protection.get("rack_hvcb", {}).get("rating_a", rack.get("hvcb_a", 350))
    system_fuse = protection.get("system_fuse", {}).get("rating_a", 1800)

    blocks = [
        _sld_card_text(
            "STRING / RACK",
            [
                ("Series packs", str(rack.get("modules_per_string", rack.get("packs_series", 4)))),
                ("Pack fuse", f"{pack_fuse} A"),
                ("Rack HVCB", f"{rack_hvcb} A"),
            ],
            styles,
        ),
        _p("->", styles["center"]),
        _sld_card_text(
            "RACK COMBINER",
            [
                ("Strings", str(container.get("racks_per_container", "-"))),
                ("Rack output", calc.get("dc_window_text", "-")),
                ("Rack energy", f"{_fmt(calc.get('rack_kwh'), 1)} kWh"),
            ],
            styles,
        ),
        _p("->", styles["center"]),
        _sld_card_text(
            "DC BUS",
            [
                ("Voltage", calc.get("dc_window_text", "-")),
                ("Current", f"{_fmt(calc.get('dc_bus_current_a'), 1)} A"),
                ("Energy", f"{_fmt(calc.get('container_mwh'), 2)} MWh"),
            ],
            styles,
        ),
        _p("->", styles["center"]),
        _sld_card_text(
            "CC PANEL",
            [
                ("Main fuse", f"{system_fuse} A"),
                ("Protection", "DC collection"),
                ("Output", "To PCS"),
            ],
            styles,
        ),
        _p("->", styles["center"]),
        _sld_card_text(
            "PCS",
            [
                ("Rating", f"{_fmt(pcs.get('rating_kva'), 0)} kVA"),
                ("AC voltage", f"{_fmt(pcs.get('ac_voltage_v'), 0)} V"),
                ("Utilisation", f"{_fmt(calc.get('pcs_utilization'), 1)} %"),
            ],
            styles,
        ),
    ]

    widths = [120, 18, 120, 18, 105, 18, 120, 18, 105]
    table = _table([blocks], col_widths=widths)
    table_style = _table_base_style(header_rows=0)

    for col in [0, 2, 4, 6, 8]:
        table_style.extend(
            [
                ("BACKGROUND", (col, 0), (col, 0), _c("card")),
                ("BOX", (col, 0), (col, 0), 0.65, _c("orange")),
                ("VALIGN", (col, 0), (col, 0), "TOP"),
            ]
        )

    for col in [1, 3, 5, 7]:
        table_style.extend(
            [
                ("BACKGROUND", (col, 0), (col, 0), _c("bg")),
                ("TEXTCOLOR", (col, 0), (col, 0), _c("yellow")),
                ("FONTNAME", (col, 0), (col, 0), "Helvetica-Bold"),
            ]
        )

    table.setStyle(TableStyle(table_style))
    story.append(table)

    story.append(Spacer(1, 6))
    story.append(
        _p(
            f"Container-to-PCS architecture: {calc.get('architecture_text', '-')}. "
            f"Max racks per PCS: {calc.get('max_racks_per_pcs', '-')}.",
            styles["small"],
        )
    )


def _engineering_notes(story: List[Any], styles: Dict[str, Any]) -> None:
    story.append(_p("Engineering Notes and Assumptions", styles["section"]))

    notes = [
        ["Item", "Assumption / Rule"],
        ["Power @ C-rate", "Selected container energy multiplied by selected C-rate."],
        ["DC bus current", "Power x 1000 divided by selected container minimum DC voltage."],
        ["Containers per PCS", "Rounded ratio of PCS rated power to selected container power, minimum one."],
        ["PCS utilisation", "Connected container power divided by PCS rated power."],
        ["SLD", "Report-style SLD represents electrical sequence from cell to AC grid and string/rack to PCS."],
        ["Data source", "Current Streamlit scenario selections and data/db.json component database."],
    ]

    table = _table(
        [[_p(cell, styles["normal"]) for cell in row] for row in notes],
        col_widths=[150, 530],
    )
    table.setStyle(TableStyle(_table_base_style()))
    story.append(table)


def build_scenario_pdf_bytes(
    project_name: str,
    results: List[Dict[str, Any]],
) -> bytes:
    _require_reportlab()

    if not results:
        raise ValueError("No enabled scenarios were supplied for PDF export.")

    buffer = BytesIO()
    page_size = landscape(A4)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title="BESS Scenario Analysis Report",
        author="BESS Dashboard",
    )

    styles = _styles()
    story: List[Any] = []

    _cover_page(story, project_name, results, styles)
    story.append(PageBreak())

    _toc(story, results, styles)
    story.append(PageBreak())

    _scenario_input_summary(story, results, styles)
    story.append(Spacer(1, 12))
    _comparison_table(story, results, styles)

    for result in results:
        story.append(PageBreak())
        _scenario_section(story, result, styles)

    story.append(PageBreak())
    _engineering_notes(story, styles)

    doc.build(
        story,
        onFirstPage=_page_background,
        onLaterPages=_page_background,
    )

    return buffer.getvalue()
