from typing import Any, Dict, List

import pandas as pd


def find_label_value(df: pd.DataFrame, labels: List[str]) -> Any:
    labels_lower = [label.lower() for label in labels]

    for row_index in range(df.shape[0]):
        for col_index in range(df.shape[1]):
            value = df.iat[row_index, col_index]

            if not isinstance(value, str):
                continue

            text = value.lower().strip()

            if not any(label in text for label in labels_lower):
                continue

            for next_col in range(col_index + 1, min(col_index + 8, df.shape[1])):
                candidate = df.iat[row_index, next_col]

                if pd.notna(candidate) and isinstance(candidate, (int, float)):
                    return candidate

    return None


def detect_excel_values(uploaded_file) -> Dict[str, Any]:
    xls = pd.ExcelFile(uploaded_file)

    label_map = {
        "dc_bus_current_a": [
            "total dc current",
            "system current",
            "i_max",
            "imax",
            "current"
        ],
        "containers_per_pcs": [
            "no. of containers per pcs",
            "containers per pcs",
            "container per pcs"
        ],
        "total_energy_kwh": [
            "total energy",
            "container energy"
        ],
        "power_kw": [
            "power @ c-rate",
            "power at c-rate",
            "power kw"
        ]
    }

    detected: Dict[str, Any] = {}

    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)
        except Exception:
            continue

        for key, labels in label_map.items():
            if key in detected:
                continue

            value = find_label_value(df, labels)

            if value is not None:
                detected[key] = {
                    "sheet": sheet_name,
                    "value": float(value)
                }

    return detected