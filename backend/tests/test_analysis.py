from __future__ import annotations

import pytest

from app.errors import AppError
from app.services.analysis import analyse_observations

ROWS = [
    {
        "cell_id": "cell-1",
        "condition": "control",
        "protein_a": "CD3",
        "protein_b": "CD4",
        "proximity_score": 0.4,
        "x": 1,
        "y": 2,
    },
    {
        "cell_id": "cell-2",
        "condition": "treated",
        "protein_a": "CD3",
        "protein_b": "CD4",
        "proximity_score": 0.8,
        "x": 3,
        "y": 4,
    },
    {
        "cell_id": "cell-2",
        "condition": "treated",
        "protein_a": "CD8",
        "protein_b": "PD1",
        "proximity_score": 0.6,
        "x": 3,
        "y": 4,
    },
]


def test_analysis_aggregates_pairs_and_condition_delta() -> None:
    result = analyse_observations("dataset-1", ROWS)

    assert result["summary"] == {
        "observation_count": 3,
        "unique_cell_count": 2,
        "unique_protein_count": 4,
        "conditions": ["control", "treated"],
    }
    assert result["pair_metrics"][0] == {
        "protein_a": "CD3",
        "protein_b": "CD4",
        "observation_count": 2,
        "unique_cell_count": 2,
        "mean_score": 0.6,
    }
    comparison = result["comparison"]
    assert comparison is not None
    assert comparison["condition_a"] == "control"
    assert comparison["condition_b"] == "treated"
    assert comparison["pairs"][0]["count_delta"] == 0
    assert comparison["pairs"][0]["mean_score_delta"] == 0.4
    assert comparison["pairs"][1]["mean_score_delta"] is None


def test_network_metrics_are_undirected_and_deterministic() -> None:
    result = analyse_observations("dataset-1", list(reversed(ROWS)))

    assert [node["protein"] for node in result["network_nodes"]] == [
        "CD3",
        "CD4",
        "CD8",
        "PD1",
    ]
    assert result["network_nodes"][0] == {
        "protein": "CD3",
        "degree": 1,
        "observation_count": 2,
        "mean_score": 0.6,
    }
    assert result["network_edges"][0]["source"] == "CD3"


def test_explicit_condition_order_controls_delta_direction() -> None:
    result = analyse_observations(
        "dataset-1",
        ROWS,
        condition_a="treated",
        condition_b="control",
    )
    comparison = result["comparison"]
    assert comparison is not None
    assert comparison["pairs"][0]["mean_score_delta"] == -0.4


@pytest.mark.parametrize(
    ("condition_a", "condition_b", "error_code"),
    [
        ("control", None, "invalid_condition_selection"),
        ("missing", "treated", "unknown_condition"),
        ("control", "control", "invalid_condition_selection"),
    ],
)
def test_invalid_condition_selection_is_rejected(
    condition_a: str | None,
    condition_b: str | None,
    error_code: str,
) -> None:
    with pytest.raises(AppError) as exc_info:
        analyse_observations(
            "dataset-1",
            ROWS,
            condition_a=condition_a,
            condition_b=condition_b,
        )
    assert exc_info.value.code == error_code
