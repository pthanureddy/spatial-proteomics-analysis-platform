from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass

from app.domain import ProximityRecord
from app.errors import CsvValidationError

REQUIRED_COLUMNS = (
    "cell_id",
    "condition",
    "protein_a",
    "protein_b",
    "proximity_score",
    "x",
    "y",
)
MAX_TEXT_LENGTHS = {
    "cell_id": 128,
    "condition": 64,
    "protein_a": 64,
    "protein_b": 64,
}
MAX_REPORTED_ERRORS = 25


@dataclass(frozen=True, slots=True)
class ValidationResult:
    records: tuple[ProximityRecord, ...]
    warnings: tuple[str, ...]


def _text_value(
    row: dict[str, str | None],
    field: str,
    row_number: int,
    errors: list[dict[str, object]],
) -> str:
    value = (row.get(field) or "").strip()
    if not value:
        errors.append(
            {"row": row_number, "field": field, "message": "Value is required."}
        )
    elif len(value) > MAX_TEXT_LENGTHS[field]:
        errors.append(
            {
                "row": row_number,
                "field": field,
                "message": f"Must be at most {MAX_TEXT_LENGTHS[field]} characters.",
            }
        )
    return value


def _number_value(
    row: dict[str, str | None],
    field: str,
    row_number: int,
    errors: list[dict[str, object]],
) -> float | None:
    raw_value = (row.get(field) or "").strip()
    try:
        value = float(raw_value)
    except ValueError:
        errors.append(
            {
                "row": row_number,
                "field": field,
                "message": "Must be a finite number.",
            }
        )
        return None
    if not math.isfinite(value):
        errors.append(
            {
                "row": row_number,
                "field": field,
                "message": "Must be a finite number.",
            }
        )
        return None
    return value


def validate_csv(content: bytes, *, max_rows: int) -> ValidationResult:
    if not content:
        raise CsvValidationError("The uploaded CSV is empty.")

    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CsvValidationError(
            "The CSV must use UTF-8 encoding.",
            [{"row": None, "field": None, "message": str(exc)}],
        ) from exc

    try:
        reader = csv.DictReader(io.StringIO(decoded, newline=""))
        if reader.fieldnames is None:
            raise CsvValidationError("The CSV must include a header row.")

        fieldnames = [name.strip() if name else "" for name in reader.fieldnames]
        if len(fieldnames) != len(set(fieldnames)):
            raise CsvValidationError("The CSV header contains duplicate columns.")
        reader.fieldnames = fieldnames

        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            raise CsvValidationError(
                "The CSV is missing required columns.",
                [
                    {
                        "row": 1,
                        "field": column,
                        "message": "Required column is missing.",
                    }
                    for column in missing
                ],
            )

        ignored = sorted(set(fieldnames) - set(REQUIRED_COLUMNS))
        warnings = (
            (f"Ignored columns: {', '.join(ignored)}.",) if ignored else ()
        )
        records: list[ProximityRecord] = []
        errors: list[dict[str, object]] = []
        cell_metadata: dict[str, tuple[str, float, float]] = {}

        for row_number, row in enumerate(reader, start=2):
            if row_number - 1 > max_rows:
                raise CsvValidationError(
                    f"The CSV exceeds the configured limit of {max_rows} data rows."
                )
            if None in row:
                errors.append(
                    {
                        "row": row_number,
                        "field": None,
                        "message": "Row has more values than the header.",
                    }
                )
                if len(errors) >= MAX_REPORTED_ERRORS:
                    break
                continue

            row_error_start = len(errors)
            cell_id = _text_value(row, "cell_id", row_number, errors)
            condition = _text_value(row, "condition", row_number, errors)
            protein_a = _text_value(row, "protein_a", row_number, errors)
            protein_b = _text_value(row, "protein_b", row_number, errors)
            score = _number_value(
                row, "proximity_score", row_number, errors
            )
            x = _number_value(row, "x", row_number, errors)
            y = _number_value(row, "y", row_number, errors)

            if (
                protein_a
                and protein_b
                and protein_a.casefold() == protein_b.casefold()
            ):
                errors.append(
                    {
                        "row": row_number,
                        "field": "protein_b",
                        "message": "Self-pairs are not accepted.",
                    }
                )
            if score is not None and not 0 <= score <= 1:
                errors.append(
                    {
                        "row": row_number,
                        "field": "proximity_score",
                        "message": "Must be between 0 and 1 inclusive.",
                    }
                )
            for field, value in (("x", x), ("y", y)):
                if value is not None and value < 0:
                    errors.append(
                        {
                            "row": row_number,
                            "field": field,
                            "message": "Must be greater than or equal to 0.",
                        }
                    )

            if len(errors) == row_error_start:
                assert score is not None and x is not None and y is not None
                existing_metadata = cell_metadata.get(cell_id)
                current_metadata = (condition, x, y)
                if (
                    existing_metadata is not None
                    and existing_metadata != current_metadata
                ):
                    errors.append(
                        {
                            "row": row_number,
                            "field": "cell_id",
                            "message": (
                                "Rows sharing a cell_id must also share condition, "
                                "x and y."
                            ),
                        }
                    )
                    continue
                cell_metadata[cell_id] = current_metadata
                if protein_b.casefold() < protein_a.casefold():
                    protein_a, protein_b = protein_b, protein_a
                records.append(
                    ProximityRecord(
                        cell_id=cell_id,
                        condition=condition,
                        protein_a=protein_a,
                        protein_b=protein_b,
                        proximity_score=score,
                        x=x,
                        y=y,
                    )
                )
            if len(errors) >= MAX_REPORTED_ERRORS:
                break
    except csv.Error as exc:
        raise CsvValidationError(
            "The CSV could not be parsed.",
            [{"row": None, "field": None, "message": str(exc)}],
        ) from exc

    if errors:
        suffix = (
            f" Showing the first {MAX_REPORTED_ERRORS} errors."
            if len(errors) >= MAX_REPORTED_ERRORS
            else ""
        )
        raise CsvValidationError(
            f"The CSV contains invalid rows.{suffix}", errors[:MAX_REPORTED_ERRORS]
        )
    if not records:
        raise CsvValidationError("The CSV must contain at least one data row.")

    return ValidationResult(records=tuple(records), warnings=warnings)
