from __future__ import annotations

import pytest

from app.errors import CsvValidationError
from app.services.csv_validation import validate_csv


def test_valid_csv_is_trimmed_and_pair_is_canonicalized() -> None:
    content = b"""cell_id,condition,protein_a,protein_b,proximity_score,x,y,note
 cell-1 , control ,CD4,CD3,0.75,1,2,ignored
"""
    result = validate_csv(content, max_rows=10)

    assert len(result.records) == 1
    assert result.records[0].cell_id == "cell-1"
    assert (result.records[0].protein_a, result.records[0].protein_b) == (
        "CD3",
        "CD4",
    )
    assert result.warnings == ("Ignored columns: note.",)


@pytest.mark.parametrize(
    ("content", "expected_message"),
    [
        (
            b"cell_id,condition\ncell-1,control\n",
            "missing required columns",
        ),
        (
            b"""cell_id,condition,protein_a,protein_b,proximity_score,x,y
cell-1,control,CD3,CD3,0.5,1,2
""",
            "invalid rows",
        ),
        (
            b"""cell_id,condition,protein_a,protein_b,proximity_score,x,y
cell-1,control,CD3,CD4,1.5,1,2
""",
            "invalid rows",
        ),
        (
            b"""cell_id,condition,protein_a,protein_b,proximity_score,x,y
cell-1,control,CD3,CD4,0.5,-1,2
""",
            "invalid rows",
        ),
    ],
)
def test_invalid_csv_is_rejected(content: bytes, expected_message: str) -> None:
    with pytest.raises(CsvValidationError, match=expected_message):
        validate_csv(content, max_rows=10)


def test_row_limit_is_enforced() -> None:
    content = b"""cell_id,condition,protein_a,protein_b,proximity_score,x,y
cell-1,control,CD3,CD4,0.5,1,2
cell-2,control,CD3,CD8,0.6,2,3
"""
    with pytest.raises(CsvValidationError, match="configured limit"):
        validate_csv(content, max_rows=1)


def test_utf8_is_required() -> None:
    with pytest.raises(CsvValidationError, match="UTF-8"):
        validate_csv(b"\xff\xfe", max_rows=10)


def test_repeated_cell_requires_consistent_metadata() -> None:
    content = b"""cell_id,condition,protein_a,protein_b,proximity_score,x,y
cell-1,control,CD3,CD4,0.5,1,2
cell-1,treated,CD3,CD8,0.6,1,2
"""
    with pytest.raises(CsvValidationError) as exc_info:
        validate_csv(content, max_rows=10)

    assert exc_info.value.details[0]["field"] == "cell_id"
    assert "must also share" in str(exc_info.value.details[0]["message"])
