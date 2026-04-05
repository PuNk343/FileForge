"""
database.py — SQLite layer for FileForge v0.1
Handles all persistence. No business logic here.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List

from config import Config


# ── Schema ────────────────────────────────────────────────────────────────────

_CREATE_FILES = """
CREATE TABLE IF NOT EXISTS files (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT    UNIQUE NOT NULL,
    name        TEXT    NOT NULL,
    extension   TEXT,
    size        INTEGER DEFAULT 0,
    category    TEXT,
    sha256      TEXT,
    created_at  REAL,
    modified_at REAL,
    scanned_at  REAL,
    is_duplicate INTEGER DEFAULT 0
);
"""

_CREATE_SCANS = """
CREATE TABLE IF NOT EXISTS scans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_root   TEXT  NOT NULL,
    started_at  REAL  NOT NULL,
    finished_at REAL,
    total_files INTEGER DEFAULT 0,
    total_size  INTEGER DEFAULT 0
);
"""

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_sha256    ON files(sha256);",
    "CREATE INDEX IF NOT EXISTS idx_extension ON files(extension);",
    "CREATE INDEX IF NOT EXISTS idx_category  ON files(category);",
    "CREATE INDEX IF NOT EXISTS idx_size      ON files(size DESC);",
    "CREATE INDEX IF NOT EXISTS idx_modified  ON files(modified_at);",
]

_UPSERT_FILE = """
INSERT INTO files (path, name, extension, size, category, sha256,
                   created_at, modified_at, scanned_at)
VALUES (:path, :name, :extension, :size, :category, :sha256,
        :created_at, :modified_at, :scanned_at)
ON CONFLICT(path) DO UPDATE SET
    size        = excluded.size,
    category    = excluded.category,
    sha256      = excluded.sha256,
    modified_at = excluded.modified_at,
    scanned_at  = excluded.scanned_at;
"""


# ── Database class ─────────────────────────────────────────────────────────────

class Database:
    def __init__(self, config: Config):
        self.db_path = config.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection with WAL mode, auto-commit/rollback."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(_CREATE_FILES)
            conn.execute(_CREATE_SCANS)
            for idx in _INDEXES:
                conn.execute(idx)

    # ── Write operations ───────────────────────────────────────────────────────

    def batch_upsert(self, records: List[dict]) -> None:
        """Insert or update a batch of file records."""
        with self.connect() as conn:
            conn.executemany(_UPSERT_FILE, records)

    def mark_duplicates(self) -> None:
        """Flag all files that share a sha256 with at least one other file."""
        with self.connect() as conn:
            conn.execute("UPDATE files SET is_duplicate = 0;")
            conn.execute("""
                UPDATE files SET is_duplicate = 1
                WHERE sha256 IS NOT NULL
                  AND sha256 IN (
                      SELECT sha256 FROM files
                      WHERE sha256 IS NOT NULL
                      GROUP BY sha256 HAVING COUNT(*) > 1
                  );
            """)

    def start_scan(self, scan_root: str, started_at: float) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO scans (scan_root, started_at) VALUES (?, ?);",
                (scan_root, started_at),
            )
            return cur.lastrowid

    def finish_scan(
        self,
        scan_id: int,
        finished_at: float,
        total_files: int,
        total_size: int,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """UPDATE scans
                   SET finished_at=?, total_files=?, total_size=?
                   WHERE id=?;""",
                (finished_at, total_files, total_size, scan_id),
            )

    # ── Read operations ────────────────────────────────────────────────────────

    def file_exists_and_unchanged(self, path: str, modified_at: float) -> bool:
        """Return True if the file is already indexed with same mtime.
        Used later for incremental re-scanning (v0.1 stub)."""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT modified_at FROM files WHERE path = ?;", (path,)
            ).fetchone()
            return row is not None and abs(row["modified_at"] - modified_at) < 1.0
