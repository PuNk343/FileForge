"""
scanner.py — File crawler, metadata extractor, and classifier for FileForge v0.1

Deliberately folds metadata.py and classifier.py into one tight module.
They're simple enough at v0.1 that separate files would be noise.
When v0.2 adds NLP-based classification, classifier.py can be extracted cleanly.
"""

import hashlib
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator, Optional, Callable

from config import Config

HASH_CHUNK = 65_536  # 64 KB


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class FileRecord:
    path: str
    name: str
    extension: str
    size: int
    category: str
    sha256: Optional[str]
    created_at: float
    modified_at: float
    scanned_at: float

    def to_dict(self) -> dict:
        return asdict(self)


# ── Classification ─────────────────────────────────────────────────────────────

def classify(extension: str, config: Config) -> str:
    """Map a file extension to a category label.

    Designed to be replaced by an ML classifier in v0.2 without changing
    the calling code — same signature, richer logic.
    """
    ext = extension.lower()
    if ext in config.IMAGE_EXTS:     return "image"
    if ext in config.VIDEO_EXTS:     return "video"
    if ext in config.AUDIO_EXTS:     return "audio"
    if ext in config.DOCUMENT_EXTS:  return "document"
    if ext in config.CODE_EXTS:      return "code"
    if ext in config.ARCHIVE_EXTS:   return "archive"
    if ext in config.INSTALLER_EXTS: return "installer"
    return "other"


# ── Hashing ────────────────────────────────────────────────────────────────────

def compute_sha256(path: Path, size: int, config: Config) -> Optional[str]:
    """Compute SHA-256 hash. Returns None on permission errors or oversized files.

    Skipping huge files keeps the scan fast. Their size alone makes them
    identifiable anyway.
    """
    if size > config.max_file_size_gb * 1_024**3:
        return None
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            while chunk := fh.read(HASH_CHUNK):
                h.update(chunk)
        return h.hexdigest()
    except (PermissionError, OSError):
        return None


# ── Scanner ────────────────────────────────────────────────────────────────────

def scan_directory(
    root: Path,
    config: Config,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> Iterator[FileRecord]:
    """Recursively yield one FileRecord per accessible file under root.

    Args:
        root:        Directory to scan.
        config:      Config instance (skip dirs, hashing limits, etc.).
        progress_cb: Optional callback(total_so_far) called every 100 files.

    Yields:
        FileRecord for each file found.
    """
    count = 0

    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda _: None):
        # Prune unwanted subdirectories in-place (os.walk respects this).
        dirnames[:] = [
            d for d in dirnames
            if d not in config.skip_dirs
            and not (config.ignore_hidden and d.startswith("."))
        ]

        for filename in filenames:
            if config.ignore_hidden and filename.startswith("."):
                continue

            filepath = Path(dirpath) / filename

            try:
                stat = filepath.stat()
            except (PermissionError, OSError):
                continue

            size      = stat.st_size
            extension = filepath.suffix.lower()

            yield FileRecord(
                path        = str(filepath),
                name        = filename,
                extension   = extension,
                size        = size,
                category    = classify(extension, config),
                sha256      = compute_sha256(filepath, size, config),
                created_at  = stat.st_ctime,
                modified_at = stat.st_mtime,
                scanned_at  = time.time(),
            )

            count += 1
            if progress_cb and count % 100 == 0:
                progress_cb(count)
