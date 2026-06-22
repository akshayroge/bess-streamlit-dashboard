from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "db.json"

ASSETS_DIR = ROOT / "assets"
CSS_PATH = ASSETS_DIR / "styles" / "dashboard.css"

IMAGES_DIR = ASSETS_DIR / "images"
EQUIPMENT_IMAGES_DIR = IMAGES_DIR / "equipment"
LOGO_IMAGES_DIR = IMAGES_DIR / "logos"