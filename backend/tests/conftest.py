from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    settings = Settings(
        database_path=tmp_path / "test.sqlite3",
        max_upload_bytes=10_000,
        max_rows=100,
        cors_origins=("http://testserver",),
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def valid_csv() -> bytes:
    return b"""cell_id,condition,protein_a,protein_b,proximity_score,x,y
cell-1,control,CD4,CD3,0.4,1.0,2.0
cell-2,treated,CD3,CD4,0.8,3.0,4.0
cell-2,treated,CD8,PD1,0.6,3.0,4.0
"""
