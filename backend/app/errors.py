from __future__ import annotations

from typing import Any


class AppError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


class CsvValidationError(AppError):
    def __init__(
        self, message: str, details: list[dict[str, Any]] | None = None
    ) -> None:
        super().__init__(
            status_code=422,
            code="invalid_csv",
            message=message,
            details=details,
        )


class DatasetNotFoundError(AppError):
    def __init__(self, dataset_id: str) -> None:
        super().__init__(
            status_code=404,
            code="dataset_not_found",
            message=f"Dataset '{dataset_id}' was not found.",
        )

