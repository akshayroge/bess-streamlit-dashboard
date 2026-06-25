import json
import traceback
from copy import deepcopy
from datetime import datetime
from html import escape
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.assets import load_css
from src.calculations import calculate_dashboard
from src.excel_importer import detect_excel_values
from src.store import load_db, save_db
from src.ui import render_cards_html, render_sld_html

try:
    from src.reporting import build_scenario_pdf_bytes
except Exception as report_import_error:
    build_scenario_pdf_bytes = None
    REPORT_IMPORT_ERROR = report_import_error
else:
    REPORT_IMPORT_ERROR = None


DASHBOARD_IFRAME_HEIGHT = 1600
CARDS_IFRAME_HEIGHT = 560
COMPARISON_TABLE_HEIGHT = 980

SCENARIO_ACCENTS = ["cyan", "yellow", "pink", "green"]
SCENARIO_NAMES = [
    "Scenario 1 (Baseline)",
    "Scenario 2",
    "Scenario 3",
    "Scenario 4",
]


# ---------------------------------------------------------------------
# CSS / HTML rendering
# ---------------------------------------------------------------------

def inject_css() -> None:
    css = load_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def build_inline_html(html: str) -> str:
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
}}
</style>

{html}
"""


def build_iframe_document(html: str) -> str:
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
    }}
  </style>
</head>
<body>
{html}
</body>
</html>
"""


def render_html_block(html: str, height: int = 600, scrolling: bool = False) -> None:
    html_renderer = getattr(st, "html", None)

    if html_renderer is not None:
        html_renderer(build_inline_html(html))
    else:
        components.html(
            build_iframe_document(html),
            height=height,
            scrolling=scrolling,
        )


def render_component_html(html: str, height: int = 900, scrolling: bool = True) -> None:
    components.html(
        build_iframe_document(html),
        height=height,
        scrolling=scrolling,
    )


def render_exception_box(title: str, exc: Exception) -> None:
    st.error(title)
    st.caption(str(exc))

    with st.expander("Technical details"):
        st.code(traceback.format_exc(), language="python")


# ---------------------------------------------------------------------
# Safe conversion helpers
# ---------------------------------------------------------------------

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


def c_rate_display_label(c_rate_key: str) -> str:
    return str(c_rate_key)


def c_rate_label(c_rate_key: str) -> str:
    text = str(c_rate_key).strip()
    if text.upper().endswith("C"):
        return text
    return f"{text}C"


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
# Dropdown helpers
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
        default="",
    )

    model = first_value(
        container.get("model_name"),
        container.get("model"),
        container.get("name"),
        container_id,
        default=container_id,
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
        default=pcs_id,
    )

    manufacturer = first_value(
        pcs.get("manufacturer"),
        pcs.get("company"),
        default="",
    )

    if manufacturer:
        return f"{model} ({manufacturer})"

    return str(model)


# ---------------------------------------------------------------------
# Navigation helpers
# ---------------------------------------------------------------------

def request_navigation(page_name: str) -> None:
    st.session_state["pending_nav_page"] = page_name
    st.rerun()


# ---------------------------------------------------------------------
# Main selection state
# ---------------------------------------------------------------------

def ensure_selection_state(db: Dict[str, Any]) -> None:
    c_rate_options = get_c_rate_options(db)
    container_options = get_container_options(db)
    pcs_options = get_pcs_options(db)

    if not c_rate_options:
        c_rate_options = ["0.25"]
    if not container_options:
        container_options = [""]
    if not pcs_options:
        pcs_options = [""]

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


def current_dashboard_selection(db: Dict[str, Any]) -> Dict[str, str]:
    ensure_selection_state(db)
    return {
        "c_rate": st.session_state["selected_c_rate"],
        "container": st.session_state["selected_container"],
        "pcs": st.session_state["selected_pcs"],
    }


# ---------------------------------------------------------------------
# Header and dashboard controls
# ---------------------------------------------------------------------

def render_bess_header(db: Dict[str, Any]) -> None:
    header_html = f"""
<div class="bess-shell">
  <div class="bess-top clean-bess-header">
    <div class="bess-title">
      <h1>{escape(db.get("project", {}).get("name", "BESS Dashboard"))}</h1>
    </div>
  </div>
</div>
"""
    render_html_block(header_html, height=120, scrolling=False)


def render_dropdown_panel(db: Dict[str, Any]) -> Dict[str, str]:
    c_rate_options = get_c_rate_options(db)
    container_options = get_container_options(db)
    pcs_options = get_pcs_options(db)

    with st.container(border=True):
        st.markdown(
            """
<div class="selector-panel-title">System Selection</div>
<div class="selector-panel-subtitle">Choose C-rate, BESS container, and PCS. The dashboard updates automatically.</div>
""",
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns([1.0, 2.25, 1.65, 1.05], gap="medium")

        with col1:
            selected_c_rate = st.selectbox(
                "1. C-rate",
                c_rate_options,
                index=default_index(c_rate_options, st.session_state.get("selected_c_rate")),
                format_func=c_rate_display_label,
                key="selected_c_rate",
            )

        with col2:
            selected_container = st.selectbox(
                "2. Container",
                container_options,
                index=default_index(container_options, st.session_state.get("selected_container")),
                format_func=lambda key: container_display_label(key, db),
                key="selected_container",
            )

        with col3:
            selected_pcs = st.selectbox(
                "3. PCS",
                pcs_options,
                index=default_index(pcs_options, st.session_state.get("selected_pcs")),
                format_func=lambda key: pcs_display_label(key, db),
                key="selected_pcs",
            )

        with col4:
            st.markdown("<div class='scenario-button-spacer'></div>", unsafe_allow_html=True)
            if st.button("📊 Scenario Analysis", key="open_scenario_analysis", use_container_width=True, type="primary"):
                sync_scenario_one_from_dashboard(db)
                request_navigation("Scenario Analysis")

    return {
        "c_rate": selected_c_rate,
        "container": selected_container,
        "pcs": selected_pcs,
    }


# ---------------------------------------------------------------------
# Working DB construction
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
            default=0,
        ),
        0.0,
    )

    racks_per_container = safe_int(
        first_value(
            container.get("racks_per_container"),
            container.get("strings_per_container"),
            default=12,
        ),
        12,
    )

    if racks_per_container <= 0:
        racks_per_container = 1

    nominal_voltage = safe_float(
        first_value(
            container.get("nominal_voltage_v"),
            container.get("rack_nominal_voltage_v"),
            default=1331.2,
        ),
        1331.2,
    )

    dc_min = safe_float(
        first_value(
            container.get("dc_window_min_v"),
            container.get("minimum_voltage_v"),
            container.get("rack_minimum_voltage_v"),
            default=1040,
        ),
        1040,
    )

    dc_max = safe_float(
        first_value(
            container.get("dc_window_max_v"),
            container.get("maximum_voltage_v"),
            container.get("rack_maximum_voltage_v"),
            default=1518.4,
        ),
        1518.4,
    )

    container["id"] = container_id
    container["name"] = first_value(
        container.get("name"),
        container.get("model_name"),
        container.get("label"),
        container_id,
        default=container_id,
    )
    container["manufacturer"] = first_value(
        container.get("manufacturer"),
        container.get("company"),
        default="",
    )
    container["technology"] = first_value(
        container.get("technology"),
        container.get("chemistry"),
        default="LFP",
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
        default="Liquid Cooling",
    )
    container["image"] = first_value(
        container.get("image"),
        default="assets/images/equipment/bess_container.png",
    )

    return container


def normalise_pcs(pcs: Dict[str, Any], pcs_id: str) -> Dict[str, Any]:
    rating_kva = safe_float(
        first_value(
            pcs.get("rating_kva"),
            pcs.get("rated_power_kw"),
            default=5000,
        ),
        5000,
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
            default=314,
        ),
        314,
    )

    cell_nominal_v = safe_float(
        first_value(
            container.get("cell_nominal_voltage_v"),
            container.get("nominal_cell_voltage_v"),
            default=3.2,
        ),
        3.2,
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
            default=0,
        ),
        0,
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
            default=4,
        ),
        4,
    )

    if modules_per_string <= 0:
        modules_per_string = 4

    pack_v = safe_float(
        first_value(
            container.get("pack_nominal_voltage_v"),
            container.get("module_nominal_voltage_v"),
            default=0,
        ),
        0,
    )

    if pack_v <= 0:
        pack_v = rack_nominal_v / modules_per_string

    pack_energy_kwh = safe_float(
        first_value(
            container.get("pack_energy_kwh"),
            container.get("module_energy_kwh"),
            default=0,
        ),
        0,
    )

    if pack_energy_kwh <= 0:
        pack_energy_kwh = rack_energy_kwh / modules_per_string

    cells_series = safe_int(
        first_value(
            container.get("cells_series"),
            container.get("series_per_module"),
            default=0,
        ),
        0,
    )

    if cells_series <= 0 and cell_nominal_v > 0:
        cells_series = max(1, round(pack_v / cell_nominal_v))

    if cells_series <= 0:
        cells_series = 104

    pack_parallel = safe_int(
        first_value(
            container.get("cells_parallel"),
            container.get("parallel_per_module"),
            default=1,
        ),
        1,
    )

    rack_capacity_ah = safe_float(
        first_value(
            container.get("rack_capacity_ah"),
            container.get("capacity_ah"),
            cell_capacity,
            default=cell_capacity,
        ),
        cell_capacity,
    )

    cell = {
        "name": f"{container.get('name', 'Selected Container')} Cell",
        "chemistry": first_value(container.get("technology"), container.get("chemistry"), default="LFP"),
        "nominal_voltage_v": cell_nominal_v,
        "maximum_cell_voltage_v": safe_float(container.get("maximum_cell_voltage_v"), 3.65),
        "minimum_cell_voltage_v": safe_float(container.get("minimum_cell_voltage_v"), 2.5),
        "capacity_ah": cell_capacity,
        "energy_kwh": cell_energy_kwh,
        "image": first_value(
            container.get("cell_image"),
            container.get("cell_image_path"),
            default="assets/images/equipment/cell.png",
        ),
    }

    pack = {
        "name": f"{container.get('name', 'Selected Container')} Pack",
        "configuration": f"{pack_parallel}P{cells_series}S",
        "cells_series": cells_series,
        "cells_parallel": pack_parallel,
        "nominal_voltage_v": pack_v,
        "capacity_ah": rack_capacity_ah,
        "energy_kwh": pack_energy_kwh,
        "fuse_a": safe_int(container.get("pack_fuse_a"), 400),
        "image": first_value(
            container.get("pack_image"),
            container.get("pack_image_path"),
            default="assets/images/equipment/pack.png",
        ),
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
        "bcmu_count": safe_int(container.get("bcmu_count"), 1),
        "image": first_value(
            container.get("rack_image"),
            container.get("rack_image_path"),
            default="assets/images/equipment/rack.png",
        ),
    }

    return {
        "cell": cell,
        "pack": pack,
        "rack": rack,
    }


def compute_dynamic_profile(
    container: Dict[str, Any],
    pcs: Dict[str, Any],
    c_rate_key: str,
) -> Dict[str, Any]:
    c_rate = parse_c_rate(c_rate_key)

    container_energy_kwh = safe_float(container.get("energy_kwh"), 0)
    container_dc_min_v = safe_float(container.get("dc_window_min_v"), 0)
    pcs_rating_kw = safe_float(first_value(pcs.get("rated_power_kw"), pcs.get("rating_kva"), default=0), 0)

    power_kw = container_energy_kwh * c_rate if container_energy_kwh > 0 else 0
    dc_bus_current_a = power_kw * 1000 / container_dc_min_v if power_kw > 0 and container_dc_min_v > 0 else 0

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
        "pcs_utilization_percent": round(pcs_utilization, 3),
    }


def build_working_db(
    db: Dict[str, Any],
    selected_c_rate: str,
    selected_container_id: str,
    selected_pcs_id: str,
) -> Dict[str, Any]:
    working_db = deepcopy(db)

    container = normalise_container(
        resolve_selected_container(db, selected_container_id),
        selected_container_id,
    )
    pcs = normalise_pcs(
        resolve_selected_pcs(db, selected_pcs_id),
        selected_pcs_id,
    )

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
        ["catalog", "pcs"],
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
# Scenario analysis state and calculations
# ---------------------------------------------------------------------

def option_at(options: List[str], index: int, fallback: Optional[str] = None) -> str:
    if not options:
        return fallback or ""
    if index < len(options):
        return options[index]
    return fallback if fallback in options else options[0]


def create_default_scenarios(db: Dict[str, Any]) -> List[Dict[str, Any]]:
    main = current_dashboard_selection(db)

    c_rates = get_c_rate_options(db)
    containers = get_container_options(db)
    pcs_options = get_pcs_options(db)

    container_0 = main["container"]
    pcs_0 = main["pcs"]

    return [
        {
            "name": "Scenario 1 (Baseline)",
            "enabled": True,
            "c_rate": main["c_rate"],
            "container": main["container"],
            "pcs": main["pcs"],
            "accent": "cyan",
        },
        {
            "name": "Scenario 2",
            "enabled": True,
            "c_rate": option_at(c_rates, 1, main["c_rate"]),
            "container": container_0,
            "pcs": pcs_0,
            "accent": "yellow",
        },
        {
            "name": "Scenario 3",
            "enabled": True,
            "c_rate": option_at(c_rates, 2, main["c_rate"]),
            "container": option_at(containers, 2, container_0),
            "pcs": option_at(pcs_options, 3, pcs_0),
            "accent": "pink",
        },
        {
            "name": "Scenario 4",
            "enabled": True,
            "c_rate": option_at(c_rates, 0, main["c_rate"]),
            "container": option_at(containers, 1, container_0),
            "pcs": option_at(pcs_options, 1, pcs_0),
            "accent": "green",
        },
    ]


def clear_scenario_widget_keys() -> None:
    prefixes = [
        "cmp_enabled_",
        "cmp_c_rate_",
        "cmp_container_",
        "cmp_pcs_",
    ]

    for key in list(st.session_state.keys()):
        if any(str(key).startswith(prefix) for prefix in prefixes):
            del st.session_state[key]


def ensure_comparison_state(db: Dict[str, Any]) -> None:
    if "comparison_scenarios" not in st.session_state:
        st.session_state["comparison_scenarios"] = create_default_scenarios(db)

    scenarios = st.session_state["comparison_scenarios"]

    if not isinstance(scenarios, list) or len(scenarios) != 4:
        st.session_state["comparison_scenarios"] = create_default_scenarios(db)
        clear_scenario_widget_keys()
        return

    c_rates = get_c_rate_options(db)
    containers = get_container_options(db)
    pcs_options = get_pcs_options(db)

    for index, scenario in enumerate(st.session_state["comparison_scenarios"]):
        scenario.setdefault("name", SCENARIO_NAMES[index])
        scenario.setdefault("enabled", True)
        scenario.setdefault("accent", SCENARIO_ACCENTS[index])

        if scenario.get("c_rate") not in c_rates:
            scenario["c_rate"] = c_rates[0]
        if scenario.get("container") not in containers:
            scenario["container"] = containers[0]
        if scenario.get("pcs") not in pcs_options:
            scenario["pcs"] = pcs_options[0]


def sync_scenario_one_from_dashboard(db: Dict[str, Any]) -> None:
    ensure_comparison_state(db)

    main = current_dashboard_selection(db)
    scenario = st.session_state["comparison_scenarios"][0]

    scenario["enabled"] = True
    scenario["c_rate"] = main["c_rate"]
    scenario["container"] = main["container"]
    scenario["pcs"] = main["pcs"]

    widget_values = {
        "cmp_enabled_0": True,
        "cmp_c_rate_0": main["c_rate"],
        "cmp_container_0": main["container"],
        "cmp_pcs_0": main["pcs"],
    }

    for key, value in widget_values.items():
        if key in st.session_state:
            st.session_state[key] = value


def reset_comparison_scenarios(db: Dict[str, Any]) -> None:
    st.session_state["comparison_scenarios"] = create_default_scenarios(db)
    clear_scenario_widget_keys()


def build_scenario_result(
    db: Dict[str, Any],
    scenario: Dict[str, Any],
    index: int,
) -> Dict[str, Any]:
    working_db = build_working_db(
        db=db,
        selected_c_rate=str(scenario["c_rate"]),
        selected_container_id=str(scenario["container"]),
        selected_pcs_id=str(scenario["pcs"]),
    )

    calc = calculate_dashboard(working_db, str(scenario["c_rate"]))

    return {
        "index": index,
        "name": scenario.get("name", SCENARIO_NAMES[index]),
        "accent": scenario.get("accent", SCENARIO_ACCENTS[index]),
        "scenario": scenario,
        "working_db": working_db,
        "calc": calc,
        "container_label": container_display_label(str(scenario["container"]), db),
        "pcs_label": pcs_display_label(str(scenario["pcs"]), db),
        "c_rate_label": c_rate_label(str(scenario["c_rate"])),
        "error": None,
    }


def collect_enabled_scenario_results(db: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    ensure_comparison_state(db)

    results: List[Dict[str, Any]] = []
    errors: List[str] = []

    for index, scenario in enumerate(st.session_state["comparison_scenarios"]):
        if not scenario.get("enabled", False):
            continue

        try:
            results.append(build_scenario_result(db, scenario, index))
        except Exception as exc:
            errors.append(f"Scenario {index + 1}: {exc}")

    return results, errors


def metric_value(result: Dict[str, Any], key: str) -> float:
    calc = result["calc"]

    mapping = {
        "energy": calc.get("container_mwh", 0),
        "power": calc.get("power_kw", 0),
        "current": calc.get("dc_bus_current_a", 0),
        "duration": calc.get("duration_h", 0),
        "containers": calc.get("containers_per_pcs", 0),
        "utilisation": calc.get("pcs_utilization", 0),
        "max_racks": calc.get("max_racks_per_pcs", 0),
    }

    return safe_float(mapping.get(key), 0.0)


def metric_display(result: Dict[str, Any], key: str) -> str:
    calc = result["calc"]

    if key == "energy":
        return f"{format_number(calc.get('container_mwh'), 2)} MWh"
    if key == "power":
        return f"{format_number(calc.get('power_kw'), 0)} kW"
    if key == "current":
        return f"{format_number(calc.get('dc_bus_current_a'), 1)} A"
    if key == "duration":
        return f"{format_number(calc.get('duration_h'), 1)} h"
    if key == "containers":
        return f"{safe_int(calc.get('containers_per_pcs'), 0)}"
    if key == "utilisation":
        return f"{format_number(calc.get('pcs_utilization'), 1)} %"
    if key == "max_racks":
        return f"{safe_int(calc.get('max_racks_per_pcs'), 0)}"

    return "-"


def best_result_for_metric(
    results: List[Dict[str, Any]],
    key: str,
) -> Optional[Dict[str, Any]]:
    if not results:
        return None

    if key in ["energy", "power", "duration", "containers", "max_racks"]:
        return max(results, key=lambda result: metric_value(result, key))

    if key == "current":
        return min(results, key=lambda result: metric_value(result, key))

    if key == "utilisation":
        feasible = [result for result in results if metric_value(result, key) <= 105]
        pool = feasible if feasible else results
        return min(pool, key=lambda result: abs(metric_value(result, key) - 85))

    return results[0]


def status_class(
    result: Dict[str, Any],
    key: str,
    best: Optional[Dict[str, Any]],
) -> str:
    value = metric_value(result, key)
    util = metric_value(result, "utilisation")

    if key == "power":
        if util > 105:
            return "status-high"
        if util >= 95:
            return "status-warn"
        return "status-good"

    if key == "current":
        if value >= 3000:
            return "status-high"
        if value >= 2400:
            return "status-warn"
        return "status-good"

    if key == "duration":
        if value < 2:
            return "status-high"
        if value < 3:
            return "status-warn"
        if best is result:
            return "status-good"
        return "status-neutral"

    if key == "utilisation":
        if value > 105:
            return "status-high"
        if value >= 95:
            return "status-warn"
        return "status-good"

    if key in ["energy", "containers", "max_racks"]:
        if best is result:
            return "status-good"
        return "status-neutral"

    return "status-neutral"


def render_comparison_table(results: List[Dict[str, Any]]) -> str:
    metrics = [
        ("energy", "Total Energy"),
        ("power", "Power @ C-rate"),
        ("current", "DC Bus Current"),
        ("duration", "Duration"),
        ("containers", "Containers / PCS"),
        ("utilisation", "PCS Utilisation"),
        ("max_racks", "Max Racks / PCS"),
    ]

    table_id = "scenario-comparison-table"

    header_cells = "".join(
        f"<th class='scenario-col scenario-accent-{escape(result['accent'])}'>"
        f"Scenario {result['index'] + 1}"
        f"</th>"
        for result in results
    )

    body_rows: List[str] = []

    for key, label in metrics:
        best = best_result_for_metric(results, key)

        scenario_cells = "".join(
            f"<td class='{status_class(result, key, best)}'>"
            f"{escape(metric_display(result, key))}"
            f"</td>"
            for result in results
        )

        row_html = (
            "<tr>"
            f"<td class='metric-name'>{escape(label)}</td>"
            f"{scenario_cells}"
            "</tr>"
        )
        body_rows.append(row_html)

    sld_buttons = "".join(
        (
            f"<td class='sld-button-cell scenario-accent-bg-{escape(result['accent'])}'>"
            f"<button type='button' class='sld-toggle-btn sld-toggle-{escape(result['accent'])}' "
            f"onclick=\"toggleScenarioSld('{table_id}', {position}, this)\">"
            f"📐 View SLD"
            f"</button>"
            f"</td>"
        )
        for position, result in enumerate(results)
    )

    sld_button_row = (
        "<tr class='sld-action-row'>"
        "<td class='metric-name sld-action-label'>Single Line Diagram</td>"
        f"{sld_buttons}"
        "</tr>"
    )

    sld_rows: List[str] = []
    colspan = len(results) + 1

    for position, result in enumerate(results):
        sld_html = render_sld_html(
            result["working_db"],
            str(result["scenario"]["c_rate"]),
        )

        sld_rows.append(
            f"<tr id='{table_id}-sld-{position}' class='sld-expanded-row' style='display:none;'>"
            f"<td colspan='{colspan}'>"
            f"<div class='embedded-sld-heading scenario-accent-border-{escape(result['accent'])}'>"
            f"<div>"
            f"<b>Scenario {result['index'] + 1} SLD</b>"
            f"<span>{escape(result['c_rate_label'])} · {escape(result['container_label'])} · {escape(result['pcs_label'])}</span>"
            f"</div>"
            f"<button type='button' class='sld-close-btn' onclick=\"closeScenarioSld('{table_id}')\">✕ Close</button>"
            f"</div>"
            f"<div class='embedded-sld-container'>"
            f"{sld_html}"
            f"</div>"
            f"</td>"
            f"</tr>"
        )

    rows_html = "".join(body_rows) + sld_button_row + "".join(sld_rows)

    return f"""
<div id="{table_id}" class="comparison-panel comparison-panel-with-sld">
  <style>
    .comparison-panel-with-sld .sld-action-row td {{
      background: rgba(0,217,255,.030);
      border-top: 1px solid rgba(0,217,255,.30);
    }}

    .comparison-panel-with-sld .sld-action-label {{
      color: #8fe6ff;
      font-weight: 950;
      text-transform: uppercase;
      letter-spacing: .3px;
    }}

    .comparison-panel-with-sld .sld-button-cell {{
      padding: 9px 10px !important;
      text-align: center;
      background:
        radial-gradient(circle at top, rgba(0,217,255,.045), rgba(7,17,31,.22)) !important;
    }}

    .comparison-panel-with-sld .sld-toggle-btn {{
      width: 100%;
      min-height: 38px;
      border-radius: 9px;
      border: 1.35px solid rgba(0,217,255,.92);
      background:
        linear-gradient(180deg, rgba(18,31,80,.98) 0%, rgba(19,6,62,.98) 58%, rgba(7,17,31,.98) 100%);
      color: #ffffff;
      font-size: 12px;
      font-weight: 950;
      letter-spacing: .15px;
      cursor: pointer;
      box-shadow:
        0 0 16px rgba(0,217,255,.32),
        inset 0 0 15px rgba(0,217,255,.10),
        inset 0 -10px 18px rgba(0,0,0,.22);
      transition:
        transform .14s ease,
        box-shadow .14s ease,
        border-color .14s ease,
        background .14s ease,
        filter .14s ease;
    }}

    .comparison-panel-with-sld .sld-toggle-btn:hover {{
      transform: translateY(-1px);
      border-color: #5ef2ff;
      background:
        linear-gradient(180deg, rgba(25,44,112,.98) 0%, rgba(28,8,82,.98) 56%, rgba(8,22,44,.98) 100%);
      box-shadow:
        0 0 24px rgba(0,217,255,.46),
        inset 0 0 18px rgba(0,217,255,.15),
        inset 0 -10px 18px rgba(0,0,0,.18);
      filter: saturate(1.08);
    }}

    .comparison-panel-with-sld .sld-toggle-btn:active {{
      transform: translateY(0);
      box-shadow:
        0 0 12px rgba(0,217,255,.26),
        inset 0 0 14px rgba(0,0,0,.32);
    }}

    .comparison-panel-with-sld .sld-toggle-btn.active {{
      background:
        linear-gradient(180deg, rgba(44,18,88,.98) 0%, rgba(36,9,72,.98) 45%, rgba(21,10,44,.98) 100%);
      border-color: rgba(255,153,0,.95);
      color: #ffffff;
      box-shadow:
        0 0 18px rgba(255,153,0,.28),
        0 0 28px rgba(0,217,255,.22),
        inset 0 0 16px rgba(255,153,0,.12);
    }}

    .comparison-panel-with-sld .sld-toggle-cyan.active {{
      border-color: rgba(0,217,255,.98);
      box-shadow:
        0 0 22px rgba(0,217,255,.40),
        inset 0 0 16px rgba(0,217,255,.14);
    }}

    .comparison-panel-with-sld .sld-toggle-yellow.active {{
      border-color: rgba(240,185,0,.98);
      box-shadow:
        0 0 22px rgba(240,185,0,.36),
        inset 0 0 16px rgba(240,185,0,.14);
    }}

    .comparison-panel-with-sld .sld-toggle-pink.active {{
      border-color: rgba(255,81,124,.98);
      box-shadow:
        0 0 22px rgba(255,81,124,.36),
        inset 0 0 16px rgba(255,81,124,.14);
    }}

    .comparison-panel-with-sld .sld-toggle-green.active {{
      border-color: rgba(96,255,155,.98);
      box-shadow:
        0 0 22px rgba(96,255,155,.34),
        inset 0 0 16px rgba(96,255,155,.14);
    }}

    .comparison-panel-with-sld .sld-expanded-row td {{
      padding: 0 !important;
      background: rgba(7,17,31,.98);
      border-top: 1.5px solid rgba(0,217,255,.52);
    }}

    .comparison-panel-with-sld .embedded-sld-heading {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      background:
        linear-gradient(90deg, rgba(0,217,255,.10), rgba(255,153,0,.04));
      border-bottom: 1px solid rgba(255,255,255,.12);
    }}

    .comparison-panel-with-sld .embedded-sld-heading b {{
      display: block;
      color: #ffffff;
      font-size: 15px;
      font-weight: 950;
      margin-bottom: 3px;
    }}

    .comparison-panel-with-sld .embedded-sld-heading span {{
      color: #a9dfff;
      font-size: 11px;
    }}

    .comparison-panel-with-sld .sld-close-btn {{
      border: 1px solid rgba(255,81,124,.75);
      border-radius: 8px;
      background: rgba(255,81,124,.16);
      color: #ffffff;
      font-size: 12px;
      font-weight: 900;
      padding: 7px 10px;
      cursor: pointer;
    }}

    .comparison-panel-with-sld .sld-close-btn:hover {{
      background: rgba(255,81,124,.28);
      box-shadow: 0 0 12px rgba(255,81,124,.22);
    }}

    .comparison-panel-with-sld .embedded-sld-container {{
      max-height: 780px;
      overflow: auto;
      padding: 14px;
      background: #07111f;
    }}

    .comparison-panel-with-sld .embedded-sld-container::-webkit-scrollbar {{
      width: 8px;
      height: 8px;
    }}

    .comparison-panel-with-sld .embedded-sld-container::-webkit-scrollbar-track {{
      background: rgba(255,255,255,.04);
      border-radius: 999px;
    }}

    .comparison-panel-with-sld .embedded-sld-container::-webkit-scrollbar-thumb {{
      background: rgba(0,217,255,.38);
      border-radius: 999px;
    }}
  </style>

  <div class="comparison-panel-head">
    <div>
      <h2>Scenario Comparison</h2>
      <p>Conditional formatting: green = good or best, yellow = acceptable/watch, red = high or overload.</p>
    </div>
    <div class="performance-guide">
      <span><i class="dot good"></i>Good</span>
      <span><i class="dot warn"></i>Acceptable</span>
      <span><i class="dot high"></i>High / Overload</span>
    </div>
  </div>

  <div class="comparison-table-wrap">
    <table class="comparison-table">
      <thead>
        <tr>
          <th>Metric</th>
          {header_cells}
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>

  <p class="comparison-note">
    Values are calculated from the selected C-rate, container, and PCS for each enabled scenario.
    Use the SLD row to open one scenario diagram inside this table.
  </p>

  <script>
    function closeScenarioSld(rootId) {{
      const root = document.getElementById(rootId);
      if (!root) return;

      const rows = root.querySelectorAll('.sld-expanded-row');
      const buttons = root.querySelectorAll('.sld-toggle-btn');

      rows.forEach(function(row) {{
        row.style.display = 'none';
      }});

      buttons.forEach(function(button) {{
        button.classList.remove('active');
        button.innerText = '📐 View SLD';
      }});
    }}

    function toggleScenarioSld(rootId, index, button) {{
      const root = document.getElementById(rootId);
      if (!root) return;

      const target = document.getElementById(rootId + '-sld-' + index);
      if (!target) return;

      const alreadyOpen = target.style.display !== 'none';

      closeScenarioSld(rootId);

      if (!alreadyOpen) {{
        target.style.display = 'table-row';
        button.classList.add('active');
        button.innerText = '▴ Hide SLD';

        setTimeout(function() {{
          target.scrollIntoView({{
            behavior: 'smooth',
            block: 'nearest'
          }});
        }}, 80);
      }}
    }}
  </script>
</div>
"""


# ---------------------------------------------------------------------
# Table editor helpers
# ---------------------------------------------------------------------

def flatten_item(item_id: str, item: Dict[str, Any]) -> Dict[str, Any]:
    row = {"id": item_id}

    for key, value in item.items():
        row[key] = json.dumps(value) if isinstance(value, (dict, list)) else value

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
            selected_pcs_id=selection["pcs"],
        )

        calc = calculate_dashboard(working_db, selection["c_rate"])

        cards_html = render_cards_html(working_db, selection["c_rate"])
        render_html_block(cards_html, height=CARDS_IFRAME_HEIGHT, scrolling=False)

        output_html = f"""
<div class="output-strip">
  <div class="output-label">OUTPUT</div>
  <div class="output-item"><span>Container Energy</span><b>{format_number(calc.get('container_mwh'), 2)} MWh</b></div>
  <div class="output-item"><span>Power @ C-rate</span><b>{format_number(calc.get('power_kw'), 0)} kW</b></div>
  <div class="output-item"><span>DC Bus Current</span><b>{format_number(calc.get('dc_bus_current_a'), 1)} A</b></div>
  <div class="output-item"><span>Containers / PCS</span><b>{calc.get('containers_per_pcs')}</b></div>
  <div class="output-item"><span>Duration</span><b>{format_number(calc.get('duration_h'), 1)} h</b></div>
</div>
"""
        st.markdown(output_html, unsafe_allow_html=True)

        with st.expander("Expand Single Line Diagram", expanded=False):
            sld_html = render_sld_html(working_db, selection["c_rate"])
            render_html_block(sld_html, height=DASHBOARD_IFRAME_HEIGHT, scrolling=True)

        if st.button("Save current selection as default"):
            db.setdefault("project", {})
            db.setdefault("selected_components", {})

            db["project"]["default_c_rate"] = selection["c_rate"]
            db["selected_components"]["container"] = selection["container"]
            db["selected_components"]["pcs"] = selection["pcs"]

            save_db(db)
            st.success("Default selection saved to data/db.json.")

    except Exception as exc:
        render_exception_box(
            "Dashboard rendering failed. Check selected container, PCS, and db.json field values.",
            exc,
        )


def scenario_analysis_page(db: Dict[str, Any]) -> None:
    validation_errors = validate_minimum_db(db)

    if validation_errors:
        st.error("The JSON database is incomplete. Fix data/db.json before rendering scenario analysis.")
        for item in validation_errors:
            st.warning(item)
        return

    ensure_selection_state(db)
    ensure_comparison_state(db)
    render_bess_header(db)

    c_rate_options = get_c_rate_options(db)
    container_options = get_container_options(db)
    pcs_options = get_pcs_options(db)

    top1, top2, top3, top4 = st.columns([1.7, 1.0, 1.0, 1.25], gap="medium")

    with top1:
        st.markdown(
            """
<div class="scenario-page-title">
  <h2>Scenario Analysis</h2>
  <p>Compare up to four BESS system configurations side by side.</p>
</div>
""",
            unsafe_allow_html=True,
        )

    with top2:
        if st.button("🏠 Dashboard", use_container_width=True, type="primary"):
            request_navigation("Dashboard")

    with top3:
        if st.button("↺ Reset Scenarios", use_container_width=True, type="primary"):
            reset_comparison_scenarios(db)
            st.rerun()

    with top4:
        export_button_slot = st.empty()

    with st.container(border=True):
        st.markdown(
            """
<div class="scenario-builder-head">
  <span>Scenario Builder</span>
  <small>Enable up to 4 scenarios. Scenario 1 is your dashboard baseline by default.</small>
</div>
""",
            unsafe_allow_html=True,
        )

        scenario_cols = st.columns(4, gap="medium")

        for index, col in enumerate(scenario_cols):
            scenario = st.session_state["comparison_scenarios"][index]
            accent = scenario.get("accent", SCENARIO_ACCENTS[index])

            with col:
                with st.container(border=True):
                    st.markdown(
                        f"""
<div class="scenario-card-heading scenario-heading-{escape(accent)}">
  <b>{escape(scenario.get('name', SCENARIO_NAMES[index]))}</b>
  <span>{escape('Baseline' if index == 0 else c_rate_label(str(scenario.get('c_rate', ''))))}</span>
</div>
""",
                        unsafe_allow_html=True,
                    )

                    enabled = st.toggle(
                        "Enabled",
                        value=bool(scenario.get("enabled", True)),
                        key=f"cmp_enabled_{index}",
                    )

                    c_rate = st.selectbox(
                        "C-rate",
                        c_rate_options,
                        index=default_index(c_rate_options, scenario.get("c_rate")),
                        key=f"cmp_c_rate_{index}",
                    )

                    container = st.selectbox(
                        "Container",
                        container_options,
                        index=default_index(container_options, scenario.get("container")),
                        format_func=lambda key: container_display_label(key, db),
                        key=f"cmp_container_{index}",
                    )

                    pcs = st.selectbox(
                        "PCS",
                        pcs_options,
                        index=default_index(pcs_options, scenario.get("pcs")),
                        format_func=lambda key: pcs_display_label(key, db),
                        key=f"cmp_pcs_{index}",
                    )

                    scenario["enabled"] = enabled
                    scenario["c_rate"] = c_rate
                    scenario["container"] = container
                    scenario["pcs"] = pcs

    results, errors = collect_enabled_scenario_results(db)

    for message in errors:
        st.warning(message)

    if not results:
        with export_button_slot:
            st.button(
                "📄 Export PDF",
                use_container_width=True,
                type="primary",
                disabled=True,
            )

        st.info("Enable at least one scenario to view comparison outputs and export a PDF.")
        return

    pdf_export_error = None

    if build_scenario_pdf_bytes is None:
        with export_button_slot:
            st.button(
                "📄 Export PDF",
                use_container_width=True,
                type="primary",
                disabled=True,
            )

        st.warning(
            "PDF export is unavailable because the reporting module could not be imported. "
            "Confirm `reportlab` is in requirements.txt and `src/reporting/pdf_report.py` exists."
        )

        if REPORT_IMPORT_ERROR is not None:
            with st.expander("PDF export technical details"):
                st.code(str(REPORT_IMPORT_ERROR))
    else:
        try:
            pdf_bytes = build_scenario_pdf_bytes(
                project_name=db.get("project", {}).get("name", "BESS Dashboard"),
                results=results,
            )

            file_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            with export_button_slot:
                st.download_button(
                    label="📄 Export PDF",
                    data=pdf_bytes,
                    file_name=f"bess_scenario_analysis_{file_stamp}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                    key="export_scenario_analysis_pdf_top",
                )
        except Exception as exc:
            pdf_export_error = exc

            with export_button_slot:
                st.button(
                    "📄 Export PDF",
                    use_container_width=True,
                    type="primary",
                    disabled=True,
                )

    comparison_html = render_comparison_table(results)
    render_component_html(
        comparison_html,
        height=COMPARISON_TABLE_HEIGHT,
        scrolling=True,
    )

    if pdf_export_error is not None:
        render_exception_box("Could not prepare Scenario Analysis PDF export.", pdf_export_error)


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
                "numeric_c_rate": parse_c_rate(key),
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
                        "containers_per_pcs": 1,
                    },
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
        type=["xlsx", "xlsm", "xls"],
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

For a production multi-user version, store the JSON database in GitHub, S3, Azure Blob, Google Cloud Storage, Supabase, PostgreSQL, or Google Sheets.
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
            selected_pcs_id=selected_pcs,
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

    pages = [
        "Dashboard",
        "Scenario Analysis",
        "Component Library",
        "C-rate Profiles",
        "Excel Import",
        "JSON Database",
        "Calculation Debug",
        "Export / Share",
    ]

    if "nav_page" not in st.session_state or st.session_state["nav_page"] not in pages:
        st.session_state["nav_page"] = "Dashboard"

    pending_page = st.session_state.pop("pending_nav_page", None)

    if pending_page in pages:
        st.session_state["nav_page"] = pending_page

    st.sidebar.title("BESS Dashboard")

    page = st.sidebar.radio(
        "Navigation",
        pages,
        key="nav_page",
    )

    try:
        if page == "Dashboard":
            dashboard_page(db)
        elif page == "Scenario Analysis":
            scenario_analysis_page(db)
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
