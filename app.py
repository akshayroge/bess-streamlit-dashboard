from __future__ import annotations

import html
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR / "data" / "bess_dataset.json"


st.set_page_config(
    page_title="BESS System Dashboard",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
<style>
:root{
    --bg:#06101d;
    --panel:#0b1728;
    --line:#173b62;
    --txt:#f7fbff;
    --muted:#9bbad3;
    --cyan:#11cfe3;
    --green:#00c785;
    --amber:#d48a00;
    --violet:#6757ff;
    --pink:#ff4b72;
    --red:#ff5b5b;
}
html, body, [data-testid="stAppViewContainer"]{
    background:
        radial-gradient(circle at 20% 0, rgba(9,93,127,.24), transparent 32%),
        linear-gradient(180deg,#07111f,#05101c);
    color:var(--txt);
}
[data-testid="stHeader"]{
    background:rgba(0,0,0,0);
}
.block-container{
    padding-top:1.1rem;
    padding-bottom:2rem;
    max-width:1500px;
}
.bess-title{
    text-align:center;
    font-size:34px;
    font-weight:900;
    line-height:38px;
    margin-bottom:4px;
    color:#fff;
    text-shadow:0 2px 14px #000;
}
.bess-subtitle{
    text-align:center;
    color:#a8dfff;
    font-size:15px;
    margin-bottom:16px;
}
.control-box{
    border:1px solid #16456b;
    border-radius:12px;
    background:rgba(9,22,39,.92);
    padding:14px 16px;
    box-shadow:0 12px 30px rgba(0,0,0,.25);
    margin-bottom:14px;
}
.metric-wrap{
    border:1px solid #173b62;
    border-radius:12px;
    background:rgba(9,22,39,.92);
    padding:13px 16px;
    min-height:102px;
    box-shadow:0 12px 28px rgba(0,0,0,.22);
}
.metric-title{
    color:#a8d2e9;
    font-size:12px;
    line-height:16px;
}
.metric-value{
    color:#ffffff;
    font-size:27px;
    font-weight:900;
    line-height:32px;
    margin-top:5px;
}
.metric-foot{
    color:#8ecfff;
    font-size:11px;
    margin-top:6px;
}
.bess-card{
    min-height:238px;
    border-radius:12px;
    padding:14px 14px 12px;
    background:linear-gradient(180deg,rgba(14,30,51,.96),rgba(7,16,29,.98));
    box-shadow:0 12px 24px rgba(0,0,0,.35);
    overflow:hidden;
    margin-bottom:14px;
}
.bess-card h3{
    margin:0 0 8px;
    font-size:18px;
    text-transform:uppercase;
    letter-spacing:.25px;
    color:#fff;
}
.bess-card .sub{
    color:#b9dbef;
    font-size:12px;
    line-height:15px;
    margin-bottom:10px;
}
.accent-cell{border:1px solid #0bbe8a;background:linear-gradient(180deg,rgba(2,75,58,.88),rgba(3,34,35,.98));}
.accent-pack{border:1px solid #b87900;background:linear-gradient(180deg,rgba(59,42,7,.9),rgba(9,22,29,.98));}
.accent-rack{border:1px solid #625cff;background:linear-gradient(180deg,rgba(39,39,99,.9),rgba(8,18,34,.98));}
.accent-container{border:1px solid #b87900;background:linear-gradient(180deg,rgba(65,47,12,.9),rgba(8,20,24,.98));}
.accent-pcs{border:1px solid #e6466b;background:linear-gradient(180deg,rgba(66,23,42,.9),rgba(10,16,31,.98));}
.accent-grid{border:1px solid #29c8ff;}
.kv{
    display:grid;
    grid-template-columns:1fr auto;
    gap:7px;
    border-bottom:1px solid rgba(160,203,230,.12);
    padding:6px 0;
}
.kv:last-child{
    border-bottom:0;
}
.kv span{
    color:#a8d2e9;
    font-size:12px;
}
.kv b{
    color:white;
    font-size:13px;
    text-align:right;
}
.architecture-pill{
    border:1px solid #f2b600;
    border-radius:999px;
    background:linear-gradient(180deg,#322502,#101923);
    color:#ffdf60;
    padding:10px 18px;
    font-size:17px;
    font-weight:900;
    text-align:center;
    box-shadow:0 0 14px rgba(242,182,0,.22);
    margin:14px 0;
}
.sld-frame{
    border:1px solid #17d4ff;
    border-radius:13px;
    background:
        radial-gradient(circle at 50% 0,rgba(0,221,255,.16),transparent 34%),
        linear-gradient(180deg,#071727 0%,#030b15 100%);
    box-shadow:0 18px 42px rgba(0,0,0,.45), inset 0 0 0 1px rgba(23,212,255,.08);
    padding:18px;
    margin-top:10px;
}
.sld-chain{
    display:grid;
    grid-template-columns:1fr 34px 1fr 34px 1fr 34px 1.15fr 34px 1fr 34px .9fr;
    gap:8px;
    align-items:stretch;
}
.sld-node{
    border-radius:10px;
    background:linear-gradient(180deg,rgba(12,31,50,.96),rgba(4,13,24,.96));
    border:1px solid #22d9ff;
    padding:12px;
    min-height:170px;
    box-shadow:inset 0 0 18px rgba(0,217,255,.08),0 10px 22px rgba(0,0,0,.25);
}
.sld-node h4{
    margin:0 0 10px;
    color:#fff;
    font-size:16px;
    text-transform:uppercase;
}
.sld-arrow{
    color:#25dfff;
    text-shadow:0 0 10px #25dfff;
    font-size:30px;
    font-weight:900;
    display:flex;
    align-items:center;
    justify-content:center;
}
.sld-mini{
    display:grid;
    grid-template-columns:1fr auto;
    gap:3px 7px;
    font-size:12px;
    line-height:18px;
}
.sld-mini span{
    color:#aee6ff;
}
.sld-mini b{
    color:#fff;
    text-align:right;
}
.connection-grid{
    display:grid;
    grid-template-columns:repeat(6,1fr);
    gap:10px;
    margin-top:16px;
}
.connection-box{
    border:1px dashed rgba(30,215,255,.58);
    border-radius:10px;
    background:linear-gradient(180deg,rgba(8,23,39,.86),rgba(4,12,22,.9));
    padding:12px;
    min-height:155px;
}
.connection-box h4{
    margin:0 0 6px;
    color:#9edfff;
    font-size:15px;
    text-transform:uppercase;
    text-align:center;
}
.connection-box p{
    color:#d7efff;
    font-size:12px;
    line-height:16px;
    margin:6px 0;
}
.dataset-note{
    border-left:4px solid #11cfe3;
    background:rgba(17,207,227,.08);
    border-radius:8px;
    padding:12px 14px;
    color:#d9ecff;
    font-size:13px;
    line-height:18px;
}
@media(max-width:1100px){
    .sld-chain{
        grid-template-columns:1fr;
    }
    .sld-arrow{
        display:none;
    }
    .connection-grid{
        grid-template-columns:1fr;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


def esc(value: Any) -> str:
    if value is None:
        return "N/A"
    return html.escape(str(value))


def to_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return None
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned.lower() in {"", "na", "n/a", "none", "null", "-"}:
            return None
        match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
        if match:
            return float(match.group(0))
    return None


def fmt_num(value: Any, decimals: int = 1, na: str = "N/A") -> str:
    number = to_float(value)
    if number is None:
        return na
    text = f"{number:,.{decimals}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def fmt_unit(value: Any, unit: str, decimals: int = 1) -> str:
    number = to_float(value)
    if number is None:
        return "N/A"
    return f"{fmt_num(number, decimals)} {unit}"


def fmt_range(min_value: Any, max_value: Any, unit: str, decimals: int = 0) -> str:
    min_number = to_float(min_value)
    max_number = to_float(max_value)

    if min_number is None and max_number is None:
        return "N/A"
    if min_number is None:
        return f"≤ {fmt_unit(max_number, unit, decimals)}"
    if max_number is None:
        return f"≥ {fmt_unit(min_number, unit, decimals)}"

    return f"{fmt_num(min_number, decimals)}–{fmt_num(max_number, decimals)} {unit}"


def get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(part)
        if current is None:
            return default
    return current


def parse_c_rate(value: Any) -> Optional[float]:
    if value is None:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", str(value))
    if not match:
        return None
    return float(match.group(1))


def pluralize(value: Any, singular: str, plural: Optional[str] = None) -> str:
    number = to_float(value)
    plural_word = plural or f"{singular}s"
    if number is not None and abs(number - 1) < 1e-9:
        return singular
    return plural_word


def kv_rows(rows: List[Tuple[str, Any]]) -> str:
    return "".join(
        f"""
        <div class="kv">
            <span>{esc(label)}</span>
            <b>{esc(value)}</b>
        </div>
        """
        for label, value in rows
    )


def render_metric(title: str, value: Any, foot: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-wrap">
            <div class="metric-title">{esc(title)}</div>
            <div class="metric-value">{esc(value)}</div>
            <div class="metric-foot">{esc(foot)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_card(title: str, subtitle: str, rows: List[Tuple[str, Any]], accent: str) -> None:
    st.markdown(
        f"""
        <div class="bess-card accent-{accent}">
            <h3>{esc(title)}</h3>
            <div class="sub">{esc(subtitle)}</div>
            {kv_rows(rows)}
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_dataset() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset file not found at {DATA_PATH}. "
            "Create data/bess_dataset.json in the repository."
        )

    with DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_dataset(data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    required_sections = ["battery_containers", "c_rate_cases", "pcs_models"]

    for section in required_sections:
        if section not in data:
            errors.append(f"Missing top-level section: {section}")
        elif not isinstance(data[section], list):
            errors.append(f"Section must be a list: {section}")

    if errors:
        return errors, warnings

    battery_ids = set()
    pcs_ids = set()

    for index, battery in enumerate(data["battery_containers"], start=1):
        battery_id = battery.get("id")
        if not battery_id:
            errors.append(f"battery_containers row {index} is missing id.")
        elif battery_id in battery_ids:
            errors.append(f"Duplicate battery container id: {battery_id}")
        else:
            battery_ids.add(battery_id)

        if not battery.get("display_name"):
            warnings.append(f"Battery container {battery_id or index} is missing display_name.")

        if to_float(get_nested(battery, "container.nominal_energy_kwh")) is None:
            warnings.append(f"Battery container {battery_id or index} has no nominal_energy_kwh.")

        if to_float(get_nested(battery, "container.racks_per_container")) is None:
            warnings.append(f"Battery container {battery_id or index} has no racks_per_container.")

    for index, pcs in enumerate(data["pcs_models"], start=1):
        pcs_id = pcs.get("id")
        if not pcs_id:
            errors.append(f"pcs_models row {index} is missing id.")
        elif pcs_id in pcs_ids:
            errors.append(f"Duplicate PCS id: {pcs_id}")
        else:
            pcs_ids.add(pcs_id)

        if not pcs.get("display_name"):
            warnings.append(f"PCS {pcs_id or index} is missing display_name.")

    for index, case in enumerate(data["c_rate_cases"], start=1):
        case_id = case.get("id", f"row {index}")
        battery_id = case.get("battery_container_id")

        if not battery_id:
            errors.append(f"C-rate case {case_id} is missing battery_container_id.")
        elif battery_id not in battery_ids:
            errors.append(f"C-rate case {case_id} references unknown battery_container_id: {battery_id}")

        if not case.get("c_rate"):
            errors.append(f"C-rate case {case_id} is missing c_rate.")

        if to_float(case.get("containers_per_pcs")) is None:
            warnings.append(f"C-rate case {case_id} has no containers_per_pcs; app will estimate if possible.")

        if to_float(case.get("dc_bus_current_a")) is None:
            warnings.append(f"C-rate case {case_id} has no dc_bus_current_a; app will use fallback calculation.")

    return errors, warnings


def active_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [record for record in records if record.get("active", True) is not False]


def find_by_id(records: List[Dict[str, Any]], record_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if record_id is None:
        return None
    for record in records:
        if str(record.get("id")) == str(record_id):
            return record
    return None


def calculate_state(
    battery: Dict[str, Any],
    c_case: Dict[str, Any],
    pcs: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[str]]:
    notes: List[str] = []

    container = battery.get("container") or {}
    cell = battery.get("cell") or {}
    pack = battery.get("pack") or {}
    rack = battery.get("rack") or {}

    energy_kwh = to_float(container.get("nominal_energy_kwh"))
    energy_mwh = to_float(container.get("nominal_energy_mwh"))

    if energy_mwh is None and energy_kwh is not None:
        energy_mwh = energy_kwh / 1000

    c_rate_label = c_case.get("c_rate")
    c_rate_value = parse_c_rate(c_rate_label)

    power_kw = to_float(c_case.get("power_kw"))
    if power_kw is None and energy_kwh is not None and c_rate_value is not None:
        power_kw = energy_kwh * c_rate_value
        notes.append("Power was calculated from container energy × C-rate because power_kw is missing.")

    duration_hr = to_float(c_case.get("duration_hr"))
    if duration_hr is None and energy_kwh is not None and power_kw not in (None, 0):
        duration_hr = energy_kwh / power_kw
        notes.append("Duration was calculated from energy / power because duration_hr is missing.")

    dc_min = (
        to_float(pcs.get("dc_window_min_v"))
        or to_float(container.get("dc_window_min_v"))
        or to_float(rack.get("min_voltage_v"))
    )
    dc_max = (
        to_float(pcs.get("dc_window_max_v"))
        or to_float(container.get("dc_window_max_v"))
        or to_float(rack.get("max_voltage_v"))
    )

    nominal_dc = (
        to_float(container.get("dc_bus_nominal_voltage_v"))
        or to_float(rack.get("nominal_voltage_v"))
        or to_float(pack.get("nominal_voltage_v"))
    )

    current_a = to_float(c_case.get("dc_bus_current_a"))

    if current_a is None:
        current_a = to_float(container.get("dc_bus_current_a"))
        if current_a is not None:
            notes.append("DC bus current was taken from container default because C-rate value is missing.")

    if current_a is None and power_kw is not None and nominal_dc not in (None, 0):
        current_a = power_kw * 1000 / nominal_dc
        notes.append("DC bus current was calculated from power / nominal DC voltage.")

    pcs_rating_kw = to_float(pcs.get("rated_power_kw")) or to_float(pcs.get("rated_power_kva"))

    containers_per_pcs = to_float(c_case.get("containers_per_pcs"))
    if containers_per_pcs is None and pcs_rating_kw and power_kw:
        containers_per_pcs = max(1, math.floor(pcs_rating_kw / power_kw))
        notes.append("Containers per PCS was estimated from PCS rating / container power.")

    racks_per_container = to_float(container.get("racks_per_container"))

    racks_per_pcs = to_float(c_case.get("racks_per_pcs"))
    if racks_per_pcs is None and racks_per_container is not None and containers_per_pcs is not None:
        racks_per_pcs = racks_per_container * containers_per_pcs
        notes.append("Racks per PCS was calculated from racks per container × containers per PCS.")

    power_to_pcs_kw = None
    if power_kw is not None and containers_per_pcs is not None:
        power_to_pcs_kw = power_kw * containers_per_pcs

    utilisation_pct = to_float(c_case.get("pcs_utilisation_percent"))
    if utilisation_pct is None and power_to_pcs_kw is not None and pcs_rating_kw not in (None, 0):
        utilisation_pct = power_to_pcs_kw / pcs_rating_kw * 100
        notes.append("PCS utilisation was calculated from total DC power into PCS / PCS rating.")

    max_racks_per_pcs = to_float(pcs.get("max_racks_per_pcs"))

    if pcs_rating_kw is None:
        notes.append("Selected PCS is missing rated power.")
    if dc_min is None or dc_max is None:
        notes.append("Selected PCS/container/rack is missing a complete DC window.")
    if utilisation_pct is not None and utilisation_pct > 100:
        notes.append(f"PCS utilisation is above 100%: {fmt_num(utilisation_pct, 1)}%.")
    if racks_per_pcs is not None and max_racks_per_pcs is not None and racks_per_pcs > max_racks_per_pcs:
        notes.append(
            f"Racks per PCS ({fmt_num(racks_per_pcs, 0)}) exceeds selected PCS max racks "
            f"({fmt_num(max_racks_per_pcs, 0)})."
        )

    rack_current_a = to_float(rack.get("rack_current_a"))
    if rack_current_a is None and current_a is not None and racks_per_container not in (None, 0):
        rack_current_a = current_a / racks_per_container

    return {
        "battery": battery,
        "container": container,
        "cell": cell,
        "pack": pack,
        "rack": rack,
        "c_case": c_case,
        "pcs": pcs,
        "energy_kwh": energy_kwh,
        "energy_mwh": energy_mwh,
        "c_rate_label": c_rate_label,
        "c_rate_value": c_rate_value,
        "power_kw": power_kw,
        "duration_hr": duration_hr,
        "dc_min": dc_min,
        "dc_max": dc_max,
        "nominal_dc": nominal_dc,
        "current_a": current_a,
        "containers_per_pcs": containers_per_pcs,
        "racks_per_pcs": racks_per_pcs,
        "power_to_pcs_kw": power_to_pcs_kw,
        "pcs_rating_kw": pcs_rating_kw,
        "utilisation_pct": utilisation_pct,
        "max_racks_per_pcs": max_racks_per_pcs,
        "rack_current_a": rack_current_a,
    }, notes


def render_sld(state: Dict[str, Any]) -> None:
    battery = state["battery"]
    cell = state["cell"]
    pack = state["pack"]
    rack = state["rack"]
    container = state["container"]
    pcs = state["pcs"]

    containers = state["containers_per_pcs"]
    container_word = pluralize(containers, "container")

    nodes = [
        (
            "Cell",
            "LFP cell",
            [
                ("Voltage", fmt_unit(cell.get("nominal_voltage_v"), "V", 2)),
                ("Capacity", fmt_unit(cell.get("nominal_capacity_ah"), "Ah", 1)),
                ("Energy", fmt_unit(cell.get("cell_energy_wh"), "Wh", 1)),
            ],
            "cell",
        ),
        (
            "Pack",
            f"{fmt_num(pack.get('series_s'), 0)}S × {fmt_num(pack.get('parallel_p'), 0)}P",
            [
                ("Voltage", fmt_unit(pack.get("nominal_voltage_v"), "V", 1)),
                ("Capacity", fmt_unit(pack.get("nominal_capacity_ah"), "Ah", 1)),
                ("Energy", fmt_unit(pack.get("nominal_energy_kwh"), "kWh", 2)),
            ],
            "pack",
        ),
        (
            "Rack",
            f"{fmt_num(rack.get('packs_per_rack'), 0)} packs in {rack.get('pack_connection') or 'series'}",
            [
                ("Voltage", fmt_unit(rack.get("nominal_voltage_v"), "V", 1)),
                ("Energy", fmt_unit(rack.get("nominal_energy_kwh"), "kWh", 1)),
                ("Fuse", fmt_unit(rack.get("rack_fuse_a"), "A", 0)),
            ],
            "rack",
        ),
        (
            "Container",
            f"{fmt_num(container.get('racks_per_container'), 0)} racks parallel",
            [
                ("Energy", fmt_unit(state["energy_mwh"], "MWh", 2)),
                ("Bus V", fmt_range(state["dc_min"], state["dc_max"], "V", 0)),
                ("Bus I", fmt_unit(state["current_a"], "A", 1)),
            ],
            "container",
        ),
        (
            "PCS",
            pcs.get("model") or pcs.get("display_name") or "PCS",
            [
                ("Rating", fmt_unit(state["pcs_rating_kw"], "kW", 0)),
                ("AC V", fmt_unit(pcs.get("ac_voltage_v"), "V", 0)),
                ("Util.", fmt_unit(state["utilisation_pct"], "%", 1)),
            ],
            "pcs",
        ),
        (
            "AC Grid",
            "3-phase output",
            [
                ("AC Voltage", fmt_unit(pcs.get("ac_voltage_v"), "V", 0)),
                ("Conversion", "DC / AC"),
                ("Status", "Linked"),
            ],
            "grid",
        ),
    ]

    node_html = ""
    for index, (title, subtitle, rows, accent) in enumerate(nodes):
        row_html = "".join(
            f"<span>{esc(label)}</span><b>{esc(value)}</b>"
            for label, value in rows
        )

        node_html += f"""
        <div class="sld-node accent-{accent}">
            <h4>{esc(title)}</h4>
            <div class="sub">{esc(subtitle)}</div>
            <div class="sld-mini">{row_html}</div>
        </div>
        """

        if index < len(nodes) - 1:
            node_html += '<div class="sld-arrow">→</div>'

    st.markdown(
        f"""
        <div class="sld-frame">
            <h2 style="margin:0 0 6px;color:white;">Single Line Diagram</h2>
            <div style="color:#b9edff;margin-bottom:10px;">
                {esc(battery.get("display_name"))} | {esc(state["c_rate_label"])} |
                {esc(pcs.get("display_name"))}
            </div>
            <div class="sld-chain">
                {node_html}
            </div>
            <div class="architecture-pill">
                {esc(fmt_num(containers, 0))} {container_word} connected to 1 PCS
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    path = get_nested(battery, "sld.dc_connection_path")
    if not isinstance(path, list) or not path:
        path = ["String", "Rack Combiner", "DC Bus", "CC Panel", "PCS", "AC Grid"]

    detail_map = {
        "String": [
            "4 packs in series per rack/string.",
            f"Rack voltage: {fmt_unit(rack.get('nominal_voltage_v'), 'V', 1)}",
            f"Rack current: {fmt_unit(state['rack_current_a'], 'A', 1)}",
        ],
        "Rack Combiner": [
            f"{fmt_num(container.get('racks_per_container'), 0)} rack inputs in parallel.",
            f"Rack fuse: {fmt_unit(rack.get('rack_fuse_a'), 'A', 0)}",
            "HVCB / IMD / Pre-charge protection.",
        ],
        "DC Bus": [
            f"DC window: {fmt_range(state['dc_min'], state['dc_max'], 'V', 0)}",
            f"DC current: {fmt_unit(state['current_a'], 'A', 1)}",
            f"Energy: {fmt_unit(state['energy_mwh'], 'MWh', 2)}",
        ],
        "CC Panel": [
            "Main DC protection and copper busbar section.",
            "Protection coordination point.",
            "Container output routed to PCS DC input.",
        ],
        "PCS": [
            "DC / AC conversion.",
            f"Rating: {fmt_unit(state['pcs_rating_kw'], 'kW', 0)}",
            f"Utilisation: {fmt_unit(state['utilisation_pct'], '%', 1)}",
        ],
        "AC Grid": [
            "3-phase AC output.",
            f"AC voltage: {fmt_unit(pcs.get('ac_voltage_v'), 'V', 0)}",
            "Grid-side interface.",
        ],
    }

    boxes = ""
    for item in path:
        lines = detail_map.get(str(item), ["Configured from JSON dataset."])
        boxes += f"""
        <div class="connection-box">
            <h4>{esc(item)}</h4>
            {''.join(f'<p>{esc(line)}</p>' for line in lines)}
        </div>
        """

    st.markdown(
        f"""
        <div class="sld-frame">
            <h2 style="margin:0 0 8px;color:white;">Electrical Connection Path</h2>
            <div class="connection-grid">{boxes}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown('<div class="bess-title">BESS System Dashboard</div>', unsafe_allow_html=True)

try:
    data = load_dataset()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()
except json.JSONDecodeError as exc:
    st.error(f"Invalid JSON syntax in data/bess_dataset.json: {exc}")
    st.stop()
except Exception as exc:
    st.error(f"Unexpected dataset loading error: {exc}")
    st.stop()

validation_errors, validation_warnings = validate_dataset(data)

if validation_errors:
    st.error("Dataset has blocking validation errors.")
    for error in validation_errors:
        st.error(error)
    st.stop()

battery_records = active_records(data.get("battery_containers", []))
pcs_records = active_records(data.get("pcs_models", []))
c_rate_records = data.get("c_rate_cases", [])

if not battery_records:
    st.error("No active battery containers found in JSON.")
    st.stop()

if not pcs_records:
    st.error("No active PCS models found in JSON.")
    st.stop()

with st.sidebar:
    st.header("Dataset")
    st.caption("Fixed JSON backend. No runtime Excel upload.")
    st.success("Loaded: data/bess_dataset.json")

    if validation_warnings:
        st.warning(f"{len(validation_warnings)} dataset warning(s)")
        with st.expander("View warnings"):
            for warning in validation_warnings:
                st.write(f"- {warning}")
    else:
        st.success("Dataset validation passed")

    st.divider()
    st.caption("To refresh data, update data/bess_dataset.json and redeploy or rerun the app.")

rules = data.get("dashboard_rules", {})
default_battery_id = rules.get("selected_battery_container")
default_pcs_id = rules.get("selected_pcs")
default_c_rate = rules.get("selected_c_rate")

battery_display_to_record = {
    str(record.get("display_name") or record.get("id")): record
    for record in battery_records
}

pcs_display_to_record = {
    str(record.get("display_name") or record.get("id")): record
    for record in pcs_records
}

battery_names = list(battery_display_to_record.keys())
pcs_names = list(pcs_display_to_record.keys())

default_battery_record = find_by_id(battery_records, default_battery_id)
default_pcs_record = find_by_id(pcs_records, default_pcs_id)

default_battery_name = (
    str(default_battery_record.get("display_name") or default_battery_record.get("id"))
    if default_battery_record
    else battery_names[0]
)

default_pcs_name = (
    str(default_pcs_record.get("display_name") or default_pcs_record.get("id"))
    if default_pcs_record
    else pcs_names[0]
)

battery_index = battery_names.index(default_battery_name) if default_battery_name in battery_names else 0
pcs_index = pcs_names.index(default_pcs_name) if default_pcs_name in pcs_names else 0

st.markdown('<div class="control-box">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1.2, 0.7, 1.1])

with col1:
    selected_battery_name = st.selectbox(
        "Select Battery Container",
        options=battery_names,
        index=battery_index,
    )

selected_battery = battery_display_to_record[selected_battery_name]

matching_cases = [
    case
    for case in c_rate_records
    if str(case.get("battery_container_id")) == str(selected_battery.get("id"))
]

matching_cases = sorted(
    matching_cases,
    key=lambda row: parse_c_rate(row.get("c_rate"))
    if parse_c_rate(row.get("c_rate")) is not None
    else 9999,
)

if not matching_cases:
    with col2:
        st.selectbox("Select C-rate", options=["No C-rate rows found"], disabled=True)
    selected_case = None
else:
    c_rate_options = [str(case.get("c_rate")) for case in matching_cases]

    if default_c_rate in c_rate_options:
        c_rate_index = c_rate_options.index(default_c_rate)
    else:
        c_rate_index = 0

    with col2:
        selected_c_rate = st.selectbox(
            "Select C-rate",
            options=c_rate_options,
            index=c_rate_index,
        )

    selected_case = next(
        case for case in matching_cases if str(case.get("c_rate")) == str(selected_c_rate)
    )

with col3:
    selected_pcs_name = st.selectbox(
        "Select PCS",
        options=pcs_names,
        index=pcs_index,
    )

selected_pcs = pcs_display_to_record[selected_pcs_name]
st.markdown("</div>", unsafe_allow_html=True)

if selected_case is None:
    st.error(
        "The selected battery container has no C-rate cases. "
        "Add rows under c_rate_cases with matching battery_container_id."
    )
    st.stop()

state, calculation_notes = calculate_state(selected_battery, selected_case, selected_pcs)

subtitle = (
    f"{selected_battery.get('display_name')} | "
    f"{state['c_rate_label']} | "
    f"{selected_pcs.get('display_name')} | "
    f"{fmt_unit(state['energy_mwh'], 'MWh', 2)} | "
    f"{fmt_unit(state['power_kw'], 'kW', 0)}"
)

st.markdown(f'<div class="bess-subtitle">{esc(subtitle)}</div>', unsafe_allow_html=True)

critical_notes = []
info_notes = []

for note in calculation_notes:
    if "exceeds" in note or "above 100%" in note or "missing" in note:
        critical_notes.append(note)
    else:
        info_notes.append(note)

if critical_notes:
    with st.expander("Configuration warnings", expanded=True):
        for note in critical_notes:
            st.warning(note)

if info_notes:
    with st.expander("Calculation notes", expanded=False):
        for note in info_notes:
            st.info(note)

dashboard_tab, sld_tab, data_tab = st.tabs(
    ["Dashboard", "Single Line Diagram", "Data & Validation"]
)

with dashboard_tab:
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        render_metric("Total Energy", fmt_unit(state["energy_mwh"], "MWh", 2), "Container energy")
    with m2:
        render_metric("Power @ C-rate", fmt_unit(state["power_kw"], "kW", 0), state["c_rate_label"])
    with m3:
        render_metric("DC Bus Current", fmt_unit(state["current_a"], "A", 1), "From JSON / fallback calc")
    with m4:
        render_metric("DC Window", fmt_range(state["dc_min"], state["dc_max"], "V", 0), "PCS operating range")
    with m5:
        render_metric(
            "Containers / PCS",
            fmt_num(state["containers_per_pcs"], 0),
            f"{fmt_num(state['racks_per_pcs'], 0)} racks / PCS",
        )

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        cell = state["cell"]
        render_card(
            "Cell",
            selected_battery.get("chemistry") or "Cell electrical data",
            [
                ("Chemistry", selected_battery.get("chemistry")),
                ("Nominal Voltage", fmt_unit(cell.get("nominal_voltage_v"), "V", 2)),
                ("Min / Max Voltage", fmt_range(cell.get("min_voltage_v"), cell.get("max_voltage_v"), "V", 2)),
                ("Capacity", fmt_unit(cell.get("nominal_capacity_ah"), "Ah", 1)),
                ("Energy", fmt_unit(cell.get("cell_energy_wh"), "Wh", 1)),
                ("DCIR", fmt_unit(cell.get("internal_resistance_mohm"), "mΩ", 2)),
            ],
            "cell",
        )

    with c2:
        pack = state["pack"]
        render_card(
            "Pack",
            f"{fmt_num(pack.get('series_s'), 0)}S × {fmt_num(pack.get('parallel_p'), 0)}P",
            [
                ("Series", fmt_num(pack.get("series_s"), 0)),
                ("Parallel", fmt_num(pack.get("parallel_p"), 0)),
                ("Total Cells", fmt_num(pack.get("total_cells"), 0)),
                ("Nominal Voltage", fmt_unit(pack.get("nominal_voltage_v"), "V", 1)),
                ("Capacity", fmt_unit(pack.get("nominal_capacity_ah"), "Ah", 1)),
                ("Energy", fmt_unit(pack.get("nominal_energy_kwh"), "kWh", 2)),
                ("Protection", pack.get("protection")),
            ],
            "pack",
        )

    with c3:
        rack = state["rack"]
        protection = rack.get("protection") or {}

        if isinstance(protection, dict):
            protection_text = ", ".join(
                key.upper().replace("_", "-")
                for key, value in protection.items()
                if isinstance(value, bool) and value
            ) or "N/A"
        else:
            protection_text = protection

        render_card(
            "Rack",
            f"{fmt_num(rack.get('packs_per_rack'), 0)} packs {rack.get('pack_connection') or ''}",
            [
                ("Packs / Rack", fmt_num(rack.get("packs_per_rack"), 0)),
                ("Nominal Voltage", fmt_unit(rack.get("nominal_voltage_v"), "V", 1)),
                ("Voltage Window", fmt_range(rack.get("min_voltage_v"), rack.get("max_voltage_v"), "V", 0)),
                ("Capacity", fmt_unit(rack.get("nominal_capacity_ah"), "Ah", 1)),
                ("Energy", fmt_unit(rack.get("nominal_energy_kwh"), "kWh", 1)),
                ("Rack Current", fmt_unit(state["rack_current_a"], "A", 1)),
                ("Fuse", fmt_unit(rack.get("rack_fuse_a"), "A", 0)),
                ("Protection", protection_text),
            ],
            "rack",
        )

    with c4:
        container = state["container"]
        render_card(
            "Container",
            selected_battery.get("product_name") or selected_battery.get("display_name"),
            [
                ("Manufacturer", selected_battery.get("manufacturer")),
                ("Energy", fmt_unit(state["energy_mwh"], "MWh", 2)),
                ("Racks / Container", fmt_num(container.get("racks_per_container"), 0)),
                ("Cooling", container.get("cooling_type")),
                ("Nominal DC Bus", fmt_unit(state["nominal_dc"], "V", 0)),
                ("DC Window", fmt_range(state["dc_min"], state["dc_max"], "V", 0)),
                ("DC Bus Current", fmt_unit(state["current_a"], "A", 1)),
                ("Duration", fmt_unit(state["duration_hr"], "h", 1)),
            ],
            "container",
        )

    with c5:
        pcs = state["pcs"]

        status = "OK"
        if state["utilisation_pct"] is not None and state["utilisation_pct"] > 100:
            status = "Over 100%"
        if state["racks_per_pcs"] is not None and state["max_racks_per_pcs"] is not None:
            if state["racks_per_pcs"] > state["max_racks_per_pcs"]:
                status = "Rack limit exceeded"

        render_card(
            "PCS",
            pcs.get("display_name") or pcs.get("model"),
            [
                ("Manufacturer", pcs.get("manufacturer")),
                ("Rating", fmt_unit(state["pcs_rating_kw"], "kW", 0)),
                ("AC Voltage", fmt_unit(pcs.get("ac_voltage_v"), "V", 0)),
                ("DC Window", fmt_range(state["dc_min"], state["dc_max"], "V", 0)),
                ("DC Inputs", fmt_num(pcs.get("dc_inputs"), 0)),
                ("Efficiency", fmt_unit(pcs.get("efficiency_percent"), "%", 1)),
                ("Power into PCS", fmt_unit(state["power_to_pcs_kw"], "kW", 0)),
                ("Utilisation", fmt_unit(state["utilisation_pct"], "%", 1)),
                ("Status", status),
            ],
            "pcs",
        )

    container_word = pluralize(state["containers_per_pcs"], "container")

    st.markdown(
        f"""
        <div class="architecture-pill">
            Container-to-PCS architecture:
            {esc(fmt_num(state["containers_per_pcs"], 0))} {container_word} connected to 1 PCS
        </div>
        """,
        unsafe_allow_html=True,
    )

with sld_tab:
    render_sld(state)

with data_tab:
    st.markdown(
        """
        <div class="dataset-note">
            This app uses a fixed JSON backend. To append future records, edit
            <b>data/bess_dataset.json</b>, add new objects under
            <b>battery_containers</b>, <b>c_rate_cases</b>, or <b>pcs_models</b>,
            then rerun or redeploy the Streamlit app.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Selected Records")

    selected_payload = {
        "battery_container": selected_battery,
        "c_rate_case": selected_case,
        "pcs": selected_pcs,
        "calculated_state": {
            key: value
            for key, value in state.items()
            if key not in {"battery", "container", "cell", "pack", "rack", "c_case", "pcs"}
        },
    }

    st.json(selected_payload)

    st.subheader("Dataset Tables")

    battery_df = pd.DataFrame(data.get("battery_containers", []))
    c_rate_df = pd.DataFrame(data.get("c_rate_cases", []))
    pcs_df = pd.DataFrame(data.get("pcs_models", []))

    t1, t2, t3 = st.tabs(["Battery Containers", "C-rate Cases", "PCS Models"])

    with t1:
        st.dataframe(battery_df, use_container_width=True)

    with t2:
        st.dataframe(c_rate_df, use_container_width=True)

    with t3:
        st.dataframe(pcs_df, use_container_width=True)

    st.subheader("Validation")

    if validation_errors:
        for error in validation_errors:
            st.error(error)
    else:
        st.success("No blocking validation errors.")

    if validation_warnings:
        for warning in validation_warnings:
            st.warning(warning)
    else:
        st.success("No validation warnings.")

    st.download_button(
        label="Download current JSON dataset",
        data=json.dumps(data, indent=2),
        file_name="bess_dataset.json",
        mime="application/json",
    )