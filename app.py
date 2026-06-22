import json
from typing import Any, Dict

import pandas as pd
import streamlit as st

from src.assets import load_css
from src.calculations import calculate_dashboard
from src.excel_importer import detect_excel_values
from src.store import load_db, save_db
from src.ui import render_dashboard_html


def inject_css() -> None:
    css = load_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def flatten_item(item_id: str, item: Dict[str, Any]) -> Dict[str, Any]:
    row = {"id": item_id}
    for key, value in item.items():
        row[key] = json.dumps(value) if isinstance(value, (dict, list)) else value
    return row


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
            if pd.isna(value):
                continue

            if isinstance(value, str):
                text = value.strip()
                if text.startswith("{") or text.startswith("["):
                    try:
                        item[col] = json.loads(text)
                        continue
                    except Exception:
                        pass
                item[col] = text
            else:
                try:
                    item[col] = value.item()
                except Exception:
                    item[col] = value

        result[item_id] = item

    return result


def dashboard_page(db: Dict[str, Any]) -> None:
    profile_keys = list(db["profiles"]["c_rate_profiles"].keys())

    if not profile_keys:
        st.error("No C-rate profiles found in data/db.json.")
        return

    default_c_rate = db["project"].get("default_c_rate", profile_keys[0])
    default_index = profile_keys.index(default_c_rate) if default_c_rate in profile_keys else 0

    selected_c_rate = st.sidebar.selectbox(
        "C-rate",
        profile_keys,
        index=default_index,
        help="Values come from data/db.json -> profiles -> c_rate_profiles."
    )

    st.markdown(
        render_dashboard_html(db, selected_c_rate),
        unsafe_allow_html=True
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
        hide_index=True
    )

    if st.button("Save library", type="primary"):
        db["catalog"][library_name] = unflatten_table(edited_df)
        save_db(db)
        st.success("Library saved to data/db.json.")


def c_rate_profiles_page(db: Dict[str, Any]) -> None:
    st.title("C-rate Profiles")
    st.caption("Edit C-rate dependent values such as power, current, and containers per PCS.")

    profiles = db["profiles"]["c_rate_profiles"]
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
        hide_index=True
    )

    if st.button("Save C-rate profiles", type="primary"):
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
                "containers_per_pcs": int(row.get("containers_per_pcs", 1))
            }

        db["profiles"]["c_rate_profiles"] = new_profiles
        save_db(db)
        st.success("C-rate profiles saved to data/db.json.")


def excel_import_page(db: Dict[str, Any]) -> None:
    st.title("Excel Import")
    st.caption("Upload the Excel sizing workbook and map detected values into the JSON database.")

    uploaded_file = st.file_uploader(
        "Upload Excel workbook",
        type=["xlsx", "xlsm", "xls"]
    )

    if uploaded_file is None:
        st.info("Upload your sizing workbook to detect current, energy, power, and containers per PCS.")
        return

    detected = detect_excel_values(uploaded_file)

    st.subheader("Detected values")
    if detected:
        st.json(detected)
    else:
        st.warning("No values were automatically detected. You can still enter values manually below.")

    profiles = db["profiles"]["c_rate_profiles"]

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
                current_profile.get("power_kw", 0)
            )
        )
    )

    dc_bus_current_a = st.number_input(
        "DC Bus Current A",
        value=float(
            detected.get("dc_bus_current_a", {}).get(
                "value",
                current_profile.get("dc_bus_current_a", 0)
            )
        )
    )

    containers_per_pcs = st.number_input(
        "Containers per PCS",
        value=int(
            detected.get("containers_per_pcs", {}).get(
                "value",
                current_profile.get("containers_per_pcs", 1)
            )
        ),
        min_value=1,
        step=1
    )

    if st.button("Save imported values", type="primary"):
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


def json_database_page(db: Dict[str, Any]) -> None:
    st.title("JSON Database")
    st.caption("View, edit, validate, and download the complete JSON database.")

    json_text = st.text_area(
        "data/db.json",
        value=json.dumps(db, indent=2),
        height=650
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Validate JSON"):
            try:
                json.loads(json_text)
                st.success("JSON is valid.")
            except Exception as exc:
                st.error(f"Invalid JSON: {exc}")

    with col2:
        if st.button("Save JSON", type="primary"):
            try:
                new_db = json.loads(json_text)
                save_db(new_db)
                st.success("JSON saved to data/db.json.")
            except Exception as exc:
                st.error(f"Could not save JSON: {exc}")

    with col3:
        st.download_button(
            "Download db.json",
            data=json.dumps(db, indent=2),
            file_name="db.json",
            mime="application/json"
        )


def export_page(db: Dict[str, Any]) -> None:
    st.title("Export / Share")
    st.caption("Download JSON backup and review deployment information.")

    st.download_button(
        "Download full JSON database",
        data=json.dumps(db, indent=2),
        file_name="bess_dashboard_db.json",
        mime="application/json"
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
    st.caption("Inspect calculated output for each C-rate profile.")

    profiles = db["profiles"]["c_rate_profiles"]

    if not profiles:
        st.error("No C-rate profiles found.")
        return

    profile_key = st.selectbox(
        "C-rate",
        list(profiles.keys())
    )

    result = calculate_dashboard(db, profile_key)
    st.json(result)


def main() -> None:
    st.set_page_config(
        page_title="BESS Streamlit Dashboard",
        page_icon="🔋",
        layout="wide"
    )

    inject_css()

    try:
        db = load_db()
    except Exception as exc:
        st.error(f"Could not load data/db.json: {exc}")
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
            "Export / Share"
        ]
    )

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


if __name__ == "__main__":
    main()