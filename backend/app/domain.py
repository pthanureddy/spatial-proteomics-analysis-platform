from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProximityRecord:
    cell_id: str
    condition: str
    protein_a: str
    protein_b: str
    proximity_score: float
    x: float
    y: float
