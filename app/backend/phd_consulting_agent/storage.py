from __future__ import annotations

import sqlite3
from pathlib import Path

from phd_consulting_agent.models import CaseCreate, GeneratedOutput, StudentCase, utc_now


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS outputs (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES cases(id)
            );
            """
        )


class CaseRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def create_case(self, data: CaseCreate) -> StudentCase:
        case = StudentCase(
            student_name=data.student_name,
            summary=data.summary,
            target_regions=data.target_regions,
            notes=data.notes,
        )
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO cases (id, payload, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (
                    case.id,
                    case.model_dump_json(),
                    case.created_at.isoformat(),
                    case.updated_at.isoformat(),
                ),
            )
        return case

    def get_case(self, case_id: str) -> StudentCase | None:
        with connect(self.db_path) as conn:
            row = conn.execute("SELECT payload FROM cases WHERE id = ?", (case_id,)).fetchone()
        if row is None:
            return None
        return StudentCase.model_validate_json(row["payload"])

    def list_cases(self) -> list[StudentCase]:
        with connect(self.db_path) as conn:
            rows = conn.execute("SELECT payload FROM cases ORDER BY created_at DESC").fetchall()
        return [StudentCase.model_validate_json(row["payload"]) for row in rows]

    def save_output(self, output: GeneratedOutput) -> GeneratedOutput:
        case = self.get_case(output.case_id)
        if case is None:
            raise ValueError(f"Case not found: {output.case_id}")

        if output.id not in case.output_ids:
            case.output_ids.append(output.id)
        case.updated_at = utc_now()

        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO outputs (id, case_id, kind, payload, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    output.id,
                    output.case_id,
                    output.kind.value,
                    output.model_dump_json(),
                    output.created_at.isoformat(),
                ),
            )
            conn.execute(
                "UPDATE cases SET payload = ?, updated_at = ? WHERE id = ?",
                (case.model_dump_json(), case.updated_at.isoformat(), case.id),
            )
        return output

    def list_outputs(self, case_id: str) -> list[GeneratedOutput]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT payload FROM outputs WHERE case_id = ? ORDER BY created_at ASC",
                (case_id,),
            ).fetchall()
        return [GeneratedOutput.model_validate_json(row["payload"]) for row in rows]
