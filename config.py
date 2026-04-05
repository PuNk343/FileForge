"""
config.py — Central configuration for FileForge v0.1
All tuneable constants live here. No magic numbers elsewhere.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set


@dataclass
class Config:
    # ── Scanning ──────────────────────────────────────────────
    scan_root: Path = field(default_factory=Path.home)
    ignore_hidden: bool = True
    ignore_system_dirs: bool = True
    max_file_size_gb: float = 10.0          # skip hashing files above this

    # ── Storage ───────────────────────────────────────────────
    db_path: Path = field(
        default_factory=lambda: Path.home() / ".file_organizer" / "fileforge.db"
    )

    # ── Insights thresholds ───────────────────────────────────
    large_file_threshold_mb: float = 100.0
    old_file_days: int = 365
    top_dirs_limit: int = 10
    top_files_limit: int = 20

    # ── Dirs to always skip ───────────────────────────────────
    skip_dirs: List[str] = field(default_factory=lambda: [
        "__pycache__", ".git", ".svn", "node_modules", ".venv", "venv",
        "env", ".tox", ".mypy_cache", ".pytest_cache",
        "System Volume Information", "$RECYCLE.BIN",
        "Windows", "Program Files", "Program Files (x86)",
        ".Trash", ".Spotlight-V100", ".fseventsd",
    ])

    # ── Extension → category maps ─────────────────────────────
    IMAGE_EXTS: Set[str] = field(default_factory=lambda: {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
        ".ico", ".tiff", ".tif", ".raw", ".cr2", ".nef", ".heic", ".heif",
    })
    VIDEO_EXTS: Set[str] = field(default_factory=lambda: {
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
        ".m4v", ".3gp", ".ts", ".vob",
    })
    AUDIO_EXTS: Set[str] = field(default_factory=lambda: {
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a",
        ".wma", ".opus", ".aiff",
    })
    DOCUMENT_EXTS: Set[str] = field(default_factory=lambda: {
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".txt", ".md", ".markdown", ".odt", ".ods", ".odp",
        ".rtf", ".csv", ".epub",
    })
    CODE_EXTS: Set[str] = field(default_factory=lambda: {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
        ".java", ".kt", ".cpp", ".c", ".h", ".hpp", ".go", ".rs",
        ".rb", ".php", ".sh", ".bash", ".zsh", ".sql", ".r",
        ".json", ".yaml", ".yml", ".xml", ".toml", ".ini", ".env",
        ".ipynb", ".lua", ".dart", ".swift",
    })
    ARCHIVE_EXTS: Set[str] = field(default_factory=lambda: {
        ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2",
        ".xz", ".tar.gz", ".tar.bz2", ".tar.xz", ".tgz",
    })
    INSTALLER_EXTS: Set[str] = field(default_factory=lambda: {
        ".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".appimage",
    })
