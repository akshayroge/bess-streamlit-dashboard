"""
Bootstrap or update the BESS Streamlit dashboard JSON database from an Excel sizing workbook.

Place this file here:

    scripts/bootstrap_from_excel.py

Run from the repo root like this:

    python scripts/bootstrap_from_excel.py "Key_Battery_Players_25.05.26 1(4).xlsx" --profile 0.25C

Dry run without saving:

    python scripts/bootstrap_from_excel.py "Key_Battery_Players_25.05.26 1(4).xlsx" --profile 0.25C --dry-run

This script scans the Excel workbook for key sizing labels and updates data/db.json.
It is conservative: it only updates values it detects and keeps all other database fields unchanged.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "db.json"


LABEL_MAP: Dict[str, List[str]] = {
    "dc_bus_current_a": [
        "total dc current",
        "system current",
        "i_max",
        "imax",
        "dc current",
        "current"
    ],
    "containers_per_pcs": [
        "no. of containers per pcs",
        "no of containers per pcs",
        "number of containers per pcs",
        "containers per pcs",
        "container per pcs"
    ],
    "total_energy_kwh": [
        "total energy",
        "container energy",
        "energy kwh"
    ],
    "power_kw": [
        "power @ c-rate",
        "power at c-rate",
        "power kw",
        "rated power"
    ]
}


PROFILE_ALIASES = {
    "0.25": "0.25C",
    "0.25c": "0.25C",
    "0.5": "0.5C",
    "0.50": "0.5C",
    "0.5c": "0.5C",
    "1": "1C",
    "1.0": "1C",
    "1c": "1C"
}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("\n", " ")
        .replace("\r", " ")
    )


def is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False

    return isinstance(value, (int, float)) and pd.notna(value)


def find_numeric_near_label(
    df: pd.DataFrame,
    labels: Iterable[str],
    max_right_scan: int = 10,
    max_down_scan: int = 4
) -> Optional[Tuple[float, int, int, str]]:
    """
    Finds the first numeric value near a matching label.

    Search method:
    1. Find a cell containing one of the target labels.
    2. Look to the right in the same row.
    3. If not found, look below the label cell.

    Returns:
        value, row_index, column_index, matched_label
    """

    labels_norm = [label.lower() for label in labels]

    for row_idx in range(df.shape[0]):
        for col_idx in range(df.shape[1]):
            cell_text = normalize_text(df.iat[row_idx, col_idx])

            if not cell_text:
                continue

            if not any(label in cell_text for label in labels_norm):
                continue

            right_limit = min(col_idx + max_right_scan + 1, df.shape[1])

            for next_col in range(col_idx + 1, right_limit):
                candidate = df.iat[row_idx, next_col]

                if is_number(candidate):
                    return float(candidate), row_idx, next_col, cell_text

            down_limit = min(row_idx + max_down_scan + 1, df.shape[0])

            for next_row in range(row_idx + 1, down_limit):
                candidate = df.iat[next_row, col_idx]

                if is_number(candidate):
                    return float(candidate), next_row, col_idx, cell_text

    return None


def detect_values_from_excel(excel_path: Path) -> Dict[str, Dict[str, Any]]:
    xls = pd.ExcelFile(excel_path)
    detected: Dict[str, Dict[str, Any]] = {}

    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
        except Exception as exc:
            print(f"Skipping sheet {sheet_name!r}: {exc}")
            continue

        for key, labels in LABEL_MAP.items():
            if key in detected:
                continue

            found = find_numeric_near_label(df, labels)

            if not found:
                continue

            value, row_idx, col_idx, matched_label = found

            detected[key] = {
                "value": value,
                "sheet": sheet_name,
                "row": row_idx + 1,
                "column": col_idx + 1,
                "matched_label": matched_label
            }

    return detected


def load_db(db_path: Path) -> Dict[str, Any]:
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    return json.loads(db_path.read_text(encoding="utf-8"))


def save_db(db: Dict[str, Any], db_path: Path, create_backup: bool = True) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if create_backup and db_path.exists():
        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"db_backup_{stamp}.json"

        shutil.copy2(db_path, backup_path)
        print(f"Backup created: {backup_path}")

    db_path.write_text(json.dumps(db, indent=2), encoding="utf-8")
    print(f"Updated database: {db_path}")


def normalize_profile_key(profile: str, db: Dict[str, Any]) -> str:
    profiles = db.get("profiles", {}).get("c_rate_profiles", {})

    if profile in profiles:
        return profile

    alias = PROFILE_ALIASES.get(profile.strip().lower())

    if alias and alias in profiles:
        return alias

    available = ", ".join(profiles.keys())

    raise KeyError(
        f"Profile {profile!r} not found. Available profiles: {available}"
    )


def apply_detected_values(
    db: Dict[str, Any],
    detected: Dict[str, Dict[str, Any]],
    profile_key: str
) -> Dict[str, Any]:
    profile_key = normalize_profile_key(profile_key, db)
    profile = db["profiles"]["c_rate_profiles"][profile_key]

    if "power_kw" in detected:
        profile["power_kw"] = float(detected["power_kw"]["value"])

    if "dc_bus_current_a" in detected:
        profile["dc_bus_current_a"] = float(detected["dc_bus_current_a"]["value"])

    if "containers_per_pcs" in detected:
        profile["containers_per_pcs"] = int(
            round(float(detected["containers_per_pcs"]["value"]))
        )

    if "total_energy_kwh" in detected:
        selected_container = db["selected_components"]["container"]

        db["catalog"]["containers"][selected_container]["energy_kwh"] = float(
            detected["total_energy_kwh"]["value"]
        )

    return db


def print_detection_report(detected: Dict[str, Dict[str, Any]]) -> None:
    if not detected:
        print("No mapped values detected.")
        return

    print("Detected values:")

    for key, info in detected.items():
        print(
            f"  - {key}: {info['value']} "
            f"(sheet={info['sheet']!r}, row={info['row']}, "
            f"column={info['column']}, label={info['matched_label']!r})"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update BESS Streamlit dashboard data/db.json from Excel sizing workbook."
    )

    parser.add_argument(
        "excel_path",
        type=Path,
        help="Path to the Excel sizing workbook."
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to db.json. Default: data/db.json"
    )

    parser.add_argument(
        "--profile",
        default="0.25C",
        help="C-rate profile to update, for example 0.25C, 0.5C, or 1C. Default: 0.25C"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect and print values without writing to db.json."
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a backup of db.json before writing."
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {args.excel_path}")

    db = load_db(args.db)

    detected = detect_values_from_excel(args.excel_path)
    print_detection_report(detected)

    if args.dry_run:
        print("Dry run selected. No changes written.")
        return

    updated_db = apply_detected_values(
        db=db,
        detected=detected,
        profile_key=args.profile
    )

    save_db(
        db=updated_db,
        db_path=args.db,
        create_backup=not args.no_backup
    )


if __name__ == "__main__":
    main()