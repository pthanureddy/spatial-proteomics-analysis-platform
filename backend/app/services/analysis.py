from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from app.errors import AppError


@dataclass(slots=True)
class Aggregate:
    count: int = 0
    score_sum: float = 0
    cells: set[str] = field(default_factory=set)

    def add(self, *, score: float, cell_id: str) -> None:
        self.count += 1
        self.score_sum += score
        self.cells.add(cell_id)

    @property
    def mean(self) -> float:
        return self.score_sum / self.count


def _rounded(value: float) -> float:
    return round(value, 6)


def analyse_observations(
    dataset_id: str,
    rows: list[dict[str, Any]],
    *,
    condition_a: str | None = None,
    condition_b: str | None = None,
) -> dict[str, Any]:
    pairs: dict[tuple[str, str], Aggregate] = defaultdict(Aggregate)
    conditional_pairs: dict[
        str, dict[tuple[str, str], Aggregate]
    ] = defaultdict(lambda: defaultdict(Aggregate))
    cells: set[str] = set()
    proteins: set[str] = set()

    for row in rows:
        pair = (str(row["protein_a"]), str(row["protein_b"]))
        score = float(row["proximity_score"])
        cell_id = str(row["cell_id"])
        condition = str(row["condition"])
        pairs[pair].add(score=score, cell_id=cell_id)
        conditional_pairs[condition][pair].add(score=score, cell_id=cell_id)
        cells.add(cell_id)
        proteins.update(pair)

    conditions = sorted(conditional_pairs)
    if (condition_a is None) != (condition_b is None):
        raise AppError(
            status_code=422,
            code="invalid_condition_selection",
            message="Provide both condition_a and condition_b, or neither.",
        )
    if condition_a is None and len(conditions) >= 2:
        condition_a, condition_b = conditions[:2]
    if condition_a is not None and condition_b is not None:
        unknown = [
            value for value in (condition_a, condition_b) if value not in conditions
        ]
        if unknown:
            raise AppError(
                status_code=422,
                code="unknown_condition",
                message=f"Unknown condition: {', '.join(sorted(set(unknown)))}.",
            )
        if condition_a == condition_b:
            raise AppError(
                status_code=422,
                code="invalid_condition_selection",
                message="condition_a and condition_b must be different.",
            )

    pair_metrics = [
        {
            "protein_a": pair[0],
            "protein_b": pair[1],
            "observation_count": aggregate.count,
            "unique_cell_count": len(aggregate.cells),
            "mean_score": _rounded(aggregate.mean),
        }
        for pair, aggregate in sorted(pairs.items())
    ]

    comparison: dict[str, Any] | None = None
    if condition_a is not None and condition_b is not None:
        comparison_pairs = []
        all_pairs = sorted(
            set(conditional_pairs[condition_a])
            | set(conditional_pairs[condition_b])
        )
        for pair in all_pairs:
            left = conditional_pairs[condition_a].get(pair)
            right = conditional_pairs[condition_b].get(pair)
            left_mean = _rounded(left.mean) if left else None
            right_mean = _rounded(right.mean) if right else None
            comparison_pairs.append(
                {
                    "protein_a": pair[0],
                    "protein_b": pair[1],
                    "condition_a": {
                        "observation_count": left.count if left else 0,
                        "mean_score": left_mean,
                    },
                    "condition_b": {
                        "observation_count": right.count if right else 0,
                        "mean_score": right_mean,
                    },
                    "count_delta": (right.count if right else 0)
                    - (left.count if left else 0),
                    "mean_score_delta": (
                        _rounded(right.mean - left.mean) if left and right else None
                    ),
                }
            )
        comparison = {
            "condition_a": condition_a,
            "condition_b": condition_b,
            "pairs": comparison_pairs,
        }

    neighbours: dict[str, set[str]] = defaultdict(set)
    node_counts: dict[str, int] = defaultdict(int)
    node_score_sums: dict[str, float] = defaultdict(float)
    network_edges = []
    for pair, aggregate in sorted(pairs.items()):
        source, target = pair
        neighbours[source].add(target)
        neighbours[target].add(source)
        for protein in pair:
            node_counts[protein] += aggregate.count
            node_score_sums[protein] += aggregate.score_sum
        network_edges.append(
            {
                "source": source,
                "target": target,
                "observation_count": aggregate.count,
                "mean_score": _rounded(aggregate.mean),
            }
        )

    network_nodes = [
        {
            "protein": protein,
            "degree": len(neighbours[protein]),
            "observation_count": node_counts[protein],
            "mean_score": _rounded(node_score_sums[protein] / node_counts[protein]),
        }
        for protein in sorted(proteins)
    ]

    return {
        "analysis_version": "1.0",
        "dataset_id": dataset_id,
        "summary": {
            "observation_count": len(rows),
            "unique_cell_count": len(cells),
            "unique_protein_count": len(proteins),
            "conditions": conditions,
        },
        "pair_metrics": pair_metrics,
        "comparison": comparison,
        "network_nodes": network_nodes,
        "network_edges": network_edges,
    }
