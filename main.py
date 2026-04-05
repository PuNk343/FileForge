"""
main.py — CLI entry point for FileForge v0.1

Usage:
    python main.py scan /path/to/dir
    python main.py scan /path/to/dir --no-hash
    python main.py report
    python main.py export --format csv
"""

import json
import time
from pathlib import Path

import click

from config import Config
from database import Database
from scanner import scan_directory
from insights import InsightsEngine


# ── Utilities ──────────────────────────────────────────────────────────────────

def fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(b) < 1_024:
            return f"{b:,.1f} {unit}"
        b = int(b / 1_024)
    return f"{b:,.1f} PB"


def fmt_pct(value: float, total: float) -> str:
    if not total:
        return "  0.0%"
    return f"{value / total * 100:5.1f}%"


BAR_WIDTH = 18

def bar(pct: float) -> str:
    filled = round(pct / 100 * BAR_WIDTH)
    return "█" * filled + "░" * (BAR_WIDTH - filled)


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.group()
@click.version_option("0.1.0", prog_name="FileForge")
def cli():
    """FileForge — intelligent local file organizer."""


@cli.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.option("--no-hash",  is_flag=True, help="Skip SHA-256 hashing (faster scan).")
@click.option("--db",       default=None, help="Custom path to SQLite database.")
def scan(path: str, no_hash: bool, db: str):
    """Scan a directory and index every file found."""

    config = Config(scan_root=Path(path))
    if db:
        config.db_path = Path(db)
    if no_hash:
        # Effectively disables hashing by setting limit to 0 bytes
        config.max_file_size_gb = 0.0

    database = Database(config)
    root     = Path(path).resolve()

    click.echo()
    click.secho(f"  FileForge v0.1  Scanning: {root}", bold=True)
    click.echo("  " + "─" * 54)

    t_start = time.time()
    scan_id = database.start_scan(str(root), t_start)

    batch       = []
    total_files = 0
    total_size  = 0
    BATCH       = 500

    def on_progress(n: int):
        click.echo(f"\r  Indexed {n:>7,} files …", nl=False)

    for record in scan_directory(root, config, progress_cb=on_progress):
        batch.append(record.to_dict())
        total_files += 1
        total_size  += record.size

        if len(batch) >= BATCH:
            database.batch_upsert(batch)
            batch.clear()

    if batch:
        database.batch_upsert(batch)

    click.echo(f"\r  Indexed {total_files:>7,} files …  done.")

    click.echo("  Marking duplicates …", nl=False)
    database.mark_duplicates()
    click.echo(" done.")

    elapsed = time.time() - t_start
    database.finish_scan(scan_id, time.time(), total_files, total_size)

    click.echo()
    click.secho(
        f"  ✓  {total_files:,} files  ·  {fmt_size(total_size)}  ·  {elapsed:.1f}s",
        fg="green",
    )
    click.echo()


@cli.command()
@click.option("--db", default=None, help="Custom path to SQLite database.")
def report(db: str):
    """Print an insights report from the last scan."""

    config = Config()
    if db:
        config.db_path = Path(db)

    engine = InsightsEngine(Database(config), config)
    r      = engine.generate()

    click.echo()
    click.secho("  ══  FileForge Report  ══", bold=True)
    click.echo()

    # ── Summary ──────────────────────────────────────────────────────────────
    click.secho("  Overview", bold=True)
    click.echo(f"  {'Total files':<22} {r.total_files:>10,}")
    click.echo(f"  {'Total size':<22} {fmt_size(r.total_size_bytes):>10}")
    click.echo(f"  {'Wasted (duplicates)':<22} {fmt_size(r.wasted_bytes):>10}")
    click.echo(
        f"  {'Untouched files':<22} {r.old_files_count:>10,}"
        f"  (>{config.old_file_days}d unchanged)"
    )
    click.echo()

    # ── Categories ────────────────────────────────────────────────────────────
    click.secho("  By category", bold=True)
    click.echo(f"  {'category':<12} {'files':>7}  {'size':>9}  {'%size':>6}  ")
    click.echo("  " + "─" * 54)
    for cat, stat in r.category_stats.items():
        click.echo(
            f"  {cat:<12} {stat.count:>7,}  {fmt_size(stat.size_bytes):>9}"
            f"  {stat.pct_size:>5.1f}%  {bar(stat.pct_size)}"
        )
    click.echo()

    # ── Largest files ─────────────────────────────────────────────────────────
    click.secho("  Largest files", bold=True)
    for f in r.largest_files[:10]:
        click.echo(f"  {fmt_size(f['size']):>10}  {f['name']}")
    click.echo()

    # ── Duplicates ────────────────────────────────────────────────────────────
    if r.duplicate_groups:
        click.secho(
            f"  Duplicate groups  ({len(r.duplicate_groups)} groups  ·  "
            f"{fmt_size(r.wasted_bytes)} wasted)",
            bold=True,
        )
        for g in r.duplicate_groups[:8]:
            click.secho(
                f"  [{g.copies}×]  wasted {fmt_size(g.wasted_bytes)}  "
                f"  sha256: {g.sha256_prefix}",
                fg="yellow",
            )
            for p in g.paths[:3]:
                click.echo(f"        {p}")
            if len(g.paths) > 3:
                click.echo(f"        … and {len(g.paths) - 3} more")
        click.echo()
    else:
        click.secho("  No duplicates found.", fg="green")
        click.echo()

    # ── Heavy dirs ────────────────────────────────────────────────────────────
    if r.heavy_dirs:
        click.secho("  Heaviest directories", bold=True)
        for d in r.heavy_dirs[:8]:
            click.echo(
                f"  {fmt_size(d['total_size']):>10}  "
                f"({d['file_count']:>5,} files)  {d['dir']}"
            )
        click.echo()


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["csv", "json"]), default="json")
@click.option("--output", "-o", default="fileforge_export", help="Output filename (no extension).")
@click.option("--db", default=None, help="Custom path to SQLite database.")
def export(fmt: str, output: str, db: str):
    """Export the full file index to CSV or JSON."""
    import csv, sqlite3

    config = Config()
    if db:
        config.db_path = Path(db)

    out_path = Path(output).with_suffix(f".{fmt}")

    with Database(config).connect() as conn:
        rows = conn.execute(
            "SELECT path, name, extension, size, category, sha256, "
            "       created_at, modified_at, scanned_at, is_duplicate "
            "FROM files ORDER BY size DESC;"
        ).fetchall()

    if fmt == "json":
        data = [dict(r) for r in rows]
        out_path.write_text(json.dumps(data, indent=2))
    else:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=dict(rows[0]).keys() if rows else [])
            writer.writeheader()
            writer.writerows(dict(r) for r in rows)

    click.secho(f"  ✓  Exported {len(rows):,} records → {out_path}", fg="green")


if __name__ == "__main__":
    cli()
