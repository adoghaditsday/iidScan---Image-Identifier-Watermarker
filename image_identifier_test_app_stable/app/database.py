import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .config import DB_PATH, STORAGE_DIR


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class IdentifierDatabase:
    def __init__(self, db_path: Path = DB_PATH):
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS image_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifier_code TEXT UNIQUE NOT NULL,
                    original_filename TEXT NOT NULL,
                    original_path TEXT,
                    marked_path TEXT,
                    snapshot_path TEXT,
                    report_path TEXT,
                    sha256_hash TEXT,
                    signature_name TEXT,
                    signature_note TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scanned_filename TEXT NOT NULL,
                    scanned_path TEXT,
                    identifier_code TEXT,
                    matched_record_id INTEGER,
                    report_path TEXT,
                    signature_name TEXT,
                    signature_note TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(matched_record_id) REFERENCES image_records(id)
                )
                """
            )

    def add_image_record(self, **kwargs) -> int:
        kwargs.setdefault("created_at", utc_now_iso())
        columns = ", ".join(kwargs.keys())
        placeholders = ", ".join([":" + key for key in kwargs.keys()])
        with self._connect() as conn:
            cur = conn.execute(
                f"INSERT INTO image_records ({columns}) VALUES ({placeholders})",
                kwargs,
            )
            return int(cur.lastrowid)

    def update_image_record(self, record_id: int, **kwargs) -> None:
        if not kwargs:
            return
        assignments = ", ".join([f"{key}=:{key}" for key in kwargs.keys()])
        kwargs["id"] = record_id
        with self._connect() as conn:
            conn.execute(
                f"UPDATE image_records SET {assignments} WHERE id=:id",
                kwargs,
            )

    def find_by_identifier(self, identifier_code: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT * FROM image_records WHERE identifier_code=?",
                (identifier_code,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def add_scan_report(self, **kwargs) -> int:
        kwargs.setdefault("created_at", utc_now_iso())
        columns = ", ".join(kwargs.keys())
        placeholders = ", ".join([":" + key for key in kwargs.keys()])
        with self._connect() as conn:
            cur = conn.execute(
                f"INSERT INTO scan_reports ({columns}) VALUES ({placeholders})",
                kwargs,
            )
            return int(cur.lastrowid)
