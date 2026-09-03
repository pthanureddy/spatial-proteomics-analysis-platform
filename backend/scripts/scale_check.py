from __future__ import annotations

import argparse
import csv
import io
import json
import platform
import sys
import tempfile
import time
from pathlib import Path

from app.database import Database
from app.services.analysis import analyse_observations
from app.services.csv_validation import REQUIRED_COLUMNS, validate_csv
from scripts.generate_sample import generate


def elapsed(started: float) -> float:
    return round(time.perf_counter() - started, 4)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run a local, single-process scale check. This is diagnostic output, "
            "not a general performance claim."
        )
    )
    parser.add_argument("--rows", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if args.rows <= 0 or args.rows % 8:
        parser.error("--rows must be positive and divisible by 8")

    timings: dict[str, float] = {}
    started = time.perf_counter()
    generated = generate(
        cells_per_condition=args.rows // 8,
        seed=args.seed,
    )
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(REQUIRED_COLUMNS))
    writer.writeheader()
    writer.writerows(generated)
    payload = buffer.getvalue().encode("utf-8")
    timings["generate_csv_seconds"] = elapsed(started)

    started = time.perf_counter()
    validated = validate_csv(payload, max_rows=args.rows)
    timings["validate_seconds"] = elapsed(started)

    with tempfile.TemporaryDirectory(prefix="spatial-scale-check-") as temp_dir:
        database = Database(Path(temp_dir) / "scale.sqlite3")
        database.initialize()
        started = time.perf_counter()
        dataset = database.create_dataset(
            name="Scale check",
            original_filename="generated.csv",
            records=validated.records,
        )
        timings["sqlite_insert_seconds"] = elapsed(started)

        started = time.perf_counter()
        rows = database.get_observations(str(dataset["id"]))
        result = analyse_observations(str(dataset["id"]), rows)
        timings["read_and_analyse_seconds"] = elapsed(started)

    assert result["summary"]["observation_count"] == args.rows
    print(
        json.dumps(
            {
                "scope": "local single-process diagnostic; not a benchmark claim",
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "processor": platform.processor() or "not reported",
                "rows": args.rows,
                "csv_bytes": len(payload),
                "seed": args.seed,
                "timings": timings,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
