import json
from typing import Any, Dict

from src.paths import DATA_DIR, DB_PATH


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_db() -> Dict[str, Any]:
    ensure_data_dir()

    if not DB_PATH.exists():
        raise FileNotFoundError(
            "data/db.json was not found. Create it before running the app."
        )

    with DB_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_db(db: Dict[str, Any]) -> None:
    ensure_data_dir()

    with DB_PATH.open("w", encoding="utf-8") as file:
        json.dump(db, file, indent=2)