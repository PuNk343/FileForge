# 🧠 FileForge v0.2.1

### A Personal Drive Intelligence System

## Overview

FileForge is a local file analysis system that scans your computer, builds a structured index of your files, and reveals patterns in how your storage is actually being used.

It doesn’t move or delete anything. It simply shows you what exists, where it exists, and how it accumulates over time.

The goal is simple:
make your system *understandable*.

---

## What’s new in v0.2.1

This version focuses on **better classification and clarity**.

Previously, a large portion of files were grouped into a generic `"other"` category.
Now, FileForge can recognize more specific file types, giving a clearer picture of what’s actually taking up space.

### New file categories added:

* font → `.ttf`, `.otf`, `.woff`, `.woff2`
* database → `.db`, `.sqlite`, `.sqlite3`, `.mdb`
* executable → `.exe`, `.bin`, `.run`
* system → `.dll`, `.sys`, `.drv`
* config → `.ini`, `.cfg`, `.conf`, `.log`
* disk_image → `.iso`, `.img`, `.vhd`, `.vmdk`
* game_asset → `.pak`, `.assets`, `.ress`

### What this improves:

* reduces the size of the `"other"` category
* helps identify system files vs user files
* makes large storage clusters easier to understand
* reveals hidden patterns (especially in games, engines, and assets)

---

## Features

* Recursive file scanning across any directory or drive
* Metadata extraction (name, path, size, timestamps, extension)
* Expanded file classification (v0.2.1 upgrade)
* Duplicate detection using SHA-256 hashing
* Insights engine providing:

  * total file count and storage usage
  * category-wise breakdown
  * largest files
  * duplicate groups and wasted space
  * old/unused files
  * heaviest directories
* Local SQLite database for persistent storage
* CLI interface using `click`
* Export support (JSON / CSV)

---

## How it works

FileForge follows a simple pipeline:

Scan → Extract metadata → Classify → Store → Analyze → Display insights

Each stage is modular, allowing future upgrades without breaking existing functionality.

---

## Project structure

```text
fileforge/
├── main.py
├── scanner.py
├── database.py
├── insights.py
├── config.py
├── requirements.txt
```

---

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Usage

Scan a directory:

```bash
python main.py scan <path>
```

Generate a report:

```bash
python main.py report
```

Export indexed data:

```bash
python main.py export --format json
```

or

```bash
python main.py export --format csv
```

---

## What you’ll notice

After upgrading to v0.2.1, reports become more informative:

* previously “unknown” files now fall into meaningful categories
* large systems like games and engines become more visible
* storage patterns feel less random and more structured

This version doesn’t add intelligence yet—it improves **visibility and separation**.

---

## Notes

* Classification is still extension-based
* Large files may skip hashing for performance
* No files are modified or deleted

---

## Roadmap

### v0.2.1 (Current)

* Expanded file type classification
* Better breakdown of storage categories

### v0.2.2 (Next)

* Highlight very large files with exact locations
* Improve duplicate grouping clarity

### v0.3+

* Semantic classification (content-aware)
* Context-based grouping
* Intelligent cleanup suggestions

---

## Final thought

FileForge started as a way to scan files.

Now it’s starting to **see structure inside the chaos**.

This version doesn’t make your system smarter yet—
it just makes it **more honest about what’s really there**.
