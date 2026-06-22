import json
import traceback
from copy import deepcopy
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.assets import asset_to_data_uri, load_css
from src.calculations import calculate_dashboard
from src.excel_importer import detect_excel_values
from src.store import load_db, save_db
from src.ui import render_dashboard_html


DASHBOARD_IFRAME_HEIGHT = 2600


# ---------------------------------------------------------------------
# Base helpers
# ---------------------------------------------------------------------

def inject_css() -> None:
    css = load_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    st.markdown(
        """
<style>
/* Native Streamlit dropdown area placed below BESS Dashboard header */
.selector-panel {
    margin: -4px 0 18px 0;
    padding: 16px 18px 18px 18px;
    border: 1px solid rgba(0,217,255,.35);
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(0,217,255,.075), rgba(240,185,0,.045));
    box-shadow: 0 0 22px rgba(0,217,255,.08);
}

.selector-panel-title {
    color: #f4f8ff;
    font-size: 17px;
    font-weight: 800;
    margin-bottom: 4px;
}

.selector-panel-subtitle {
    color: #94a7bf;
    font-size: 13px;
    margin-bottom: 2px;
}

.selection-summary {
    margin: 4px 0 18px 0;
    padding: 12px 16px;
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 14px;
    background: rgba(255,255,255,.04);
    color: #f4f8ff;
    font-size: 13px;
}

.selection-summary b {
    color: #00d9ff;
}

div[data-testid="stSelectbox"] label {
    color: #f4f8ff !important;
    font-weight: 800 !important;
}

div[data-baseweb="select"] > div {
    background-color: rgba(7,17,31,.92) !important;
    border-color: rgba(0,217,255,.38) !important;
    border-radius: 12px !important;
    color: #f4f8ff !important;
}
</style>
""",
        unsafe_allow_html=True,
    )


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default

    if isinstance(value, str):
        text = value.strip().replace(",", "")
        if text in ["", "-", "NA", "N/A", "null", "None", "#DIV/0!"]:
            return default
        text = text.replace("%", "")
        try:
            return float(text)
        except Exception:
            return default

    try:
        if pd.isna(value):
            return default
    except Exception:
        pass

    try:
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    number = safe_float(value, float(default))
    try:
        return int(round(number))
    except Exception:
        return default


def is_blank(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    try:
        return bool(pd.isna(value))
    except Exception:
        return False


def first_value(*values: Any, default: Any = None) -> Any:
    for value in values:
        if not is_blank(value):
            return value
    return default


def get_nested(db: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    current: Any = db

    for key in path:
        if not isinstance(current, dict):
            return default
        if key not in current:
            return default
        current = current[key]

    return current


def parse_c_rate(c_rate_key: str) -> float:
    text = str(c_rate_key).strip().upper().replace("C", "")
    return safe_float(text, 0.0)


def format_number(value: Any, decimals: int = 1) -> str:
    number = safe_float(value, 0.0)

    if decimals == 0:
        return f"{round(number):,.0f}"

    return f"{number:,.{decimals}f}"


def default_index(options: List[str], preferred: Optional[str]) -> int:
    if preferred in options:
        return options.index(preferred)
    return 0


# ---------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------

def build_inline_dashboard_html(dashboard_html: str) -> str:
    css = load_css()

    return f"""
<style>
html, body {{
  margin: 0;
  padding: 0;
  background: transparent;
  overflow-x: hidden;
}}

* {{
  box-sizing: border-box;
}}

{css}

.bess-shell {{
  max-width: 1500px;
  margin: 0 auto;
  padding: 10px 10px 28px 10px;
}}
</style>

{dashboard_html}
"""


def build_iframe_dashboard_document(dashboard_html: str) -> str:
    css = load_css()

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      background: transparent;
      overflow-x: hidden;
    }}

    * {{
      box-sizing: border-box;
    }}

    {css}

    .bess-shell {{
      max-width: 1500px;
      margin: 0 auto;
      padding: 10px 10px 28px 10px;
    }}
  </style>
</head>
<body>
{dashboard_html}
</body>
</html>
"""


def render_dashboard_raw_html(dashboard_html: str) -> None:
    html_renderer = getattr(st, "html", None)

    if html_renderer is not None:
        html_renderer(build_inline_dashboard_html(dashboard_html))
    else:
        components.html(
            build_iframe_dashboard_document(dashboard_html),
            height=DASHBOARD_IFRAME_HEIGHT,
            scrolling=True,
        )


def strip_bess_header_from_dashboard_html(dashboard_html: str) -> str:
    """
    src.ui.render_dashboard_html() already includes the BESS header.
    Since we render the header separately to place Streamlit widgets below it,
    remove the duplicate header before rendering the rest of the dashboard.
    """
    start_marker = '<div class="bess-top">'
    next_section_marker = '<div class="grid3">'

    start = dashboard_html.find(start_marker)
    next_section = dashboard_html.find(next_section_marker, start)

    if start == -1 or next_section == -1:
        return dashboard_html

    return dashboard_html[:start] + dashboard_html[next_section:]


def render_exception_box(title: str, exc: Exception) -> None:
    st.error(title)
    st.caption(str(exc))

    with st.expander("Technical details"):
        st.code(traceback.format_exc(), language="python")


# ---------------------------------------------------------------------
# Dropdown options and display labels
# ---------------------------------------------------------------------

def get_c_rate_options(db: Dict[str, Any]) -> List[str]:
    options = get_nested(db, ["dropdowns", "c_rates"], None)

    if isinstance(options, list) and options:
        return [str(item) for item in options]

    profiles = get_nested(db, ["profiles", "c_rate_profiles"], {}) or {}

    if profiles:
        return list(profiles.keys())

    return ["0.25", "0.5", "1"]


def get_container_options(db: Dict[str, Any]) -> List[str]:
    options = get_nested(db, ["dropdowns", "containers"], None)

    if isinstance(options, list) and options:
        return [str(item) for item in options]

    containers = get_nested(db, ["catalog", "containers"], {}) or {}
    return list(containers.keys())


def get_pcs_options(db: Dict[str, Any]) -> List[str]:
    options = get_nested(db, ["dropdowns", "pcs"], None)

    if isinstance(options, list) and options:
        return [str(item) for item in options]

    pcs_catalog = get_nested(db, ["catalog", "pcs"], {}) or {}
    return list(pcs_catalog.keys())


def container_display_label(container_id: str, db: Dict[str, Any]) -> str:
    container = get_nested(db, ["catalog", "containers", container_id], {}) or {}

    if container.get("label"):
        return str(container["label"])

    company = first_value(
        container.get("manufacturer"),
        container.get("company"),
        default=""
    )

    model = first_value(
        container.get("model_name"),
        container.get("model"),
        container.get("name"),
        container_id,
        default=container_id
    )

    if company:
        return f"{company} | {model}"

    return str(model)


def pcs_display_label(pcs_id: str, db: Dict[str, Any]) -> str:
    pcs = get_nested(db, ["catalog", "pcs", pcs_id], {}) or {}

    if pcs.get("label"):
        return str(pcs["label"])

    model = first_value(
        pcs.get("model"),
        pcs.get("name"),
        pcs_id,
        default=pcs_id
    )

    manufacturer = first_value(
        pcs.get("manufacturer"),
        pcs.get("company"),
        default=""
    )

    if manufacturer:
        return f"{model} ({manufacturer})"

    return str(model)


def c_rate_display_label(c_rate_key: str) -> str:
    return str(c_rate_key)


# ---------------------------------------------------------------------
# Header and selector rendering
# ---------------------------------------------------------------------

def ensure_selection_state(db: Dict[str, Any]) -> None:
    c_rate_options = get_c_rate_options(db)
    container_options = get_container_options(db)
    pcs_options = get_pcs_options(db)

    selected = db.get("selected_components", {})

    default_c_rate = db.get("project", {}).get("default_c_rate", c_rate_options[0])
    default_container = selected.get("container", container_options[0])
    default_pcs = selected.get("pcs", pcs_options[0])

    if "selected_c_rate" not in st.session_state or st.session_state["selected_c_rate"] not in c_rate_options:
        st.session_state["selected_c_rate"] = default_c_rate if default_c_rate in c_rate_options else c_rate_options[0]

    if "selected_container" not in st.session_state or st.session_state["selected_container"] not in container_options:
        st.session_state["selected_container"] = default_container if default_container in container_options else container_options[0]

    if "selected_pcs" not in st.session_state or st.session_state["selected_pcs"] not in pcs_options:
        st.session_state["selected_pcs"] = default_pcs if default_pcs in pcs_options else pcs_options[0]


def render_bess_header(db: Dict[str, Any]) -> None:
    clou_logo = asset_to_data_uri(
        db.get("ui", {}).get("logos", {}).get("clou"),
        "CLOU"
    )

    midea_logo = asset_to_data_uri(
        db.get("ui", {}).get("logos", {}).get("midea"),
        "MIDEA"
    )

    selected_c_rate = st.session_state.get("selected_c_rate", db.get("project", {}).get("default_c_rate", "0.25"))

    header_html = f"""
<div class="bess-shell">
  <div class="bess-top">
    <div class="bess-title">
      <h1>{db["project"]["name"]}</h1>
      <p>{db["project"]["system_type"]} · Selected C-rate: <b>{selected_c_rate}</b></p>
    </div>

    <div class="logo-row">
      <div class="logo-box">
        <img src="{clou_logo}" alt="CLOU"/>
      </div>
      <div class="logo-box">
        <img src="{midea_logo}" alt="Midea"/>
      </div>
    </div>
  </div>
</div>
"""
    st.markdown(header_html, unsafe_allow_html=True)


def render_dropdown_panel(db: Dict[str, Any]) -> Dict[str, str]:
    c_rate_options = get_c_rate_options(db)
    container_options = get_container_options(db)
    pcs_options = get_pcs_options(db)

    st.markdown(
        """
<div class="selector-panel">
  <div class="selector-panel-title">System Selection</div>
  <div class="selector-panel-subtitle">Choose C-rate, BESS container, and PCS. The dashboard below updates automatically.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2.4, 1.7], gap="medium")

    with col1:
        selected_c_rate = st.selectbox(
            "1. C-rate",
            c_rate_options,
            index=default_index(c_rate_options, st.session_state.get("selected_c_rate")),
            format_func=c_rate_display_label,
            key="selected_c_rate",
            help="Options loaded from db.json → dropdowns.c_rates."
        )

    with col2:
        selected_container = st.selectbox(
            "2. Container",
            container_options,
            index=default_index(container_options, st.session_state.get("selected_container")),
            format_func=lambda key: container_display_label(key, db),
            key="selected_container",
            help="Options loaded from db.json → dropdowns.containers / catalog.containers."
        )

    with col3:
        selected_pcs = st.selectbox(
            "3. PCS",
            pcs_options,
            index=default_index(pcs_options, st.session_state.get("selected_pcs")),
            format_func=lambda key: pcs_display_label(key, db),
            key="selected_pcs",
            help="Options loaded from db.json → dropdowns.pcs / catalog.pcs."
        )

    return {
        "c_rate": selected_c_rate,
        "container": selected_container,
        "pcs": selected_pcs,
    }


# ---------------------------------------------------------------------
# Calculation and temporary working DB
# ---------------------------------------------------------------------

def resolve_selected_container(db: Dict[str, Any], container_id: str) -> Dict[str, Any]:
    container = get_nested(db, ["catalog", "containers", container_id], None)

    if not isinstance(container, dict):
        raise KeyError(f"Container id '{container_id}' was not found in catalog.containers.")

    return deepcopy(container)


def resolve_selected_pcs(db: Dict[str, Any], pcs_id: str) -> Dict[str, Any]:
    pcs = get_nested(db, ["catalog", "pcs", pcs_id], None)

    if not isinstance(pcs, dict):
        raise KeyError(f"PCS id '{pcs_id}' was not found in catalog.pcs.")

    return deepcopy(pcs)


def normalise_container(container: Dict[str, Any], container_id: str) -> Dict[str, Any]:
    energy_kwh = safe_float(
        first_value(
            container.get("energy_kwh"),
            container.get("total_energy_per_container_kwh"),
            container.get("total_energy_kwh"),
            default=0
        ),
        0.0
    )

    racks_per_container = safe_int(
        first_value(
            container.get("racks_per_container"),
            container.get("strings_per_container"),
            default=12
        ),
        12
    )

    if racks_per_container <= 0:
        racks_per_container = 1

    nominal_voltage = safe_float(
        first_value(
            container.get("nominal_voltage_v"),
            container.get("rack_nominal_voltage_v"),
            default=1331.2
        ),
        1331.2
    )

    dc_min = safe_float(
        first_value(
            container.get("dc_window_min_v"),
            container.get("minimum_voltage_v"),
            container.get("rack_minimum_voltage_v"),
            default=1040
        ),
        1040
    )

    dc_max = safe_float(
        first_value(
            container.get("dc_window_max_v"),
            container.get("maximum_voltage_v"),
            container.get("rack_maximum_voltage_v"),
            default=1518.4
        ),
        1518.4
    )

    container["id"] = container_id
    container["name"] = first_value(
        container.get("name"),
        container.get("model_name"),
        container.get("label"),
        container_id,
        default=container_id
    )
    container["manufacturer"] = first_value(
        container.get("manufacturer"),
        container.get("company"),
        default=""
    )
    container["technology"] = first_value(
        container.get("technology"),
        container.get("chemistry"),
        default="LFP"
    )
    container["racks_per_container"] = racks_per_container
    container["strings_per_container"] = racks_per_container
    container["energy_kwh"] = energy_kwh
    container["nominal_voltage_v"] = nominal_voltage
    container["dc_window_min_v"] = dc_min
    container["dc_window_max_v"] = dc_max
    container["cooling"] = first_value(
        container.get("cooling"),
        container.get("cooling_type"),
        default="Liquid Cooling"
    )
    container["image"] = first_value(
        container.get("image"),
        default="assets/images/equipment/bess_container.png"
    )

    return container


def normalise_pcs(pcs: Dict[str, Any], pcs_id: str) -> Dict[str, Any]:
    rating_kva = safe_float(
        first_value(
            pcs.get("rating_kva"),
            pcs.get("rated_power_kw"),
            default=5000
        ),
        5000
    )

    ac_voltage = safe_float(first_value(pcs.get("ac_voltage_v"), default=750), 750)
    dc_min = safe_float(first_value(pcs.get("dc_window_min_v"), default=976), 976)
    dc_max = safe_float(first_value(pcs.get("dc_window_max_v"), default=1061), 1061)
    efficiency = safe_float(first_value(pcs.get("efficiency_percent"), default=98.8), 98.8)

    pcs["id"] = pcs_id
    pcs["name"] = first_value(pcs.get("name"), pcs.get("model"), pcs_id, default=pcs_id)
    pcs["model"] = first_value(pcs.get("model"), pcs.get("name"), pcs_id, default=pcs_id)
    pcs["rating_kva"] = rating_kva
    pcs["rated_power_kw"] = safe_float(first_value(pcs.get("rated_power_kw"), rating_kva), rating_kva)
    pcs["ac_voltage_v"] = ac_voltage
    pcs["dc_window_min_v"] = dc_min
    pcs["dc_window_max_v"] = dc_max
    pcs["dc_inputs"] = safe_int(first_value(pcs.get("dc_inputs"), default=2), 2)
    pcs["efficiency_percent"] = efficiency
    pcs["image"] = first_value(pcs.get("image"), default="assets/images/equipment/pcs_nextpower.png")

    return pcs


def build_virtual_cell_pack_rack(container: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    cell_capacity = safe_float(
        first_value(
            container.get("cell_capacity_ah"),
            container.get("nominal_capacity_ah"),
            container.get("capacity_ah"),
            default=314
        ),
        314
    )

    cell_nominal_v = safe_float(
        first_value(
            container.get("cell_nominal_voltage_v"),
            container.get("nominal_cell_voltage_v"),
            default=3.2
        ),
        3.2
    )

    cell_energy_kwh = safe_float(first_value(container.get("cell_energy_kwh"), default=0), 0)

    if cell_energy_kwh <= 0:
        cell_energy_kwh = cell_capacity * cell_nominal_v / 1000

    racks_per_container = safe_int(container.get("racks_per_container"), 12)
    container_energy_kwh = safe_float(container.get("energy_kwh"), 0)

    rack_energy_kwh = safe_float(
        first_value(
            container.get("rack_energy_kwh"),
            container.get("energy_per_rack_kwh"),
            default=0
        ),
        0
    )

    if rack_energy_kwh <= 0 and container_energy_kwh > 0 and racks_per_container > 0:
        rack_energy_kwh = container_energy_kwh / racks_per_container

    if rack_energy_kwh <= 0:
        rack_energy_kwh = 418

    rack_nominal_v = safe_float(container.get("nominal_voltage_v"), 1331.2)
    rack_max_v = safe_float(container.get("dc_window_max_v"), 1518.4)
    rack_min_v = safe_float(container.get("dc_window_min_v"), 1040)

    modules_per_string = safe_int(
        first_value(
            container.get("modules_per_string"),
            container.get("packs_series"),
            default=4
        ),
        4
    )

    if modules_per_string <= 0:
        modules_per_string = 4

    pack_v = safe_float(
        first_value(
            container.get("pack_nominal_voltage_v"),
            container.get("module_nominal_voltage_v"),
            default=0
        ),
        0
    )

    if pack_v <= 0:
        pack_v = rack_nominal_v / modules_per_string

    pack_energy_kwh = safe_float(
        first_value(
            container.get("pack_energy_kwh"),
            container.get("module_energy_kwh"),
            default=0
        ),
        0
    )

    if pack_energy_kwh <= 0:
        pack_energy_kwh = rack_energy_kwh / modules_per_string

    cells_series = safe_int(
        first_value(
            container.get("cells_series"),
            container.get("series_per_module"),
            default=0
        ),
        0
    )

    if cells_series <= 0 and cell_nominal_v > 0:
        cells_series = max(1, round(pack_v / cell_nominal_v))

    if cells_series <= 0:
        cells_series = 104

    pack_parallel = safe_int(
        first_value(
            container.get("cells_parallel"),
            container.get("parallel_per_module"),
            default=1
        ),
        1
    )

    rack_capacity_ah = safe_float(
        first_value(
            container.get("rack_capacity_ah"),
            container.get("capacity_ah"),
            cell_capacity,
            default=cell_capacity
        ),
        cell_capacity
    )

    cell = {
        "name": f"{container.get('name', 'Selected Container')} Cell",
        "chemistry": first_value(container.get("technology"), container.get("chemistry"), default="LFP"),
        "nominal_voltage_v": cell_nominal_v,
        "capacity_ah": cell_capacity,
        "energy_kwh": cell_energy_kwh
    }

    pack = {
        "name": f"{container.get('name', 'Selected Container')} Pack",
        "configuration": f"{pack_parallel}P{cells_series}S",
        "cells_series": cells_series,
        "cells_parallel": pack_parallel,
        "nominal_voltage_v": pack_v,
        "capacity_ah": rack_capacity_ah,
        "energy_kwh": pack_energy_kwh,
        "fuse_a": safe_int(container.get("pack_fuse_a"), 400)
    }

    rack = {
        "name": f"{container.get('name', 'Selected Container')} Rack / String",
        "modules_per_string": modules_per_string,
        "packs_series": modules_per_string,
        "packs_parallel": 1,
        "total_series_per_string": cells_series * modules_per_string,
        "parallel_per_string": pack_parallel,
        "nominal_voltage_v": rack_nominal_v,
        "maximum_voltage_v": rack_max_v,
        "minimum_voltage_v": rack_min_v,
        "capacity_ah": rack_capacity_ah,
        "energy_kwh": rack_energy_kwh,
        "fuse_a": safe_int(container.get("rack_fuse_a"), 350),
        "hvcb_a": safe_int(container.get("rack_hvcb_a"), 350),
        "bmu_count": safe_int(container.get("bmu_count"), 4),
        "bcmu_count": safe_int(container.get("bcmu_count"), 1)
    }

    return {
        "cell": cell,
        "pack": pack,
        "rack": rack
    }


def compute_dynamic_profile(container: Dict[str, Any], pcs: Dict[str, Any], c_rate_key: str) -> Dict[str, Any]:
    c_rate = parse_c_rate(c_rate_key)

    container_energy_kwh = safe_float(container.get("energy_kwh"), 0)
    container_dc_min_v = safe_float(container.get("dc_window_min_v"), 0)
    pcs_rating_kw = safe_float(first_value(pcs.get("rated_power_kw"), pcs.get("rating_kva"), default=0), 0)

    power_kw = container_energy_kwh * c_rate if container_energy_kwh > 0 else 0

    if power_kw > 0 and container_dc_min_v > 0:
        dc_bus_current_a = power_kw * 1000 / container_dc_min_v
    else:
        dc_bus_current_a = 0

    if power_kw > 0 and pcs_rating_kw > 0:
        containers_per_pcs = max(1, int(round(pcs_rating_kw / power_kw)))
    else:
        containers_per_pcs = 1

    pcs_total_power_kw = containers_per_pcs * power_kw

    if pcs_rating_kw > 0:
        pcs_utilization = pcs_total_power_kw / pcs_rating_kw * 100
    else:
        pcs_utilization = 0

    return {
        "label": str(c_rate_key),
        "c_rate": c_rate,
        "power_kw": round(power_kw, 3),
        "dc_bus_current_a": round(dc_bus_current_a, 3),
        "containers_per_pcs": containers_per_pcs,
        "pcs_total_power_kw": round(pcs_total_power_kw, 3),
        "pcs_utilization_percent": round(pcs_utilization, 3)
    }


def build_working_db(
    db: Dict[str, Any],
    selected_c_rate: str,
    selected_container_id: str,
    selected_pcs_id: str
) -> Dict[str, Any]:
    working_db = deepcopy(db)

    container = normalise_container(resolve_selected_container(db, selected_container_id), selected_container_id)
    pcs = normalise_pcs(resolve_selected_pcs(db, selected_pcs_id), selected_pcs_id)

    virtual_components = build_virtual_cell_pack_rack(container)
    dynamic_profile = compute_dynamic_profile(container, pcs, selected_c_rate)

    working_db.setdefault("catalog", {})
    working_db["catalog"].setdefault("cells", {})
    working_db["catalog"].setdefault("packs", {})
    working_db["catalog"].setdefault("racks", {})
    working_db["catalog"].setdefault("containers", {})
    working_db["catalog"].setdefault("pcs", {})
    working_db["catalog"].setdefault("protection_devices", {})

    working_db["catalog"]["cells"]["selected_cell"] = virtual_components["cell"]
    working_db["catalog"]["packs"]["selected_pack"] = virtual_components["pack"]
    working_db["catalog"]["racks"]["selected_rack"] = virtual_components["rack"]
    working_db["catalog"]["containers"][selected_container_id] = container
    working_db["catalog"]["pcs"][selected_pcs_id] = pcs

    working_db.setdefault("selected_components", {})
    working_db["selected_components"]["cell"] = "selected_cell"
    working_db["selected_components"]["pack"] = "selected_pack"
    working_db["selected_components"]["rack"] = "selected_rack"
    working_db["selected_components"]["container"] = selected_container_id
    working_db["selected_components"]["pcs"] = selected_pcs_id

    working_db.setdefault("profiles", {})
    working_db["profiles"].setdefault("c_rate_profiles", {})
    working_db["profiles"]["c_rate_profiles"][selected_c_rate] = dynamic_profile

    working_db.setdefault("project", {})
    working_db["project"]["default_c_rate"] = selected_c_rate

    return working_db


def validate_minimum_db(db: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    required_paths = [
        ["project"],
        ["selected_components"],
        ["catalog"],
        ["catalog", "containers"],
        ["catalog", "pcs"]
    ]

    for path in required_paths:
        if get_nested(db, path) is None:
            errors.append("Missing required JSON section: " + " -> ".join(path))

    if not get_container_options(db):
        errors.append("No container dropdown options found. Add dropdowns.containers or catalog.containers.")

    if not get_pcs_options(db):
        errors.append("No PCS dropdown options found. Add dropdowns.pcs or catalog.pcs.")

    if not get_c_rate_options(db):
        errors.append("No C-rate dropdown options found. Add dropdowns.c_rates or profiles.c_rate_profiles.")

    return errors


# ---------------------------------------------------------------------
# Table edit helpers
# ---------------------------------------------------------------------

def flatten_item(item_id: str, item: Dict[str, Any]) -> Dict[str, Any]:
    row = {"id": item_id}

    for key, value in item.items():
        if isinstance(value, (dict, list)):
            row[key] = json.dumps(value)
        else:
            row[key] = value

    return row


def is_missing(value: Any) -> bool:
    try:
        result = pd.isna(value)

        if isinstance(result, bool):
            return result

        if hasattr(result, "any"):
            return bool(result.any())

        return bool(result)
    except Exception:
        return value is None


def convert_editor_value(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()

        if text.startswith("{") or text.startswith("["):
            try:
                return json.loads(text)
            except Exception:
                return text

        return text

    try:
        return value.item()
    except Exception:
        return value


def unflatten_table(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}

    for _, row in df.iterrows():
        item_id = str(row.get("id", "")).strip()

        if not item_id or item_id.lower() == "nan":
            continue

        item: Dict[str, Any] = {}

        for col in df.columns:
            if col == "id":
                continue

            value = row.get(col)

            if is_missing(value):
                continue

            item[col] = convert_editor_value(value)

        result[item_id] = item

    return result


# ---------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------

def dashboard_page(db: Dict[str, Any]) -> None:
    validation_errors = validate_minimum_db(db)

    if validation_errors:
        st.error("The JSON database is incomplete. Fix data/db.json before rendering the dashboard.")
        for item in validation_errors:
            st.warning(item)
        return

    ensure_selection_state(db)
    render_bess_header(db)
    selection = render_dropdown_panel(db)

    try:
        working_db = build_working_db(
            db=db,
            selected_c_rate=selection["c_rate"],
            selected_container_id=selection["container"],
            selected_pcs_id=selection["pcs"]
        )

        calc = calculate_dashboard(working_db, selection["c_rate"])

        st.markdown(
            f"""
<div class="selection-summary">
  <b>Selected:</b>
  C-rate {selection["c_rate"]} ·
  {container_display_label(selection["container"], db)} ·
  {pcs_display_label(selection["pcs"], db)}
  <br/>
  <b>Calculated:</b>
  Power {format_number(calc.get("power_kw"), 1)} kW ·
  DC Current {format_number(calc.get("dc_bus_current_a"), 1)} A ·
  Containers / PCS {calc.get("containers_per_pcs")} ·
  PCS Utilisation {format_number(calc.get("pcs_utilization"), 1)} %
</div>
""",
            unsafe_allow_html=True,
        )

        if st.button("Save current selection as default"):
            db.setdefault("project", {})
            db.setdefault("selected_components", {})

            db["project"]["default_c_rate"] = selection["c_rate"]
            db["selected_components"]["container"] = selection["container"]
            db["selected_components"]["pcs"] = selection["pcs"]

            save_db(db)
            st.success("Default selection saved to data/db.json.")

        dashboard_html = render_dashboard_html(working_db, selection["c_rate"])
        dashboard_html = strip_bess_header_from_dashboard_html(dashboard_html)
        render_dashboard_raw_html(dashboard_html)

    except Exception as exc:
        render_exception_box(
            "Dashboard rendering failed. Check selected container, PCS, and db.json field values.",
            exc
        )


def component_library_page(db: Dict[str, Any]) -> None:
    st.title("Component Library")
    st.caption("Add or edit cells, packs, racks, containers, PCS, and protection devices.")

    catalog = db.setdefault("catalog", {})
    library_names = list(catalog.keys())

    if not library_names:
        st.warning("No catalog libraries found in data/db.json.")
        return

    library_name = st.selectbox("Select library", library_names)
    collection = catalog[library_name]

    if not isinstance(collection, dict):
        st.warning("This library cannot be edited as a table.")
        return

    rows = [flatten_item(item_id, item) for item_id, item in collection.items()]
    df = pd.DataFrame(rows)

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
    )

    if st.button("Save library", type="primary"):
        try:
            db["catalog"][library_name] = unflatten_table(edited_df)
            save_db(db)
            st.success("Library saved to data/db.json.")
        except Exception as exc:
            render_exception_box("Could not save component library.", exc)


def c_rate_profiles_page(db: Dict[str, Any]) -> None:
    st.title("C-rate Profiles")
    st.caption("C-rate dropdown options are stored in db.json under dropdowns.c_rates.")

    c_rate_options = get_c_rate_options(db)

    df = pd.DataFrame(
        [
            {
                "c_rate_option": key,
                "numeric_c_rate": parse_c_rate(key)
            }
            for key in c_rate_options
        ]
    )

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
    )

    if st.button("Save C-rate dropdown options", type="primary"):
        try:
            new_options = []

            for _, row in edited_df.iterrows():
                value = str(row.get("c_rate_option", "")).strip()
                if value:
                    new_options.append(value)

            if not new_options:
                st.error("At least one C-rate option is required.")
                return

            db.setdefault("dropdowns", {})
            db["dropdowns"]["c_rates"] = new_options

            db.setdefault("profiles", {})
            db["profiles"].setdefault("c_rate_profiles", {})

            for option in new_options:
                db["profiles"]["c_rate_profiles"].setdefault(
                    option,
                    {
                        "label": option,
                        "c_rate": parse_c_rate(option),
                        "power_kw": 0,
                        "dc_bus_current_a": 0,
                        "containers_per_pcs": 1
                    }
                )

            save_db(db)
            st.success("C-rate dropdown options saved.")
        except Exception as exc:
            render_exception_box("Could not save C-rate options.", exc)


def excel_import_page(db: Dict[str, Any]) -> None:
    st.title("Excel Import")
    st.caption("Optional: upload workbook to inspect detected fields. Current dropdowns come from db.json.")

    uploaded_file = st.file_uploader(
        "Upload Excel workbook",
        type=["xlsx", "xlsm", "xls"]
    )

    if uploaded_file is None:
        st.info("Upload your sizing workbook to inspect detected current, energy, power, and containers per PCS.")
        return

    try:
        detected = detect_excel_values(uploaded_file)
    except Exception as exc:
        render_exception_box("Excel import failed. Please check workbook format and sheet data.", exc)
        return

    st.subheader("Detected values")
    if detected:
        st.json(detected)
    else:
        st.warning("No values were automatically detected.")

    st.info("For this app version, dropdown options and component values are controlled by data/db.json.")


def json_database_page(db: Dict[str, Any]) -> None:
    st.title("JSON Database")
    st.caption("View, edit, validate, and download the complete JSON database.")

    json_text = st.text_area(
        "data/db.json",
        value=json.dumps(db, indent=2),
        height=650,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Validate JSON"):
            try:
                new_db = json.loads(json_text)
                errors = validate_minimum_db(new_db)

                if errors:
                    st.warning("JSON syntax is valid, but dashboard sections are missing.")
                    for item in errors:
                        st.warning(item)
                else:
                    st.success("JSON is valid and dashboard sections are present.")
            except Exception as exc:
                st.error(f"Invalid JSON: {exc}")

    with col2:
        if st.button("Save JSON", type="primary"):
            try:
                new_db = json.loads(json_text)
                errors = validate_minimum_db(new_db)

                if errors:
                    st.error("JSON was not saved because required dashboard fields are missing.")
                    for item in errors:
                        st.warning(item)
                else:
                    save_db(new_db)
                    st.success("JSON saved to data/db.json.")
            except Exception as exc:
                render_exception_box("Could not save JSON.", exc)

    with col3:
        st.download_button(
            "Download db.json",
            data=json.dumps(db, indent=2),
            file_name="db.json",
            mime="application/json",
        )


def export_page(db: Dict[str, Any]) -> None:
    st.title("Export / Share")
    st.caption("Download JSON backup and review deployment information.")

    st.download_button(
        "Download full JSON database",
        data=json.dumps(db, indent=2),
        file_name="bess_dashboard_db.json",
        mime="application/json",
    )

    st.markdown(
        """
### Streamlit Cloud deployment

1. Push this full folder to GitHub.
2. Open Streamlit Cloud.
3. Click New app.
4. Select the GitHub repository.
5. Use `app.py` as the main file path.
6. Deploy.

### Important note about persistence

Local JSON editing works on a local PC or internal server.

On Streamlit Cloud, changes to local JSON files may reset after redeployment.

For a production multi-user version, store the JSON database in one of these:

- GitHub
- S3
- Azure Blob
- Google Cloud Storage
- Supabase
- PostgreSQL
- Google Sheets
"""
    )


def calculation_debug_page(db: Dict[str, Any]) -> None:
    st.title("Calculation Debug")
    st.caption("Inspect calculated output for any C-rate, container, and PCS selection.")

    c_rate_options = get_c_rate_options(db)
    container_options = get_container_options(db)
    pcs_options = get_pcs_options(db)

    selected_c_rate = st.selectbox("C-rate", c_rate_options)
    selected_container = st.selectbox(
        "Container",
        container_options,
        format_func=lambda key: container_display_label(key, db),
    )
    selected_pcs = st.selectbox(
        "PCS",
        pcs_options,
        format_func=lambda key: pcs_display_label(key, db),
    )

    try:
        working_db = build_working_db(
            db=db,
            selected_c_rate=selected_c_rate,
            selected_container_id=selected_container,
            selected_pcs_id=selected_pcs
        )

        result = calculate_dashboard(working_db, selected_c_rate)
        dynamic_profile = working_db["profiles"]["c_rate_profiles"][selected_c_rate]

        st.subheader("Dashboard calculation output")
        st.json(result)

        st.subheader("Dynamic profile")
        st.json(dynamic_profile)

        st.subheader("Selected container object")
        st.json(working_db["catalog"]["containers"][selected_container])

        st.subheader("Selected PCS object")
        st.json(working_db["catalog"]["pcs"][selected_pcs])

    except Exception as exc:
        render_exception_box(
            "Calculation failed. Check selected components and C-rate profile values.",
            exc,
        )


def main() -> None:
    st.set_page_config(
        page_title="BESS Streamlit Dashboard",
        page_icon="🔋",
        layout="wide",
    )

    inject_css()

    try:
        db = load_db()
    except Exception as exc:
        render_exception_box("Could not load data/db.json.", exc)
        st.stop()

    st.sidebar.title("BESS Dashboard")

    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Component Library",
            "C-rate Profiles",
            "Excel Import",
            "JSON Database",
            "Calculation Debug",
            "Export / Share",
        ],
    )

    try:
        if page == "Dashboard":
            dashboard_page(db)
        elif page == "Component Library":
            component_library_page(db)
        elif page == "C-rate Profiles":
            c_rate_profiles_page(db)
        elif page == "Excel Import":
            excel_import_page(db)
        elif page == "JSON Database":
            json_database_page(db)
        elif page == "Calculation Debug":
            calculation_debug_page(db)
        elif page == "Export / Share":
            export_page(db)
    except Exception as exc:
        render_exception_box("Unexpected application error.", exc)


if __name__ == "__main__":
    main()
