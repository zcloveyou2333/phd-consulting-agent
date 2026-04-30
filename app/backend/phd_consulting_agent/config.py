from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    repo_root: Path
    data_dir: Path
    database_path: Path
    gemini_cleaned_dir: Path


def default_config() -> AppConfig:
    repo_root = Path(__file__).resolve().parents[3]
    data_dir = repo_root / "data" / "app"
    return AppConfig(
        repo_root=repo_root,
        data_dir=data_dir,
        database_path=data_dir / "phd_consulting_agent.sqlite3",
        gemini_cleaned_dir=repo_root / "data" / "cleaned" / "gemini_takeout",
    )
