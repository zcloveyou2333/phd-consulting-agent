from __future__ import annotations

import csv
from pathlib import Path


def load_relevant_index(cleaned_dir: Path, limit: int = 100) -> list[dict[str, str]]:
    path = cleaned_dir / "gemini_activity_relevant_index.csv"
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
            if len(rows) >= limit:
                break
    return rows
