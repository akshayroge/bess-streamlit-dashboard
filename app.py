import json
import traceback
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.assets import load_css
from src.calculations import calculate_dashboard
from src.excel_importer import detect_excel_values
from src.store import load_db, save_db
from src.ui import render_dashboard_html


DASHBOARD_IFRAME_HEIGHT = 2400


def inject_css() -> None:
    """
    Inject CSS into the main Streamlit page.

    This styles Streamlit's body/background/sidebar area.
    The dashboard HTML also receives CSS separately inside render_dashboard_raw_html().
    """
    css = load_css()

    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def build_inline_dashboard_html(dashboard_html: str) -> str:
    """
    Build raw dashboard HTML for st.html().

    st.html() avoids Markdown parsing. Markdown parsing was the reason raw
    dashboard HTML was appearing on the page.
    """
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
    """
    Build full HTML document for components.html() fallback.

    This fallback is used only if the deployed Streamlit version does not
    support st.html().
    """
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
    """
    Render dashboard HTML safely.

    Do not use st.markdown() for the full dashboard HTML.
    It can treat indented HTML as Markdown code blocks.
    """
    html_renderer = getattr(st, "html", None)

    if html_renderer is not None:
        html_renderer(build_inline_dashboard_html(dashboard_html))
    else:
        components.html(
            build_iframe_dashboard_document(dashboard_html),
            height=DASHBOARD_IFRAME_HEIGHT,
            scrolling=True,
        )


def render_exception_box(title: str, exc: Exception) -> None:
    """
    Show controlled error details instead of leaking broken HTML or traceback
    directly into the dashboard UI.
    """
    st.error(title)
    st.caption(str(exc))

    with st.expander("Technical details"):
        st.code(traceback.format_exc(), language="python")


def get_nested(db: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    """
    Safely read nested dictionary paths.
    """
    current: Any = db

    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]

    return current


def validate_db(db: Dict[str, Any]) -> List[str]:
    """
    Validate the minimum JSON structure required to render the dashboard.
    """
    errors: List[str] = []

    required_paths = [
        ["project"],
        ["selected_components"],
        ["catalog"],
        ["catalog", "cells"],
        ["catalog", "packs"],
        ["catalog", "racks"],
        ["catalog", "containers"],
        ["catalog", "pcs"],
        ["profiles"],
        ["profiles", "c_rate_profiles"],
    ]

    for path in required_paths:
        if get_nested(db, path) is None:
            errors.append("Missing required JSON section: " + " -> ".join(path))

    selected = db.get("selected_components", {})
    catalog = db.get("catalog", {})

    component_map = {
        "cell": "cells",
        "pack": "packs",
        "rack": "racks",
        "container": "containers",
        "pcs": "pcs",
    }

    for selected_key, catalog_key in component_map.items():
        component_id = selected.get(selected_key)

        if not component_id:
            errors.append(f"Missing selected component: {selected_key}")
            continue

        if component_id not in catalog.get(catalog_key, {}):
            errors.append(
                f"Selected component '{selected_key}' with id '{component_id}' "
                f"was not found in catalog.{catalog_key}."
            )

    profiles = get_nested(db, ["profiles", "c_rate_profiles"], {}) or {}

    if not profiles:
        errors.append("No C-rate profiles found in profiles.c_rate_profiles.")

    return errors


def flatten_item(item_id: str, item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a JSON catalog item into a flat table row for st.data_editor().
    """
    row = {"id": item_id}

    for key, value in item.items():
        if isinstance(value, (dict, list)):
            row[key] = json.dumps(value)
        else:
            row[key] = value

    return row


def is_missing(value: Any) -> bool:
    """
    Robust missing-value check for table editor data.
    """
    try:
        result = pd.isna(value)

        if isinstance(result, (list, tuple)):
            return False

        if hasattr(result, "any"):
            return bool(result.any())

        return bool(result)
    except Exception:
        return value is None


def convert_editor_value(value: Any) -> Any:
    """
    Convert table editor values back into JSON-compatible values.
    """
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
    """
    Convert edited table rows back into catalog JSON.
    """
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


def dashboard_page(db: Dict[str, Any]) -> None:
    """
    Main dashboard page.
    """
    validation_errors = validate_db(db)

    if validation_errors:
        st.error("The JSON database is incomplete. Fix data/db.json before rendering the dashboard.")
        for item in validation_errors:
            st.warning(item)
        return

    profile_keys = list(db["profiles"]["c_rate_profiles"].keys())

    default_c_rate = db.get("project", {}).get("default_c_rate", profile_keys[0])
    default_index = profile_keys.index(default_c_rate) if default_c_rate in profile_keys else 0

    selected_c_rate = st.sidebar.selectbox(
        "C-rate",
        profile_keys,
        index=default_index,
        help="Values come from data/db.json -> profiles -> c_rate_profiles.",
    )

    try:
        dashboard_html = render_dashboard_html(db, selected_c_rate)
        render_dashboard_raw_html(dashboard_html)
    except Exception as exc:
        render_exception_box(
            "Dashboard rendering failed. Check data/db.json, src/ui.py, CSS, and image paths.",
            exc,
        )


def component_library_page(db: Dict[str, Any]) -> None:
    """
    Editable component library page.
    """
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
    """
    Editable C-rate profile page.
    """
    st.title("C-rate Profiles")
    st.caption("Edit C-rate dependent values such as power, current, and containers per PCS.")

    profiles = get_nested(db, ["profiles", "c_rate_profiles"], {}) or {}

    if not profiles:
        st.error("No C-rate profiles found in data/db.json.")
        return

    rows = []

    for key, profile in profiles.items():
        row = {"id": key}
        row.update(profile)
        rows.append(row)

    df = pd.DataFrame(rows)

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
    )

    if st.button("Save C-rate profiles", type="primary"):
        try:
            new_profiles: Dict[str, Any] = {}

            for _, row in edited_df.iterrows():
                profile_id = str(row.get("id", "")).strip()

                if not profile_id:
                    continue

                new_profiles[profile_id] = {
                    "label": str(row.get("label", profile_id)),
                    "c_rate": float(row.get("c_rate", 0)),
                    "power_kw": float(row.get("power_kw", 0)),
                    "dc_bus_current_a": float(row.get("dc_bus_current_a", 0)),
                    "containers_per_pcs": int(row.get("containers_per_pcs", 1)),
                }

            if not new_profiles:
                st.error("No valid C-rate profiles were found in the edited table.")
                return

            db["profiles"]["c_rate_profiles"] = new_profiles
            save_db(db)
            st.success("C-rate profiles saved to data/db.json.")
        except Exception as exc:
            render_exception_box("Could not save C-rate profiles.", exc)


def excel_import_page(db: Dict[str, Any]) -> None:
    """
    Excel import page.
    """
    st.title("Excel Import")
    st.caption("Upload the Excel sizing workbook and map detected values into the JSON database.")

    uploaded_file = st.file_uploader(
        "Upload Excel workbook",
        type=["xlsx", "xlsm", "xls"],
    )

    if uploaded_file is None:
        st.info("Upload your sizing workbook to detect current, energy, power, and containers per PCS.")
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
        st.warning("No values were automatically detected. You can still enter values manually below.")

    profiles = get_nested(db, ["profiles", "c_rate_profiles"], {}) or {}

    if not profiles:
        st.error("No C-rate profiles found in data/db.json.")
        return

    profile_key = st.selectbox("Apply values to C-rate profile", list(profiles.keys()))
    current_profile = profiles[profile_key]

    power_kw = st.number_input(
        "Power kW",
        value=float(
            detected.get("power_kw", {}).get(
                "value",
                current_profile.get("power_kw", 0),
            )
        ),
    )

    dc_bus_current_a = st.number_input(
        "DC Bus Current A",
        value=float(
            detected.get("dc_bus_current_a", {}).get(
                "value",
                current_profile.get("dc_bus_current_a", 0),
            )
        ),
    )

    containers_per_pcs = st.number_input(
        "Containers per PCS",
        value=int(
            detected.get("containers_per_pcs", {}).get(
                "value",
                current_profile.get("containers_per_pcs", 1),
            )
        ),
        min_value=1,
        step=1,
    )

    if st.button("Save imported values", type="primary"):
        try:
            db["profiles"]["c_rate_profiles"][profile_key]["power_kw"] = float(power_kw)
            db["profiles"]["c_rate_profiles"][profile_key]["dc_bus_current_a"] = float(dc_bus_current_a)
            db["profiles"]["c_rate_profiles"][profile_key]["containers_per_pcs"] = int(containers_per_pcs)

            if "total_energy_kwh" in detected:
                selected_container = db["selected_components"]["container"]
                db["catalog"]["containers"][selected_container]["energy_kwh"] = float(
                    detected["total_energy_kwh"]["value"]
                )

            save_db(db)
            st.success("Imported values saved to data/db.json.")
        except Exception as exc:
            render_exception_box("Could not save imported Excel values.", exc)


def json_database_page(db: Dict[str, Any]) -> None:
    """
    Raw JSON database editor.
    """
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
                errors = validate_db(new_db)

                if errors:
                    st.warning("JSON syntax is valid, but required dashboard fields are missing.")
                    for item in errors:
                        st.warning(item)
                else:
                    st.success("JSON is valid and required dashboard fields are present.")
            except Exception as exc:
                st.error(f"Invalid JSON: {exc}")

    with col2:
        if st.button("Save JSON", type="primary"):
            try:
                new_db = json.loads(json_text)
                errors = validate_db(new_db)

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
    """
    Export/share page.
    """
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
    """
    Calculation debug page.
    """
    st.title("Calculation Debug")
    st.caption("Inspect calculated output for each C-rate profile.")

    profiles = get_nested(db, ["profiles", "c_rate_profiles"], {}) or {}

    if not profiles:
        st.error("No C-rate profiles found.")
        return

    profile_key = st.selectbox(
        "C-rate",
        list(profiles.keys()),
    )

    try:
        result = calculate_dashboard(db, profile_key)
        st.json(result)
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
