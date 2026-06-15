from pathlib import Path

APP_NAME = "Image Identifier Test App"
APP_VERSION = "0.3.0-view-modes"

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
MARKED_DIR = STORAGE_DIR / "marked"
SNAPSHOT_DIR = STORAGE_DIR / "snapshots"
REPORT_DIR = STORAGE_DIR / "reports"
DB_PATH = STORAGE_DIR / "identifiers.db"

MAGIC_HEADER = "GSG3IMGIDv1"

ACCOUNTS_PATH = STORAGE_DIR / "accounts.json"
USER_LOG_DIR = STORAGE_DIR / "user_logs"
ASSET_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSET_DIR / "logo.png"
