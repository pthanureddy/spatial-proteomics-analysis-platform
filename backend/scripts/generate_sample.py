from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

PROTEINS = ("CD3", "CD4", "CD8", "PD1", "PDL1", "CD28")
PAIRS = tuple(
    (left, right)
    for index, left in enumerate(PROTEINS)
    for right in PROTEINS[index + 1 :]
)


def generate(*, cells_per_condition: int, seed: int) -> list[dict[str, object]]:
    randomizer = random.Random(seed)
    rows: list[dict[str, object]] = []
    for condition_index, condition in enumerate(("control", "treated")):
        for cell_offset in range(cells_per_condition):
            cell_number = condition_index * cells_per_condition + cell_offset + 1
            cell_id = f"cell_{cell_number:04d}"
            x = round(randomizer.uniform(0, 100), 2)
            y = round(randomizer.uniform(0, 100), 2)
            selected_pairs = randomizer.sample(PAIRS, k=4)
            for protein_a, protein_b in sorted(selected_pairs):
                shift = 0.12 if condition == "treated" and "PD1" in (
                    protein_a,
                    protein_b,
                ) else 0
                score = min(
                    1,
                    max(0, randomizer.betavariate(2.4, 3.2) + shift),
                )
                rows.append(
                    {
                        "cell_id": cell_id,
                        "condition": condition,
                        "protein_a": protein_a,
                        "protein_b": protein_b,
                        "proximity_score": f"{score:.4f}",
                        "x": f"{x:.2f}",
                        "y": f"{y:.2f}",
                    }
                )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic synthetic proximity edge list."
    )
    parser.add_argument("--cells-per-condition", type=int, default=50)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.cells_per_condition <= 0:
        parser.error("--cells-per-condition must be positive")

    rows = generate(
        cells_per_condition=args.cells_per_condition,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
