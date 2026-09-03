from __future__ import annotations

import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.domain import ProximityRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    row_count INTEGER NOT NULL CHECK (row_count > 0),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS proximity_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    cell_id TEXT NOT NULL,
    condition_name TEXT NOT NULL,
    protein_a TEXT NOT NULL,
    protein_b TEXT NOT NULL,
    proximity_score REAL NOT NULL CHECK (
        proximity_score >= 0 AND proximity_score <= 1
    ),
    x REAL NOT NULL CHECK (x >= 0),
    y REAL NOT NULL CHECK (y >= 0)
);

CREATE INDEX IF NOT EXISTS idx_proximity_events_dataset
    ON proximity_events(dataset_id);
CREATE INDEX IF NOT EXISTS idx_proximity_events_dataset_condition
    ON proximity_events(dataset_id, condition_name);
CREATE INDEX IF NOT EXISTS idx_proximity_events_dataset_pair
    ON proximity_events(dataset_id, protein_a, protein_b);
"""


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def ping(self) -> None:
        with self.connection() as connection:
            connection.execute("SELECT 1").fetchone()

    def create_dataset(
        self,
        *,
        name: str,
        original_filename: str,
        records: Sequence[ProximityRecord],
    ) -> dict[str, object]:
        dataset_id = str(uuid4())
        created_at = datetime.now(UTC).isoformat()
        with self.transaction() as connection:
            connection.execute(
                """
                INSERT INTO datasets (id, name, original_filename, row_count, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (dataset_id, name, original_filename, len(records), created_at),
            )
            connection.executemany(
                """
                INSERT INTO proximity_events (
                    dataset_id, cell_id, condition_name, protein_a, protein_b,
                    proximity_score, x, y
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        dataset_id,
                        record.cell_id,
                        record.condition,
                        record.protein_a,
                        record.protein_b,
                        record.proximity_score,
                        record.x,
                        record.y,
                    )
                    for record in records
                ),
            )
        return {
            "id": dataset_id,
            "name": name,
            "original_filename": original_filename,
            "row_count": len(records),
            "created_at": created_at,
        }

    def list_datasets(self) -> list[dict[str, object]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, name, original_filename, row_count, created_at
                FROM datasets
                ORDER BY created_at DESC, id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_dataset(self, dataset_id: str) -> dict[str, object] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT id, name, original_filename, row_count, created_at
                FROM datasets
                WHERE id = ?
                """,
                (dataset_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_observations(self, dataset_id: str) -> list[dict[str, object]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    cell_id,
                    condition_name AS condition,
                    protein_a,
                    protein_b,
                    proximity_score,
                    x,
                    y
                FROM proximity_events
                WHERE dataset_id = ?
                ORDER BY id ASC
                """,
                (dataset_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_cells(
        self, dataset_id: str, *, limit: int, offset: int
    ) -> tuple[int, list[dict[str, object]]]:
        with self.connection() as connection:
            total = connection.execute(
                """
                SELECT COUNT(DISTINCT cell_id)
                FROM proximity_events
                WHERE dataset_id = ?
                """,
                (dataset_id,),
            ).fetchone()[0]
            rows = connection.execute(
                """
                SELECT
                    cell_id,
                    MIN(condition_name) AS condition,
                    MIN(x) AS x,
                    MIN(y) AS y,
                    COUNT(*) AS observation_count,
                    ROUND(AVG(proximity_score), 6) AS mean_score
                FROM proximity_events
                WHERE dataset_id = ?
                GROUP BY cell_id
                ORDER BY cell_id ASC
                LIMIT ? OFFSET ?
                """,
                (dataset_id, limit, offset),
            ).fetchall()
        return int(total), [dict(row) for row in rows]

    def get_cell(
        self, dataset_id: str, cell_id: str
    ) -> dict[str, object] | None:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    cell_id,
                    condition_name AS condition,
                    protein_a,
                    protein_b,
                    proximity_score,
                    x,
                    y
                FROM proximity_events
                WHERE dataset_id = ? AND cell_id = ?
                ORDER BY protein_a ASC, protein_b ASC, id ASC
                """,
                (dataset_id, cell_id),
            ).fetchall()
        if not rows:
            return None
        first = rows[0]
        return {
            "cell_id": first["cell_id"],
            "condition": first["condition"],
            "x": first["x"],
            "y": first["y"],
            "observations": [
                {
                    "protein_a": row["protein_a"],
                    "protein_b": row["protein_b"],
                    "proximity_score": row["proximity_score"],
                }
                for row in rows
            ],
        }
