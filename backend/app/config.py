from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    database_path: Path
    max_upload_bytes: int = 5 * 1024 * 1024
    max_rows: int = 100_000
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)

    @classmethod
    def from_environment(cls) -> "Settings":
        origins = tuple(
            origin.strip()
            for origin in os.getenv(
                "SPATIAL_CORS_ORIGINS", "http://localhost:5173"
            ).split(",")
            if origin.strip()
        )
        return cls(
            database_path=Path(
                os.getenv(
                    "SPATIAL_DATABASE_PATH",
                    "./data/spatial_proteomics.sqlite3",
                )
            ),
            max_upload_bytes=_positive_int(
                "SPATIAL_MAX_UPLOAD_BYTES", 5 * 1024 * 1024
            ),
            max_rows=_positive_int("SPATIAL_MAX_ROWS", 100_000),
            cors_origins=origins,
        )

