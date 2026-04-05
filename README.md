# 🧠 FileForge v0.1

### A Personal Drive Intelligence System

## Overview

FileForge is a local file analysis tool that helps you understand what’s actually sitting on your computer. It scans your files, organizes the information, and shows you patterns that are usually hidden in plain sight—like duplicate files, storage-heavy folders, or forgotten downloads.

Instead of digging through folders manually, you get a clear picture of your digital space in seconds.
It’s less about organizing files for you, and more about helping you *see* what’s going on.

---

## What it can do (v0.1)

* Scan any folder or drive and index all files
* Extract useful metadata like name, path, size, timestamps
* Categorize files into images, videos, documents, code, archives, installers, and others
* Detect duplicate files using hashing
* Show insights like:

  * total storage usage
  * category-wise breakdown
  * largest files
  * duplicate groups and wasted space
  * old or untouched files
  * heaviest directories
* Store everything locally using SQLite
* Export your data to JSON or CSV

---

## How it works

At a high level, FileForge follows a simple flow:

Scan → Understand basic structure → Store → Analyze → Show insights

Each step is designed to be simple and reliable so it can be extended later without breaking.

---

## Project structure

```
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

Clone or create the project folder and move into it:

```
git clone <your-repo-url>
cd fileforge
```

Create a virtual environment:

```
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```
pip install -r requirements.txt
```

---

## How to use

To scan a folder:

```
python main.py scan <path>
```

Example:

```
python main.py scan "C:\Users\YourName\Downloads"
```

To generate a report:

```
python main.py report
```

To export your data:

```
python main.py export --format json
```

or

```
python main.py export --format csv
```

---

## What you’ll start noticing

Once you run it on a real folder, a few things usually stand out:

* large files you forgot existed
* folders quietly taking up space
* duplicate downloads with slightly different names
* patterns in how you store (or don’t store) files

It’s a small shift, but it changes how you look at your system.

---

## Notes

* Large files may skip hashing to keep scans fast
* Hidden/system folders can be ignored through config
* Nothing is deleted or modified in this version

---

## Where this is going

Right now, FileForge focuses on structure and clarity.

Next steps include:

* deeper content understanding (NLP-based classification)
* smarter grouping of related files
* suggestions for cleanup and organization
* eventually, a system that learns from your habits

The long-term idea is simple:
a system that doesn’t just list your files, but actually *understands* them.

---

## Final thought

FileForge started from a very common problem:
files piling up, folders getting messy, and no clear way to fix it.

This is the first step toward changing that—quietly, locally, and intelligently.
