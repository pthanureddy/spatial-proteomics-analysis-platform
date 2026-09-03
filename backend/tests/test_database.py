from __future__ import annotations

import sqlite3

import pytest

from app.database import Database
from app.domain import ProximityRecord


def record(*, score: float = 0.5) -> ProximityRecord:
    return ProximityRecord(
        cell_id="cell-1",
        condition="control",
        protein_a="CD3",
        protein_b="CD4",
        proximity_score=score,
        x=1,
        y=2,
    )


def test_dataset_and_rows_are_inserted_atomically(tmp_path) -> None:
    database = Database(tmp_path / "atomic.sqlite3")
    database.initialize()

    with pytest.raises(sqlite3.IntegrityError):
        database.create_dataset(
            name="Invalid",
            original_filename="invalid.csv",
            records=[record(score=1.5)],
        )

    assert database.list_datasets() == []


def test_read_connections_are_closed_after_use(tmp_path) -> None:
    database_path = tmp_path / "connections.sqlite3"
    database = Database(database_path)
    database.initialize()
    created = database.create_dataset(
        name="Connection lifecycle",
        original_filename="valid.csv",
        records=[record()],
    )
    dataset_id = str(created["id"])

    database.ping()
    database.list_datasets()
    database.get_dataset(dataset_id)
    database.get_observations(dataset_id)
    database.list_cells(dataset_id, limit=10, offset=0)
    database.get_cell(dataset_id, "cell-1")

    renamed = tmp_path / "renamed.sqlite3"
    database_path.rename(renamed)
    assert renamed.exists()

