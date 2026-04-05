"""
insights.py — Insights engine for FileForge v0.1

Queries the indexed database and produces structured, human-readable analysis.
No file system access here — pure SQL over the stored data.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config import Config
from database import Database


# ── Report data model ──────────────────────────────────────────────────────────

@dataclass
class CategoryStat:
    count: int
    size_bytes: int
    pct_size: float = 0.0   # populated after totals are known


@dataclass
class DuplicateGroup:
    sha256_prefix: str
    copies: int
    paths: List[str]
    wasted_bytes: int


@dataclass
class InsightReport:
    total_files: int
    total_size_bytes: int
    wasted_bytes: int           # bytes lost to duplicates
    old_files_count: int        # files not modified in > config.old_file_days

    category_stats: Dict[str, CategoryStat] = field(default_factory=dict)
    largest_files: List[dict]   = field(default_factory=list)
    duplicate_groups: List[DuplicateGroup] = field(default_factory=list)
    heavy_dirs: List[dict]      = field(default_factory=list)


# ── Engine ─────────────────────────────────────────────────────────────────────

class InsightsEngine:
    def __init__(self, db: Database, config: Config):
        self.db     = db
        self.config = config

    def generate(self) -> InsightReport:
        with self.db.connect() as conn:
            total_files      = self._total_files(conn)
            total_size_bytes = self._total_size(conn)
            category_stats   = self._category_stats(conn, total_size_bytes)
            largest_files    = self._largest_files(conn)
            duplicate_groups = self._duplicate_groups(conn)
            wasted_bytes     = sum(g.wasted_bytes for g in duplicate_groups)
            old_files_count  = self._old_files(conn)
            heavy_dirs       = self._heavy_dirs(conn)

        return InsightReport(
            total_files      = total_files,
            total_size_bytes = total_size_bytes,
            wasted_bytes     = wasted_bytes,
            old_files_count  = old_files_count,
            category_stats   = category_stats,
            largest_files    = largest_files,
            duplicate_groups = duplicate_groups,
            heavy_dirs       = heavy_dirs,
        )

    # ── Private query helpers ──────────────────────────────────────────────────

    def _total_files(self, conn) -> int:
        return conn.execute("SELECT COUNT(*) FROM files;").fetchone()[0]

    def _total_size(self, conn) -> int:
        return conn.execute(
            "SELECT COALESCE(SUM(size), 0) FROM files;"
        ).fetchone()[0]

    def _category_stats(
        self, conn, total_size: int
    ) -> Dict[str, CategoryStat]:
        rows = conn.execute("""
            SELECT category,
                   COUNT(*)          AS count,
                   COALESCE(SUM(size), 0) AS total_size
            FROM files
            GROUP BY category
            ORDER BY total_size DESC;
        """).fetchall()

        stats = {}
        for row in rows:
            pct = (row["total_size"] / total_size * 100) if total_size else 0.0
            stats[row["category"]] = CategoryStat(
                count      = row["count"],
                size_bytes = row["total_size"],
                pct_size   = round(pct, 1),
            )
        return stats

    def _largest_files(self, conn) -> List[dict]:
        rows = conn.execute("""
            SELECT name, path, size, category
            FROM files
            ORDER BY size DESC
            LIMIT ?;
        """, (self.config.top_files_limit,)).fetchall()
        return [dict(r) for r in rows]

    def _duplicate_groups(self, conn) -> List[DuplicateGroup]:
        rows = conn.execute("""
            SELECT sha256,
                   COUNT(*)               AS copies,
                   SUM(size)              AS total_size,
                   GROUP_CONCAT(path, '|||') AS paths_raw
            FROM files
            WHERE sha256 IS NOT NULL
            GROUP BY sha256
            HAVING COUNT(*) > 1
            ORDER BY total_size DESC;
        """).fetchall()

        groups = []
        for row in rows:
            paths      = row["paths_raw"].split("|||")
            unit_size  = row["total_size"] // row["copies"]
            wasted     = unit_size * (row["copies"] - 1)
            groups.append(DuplicateGroup(
                sha256_prefix = row["sha256"][:16] + "…",
                copies        = row["copies"],
                paths         = paths,
                wasted_bytes  = wasted,
            ))
        return groups

    def _old_files(self, conn) -> int:
        cutoff = (
            datetime.now() - timedelta(days=self.config.old_file_days)
        ).timestamp()
        return conn.execute(
            "SELECT COUNT(*) FROM files WHERE modified_at < ?;", (cutoff,)
        ).fetchone()[0]

    def _heavy_dirs(self, conn) -> List[dict]:
        """Top directories by total size, computed via SQL path parsing."""
        # Cross-platform parent-dir extraction done in Python, not SQL.
        # SQL path manipulation is too brittle across OS separators.
        rows = conn.execute(
            "SELECT path, size FROM files;", ()
        ).fetchall()

        from collections import defaultdict
        import os
        dir_stats: dict = defaultdict(lambda: {"file_count": 0, "total_size": 0})
        for row in rows:
            parent = os.path.dirname(row["path"])
            dir_stats[parent]["file_count"] += 1
            dir_stats[parent]["total_size"] += row["size"]

        sorted_dirs = sorted(
            dir_stats.items(), key=lambda kv: kv[1]["total_size"], reverse=True
        )
        rows = sorted_dirs[: self.config.top_dirs_limit]  # type: ignore[assignment]

        results = []
        for dir_path, stats in rows:
            results.append({
                "dir":        dir_path or "(unknown)",
                "file_count": stats["file_count"],
                "total_size": stats["total_size"],
            })
        return results
