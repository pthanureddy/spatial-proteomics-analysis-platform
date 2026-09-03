from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DatasetSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    original_filename: str
    row_count: int = Field(gt=0)
    created_at: datetime


class UploadResponse(BaseModel):
    dataset: DatasetSummary
    warnings: list[str]


class SummaryMetrics(BaseModel):
    observation_count: int
    unique_cell_count: int
    unique_protein_count: int
    conditions: list[str]


class PairMetric(BaseModel):
    protein_a: str
    protein_b: str
    observation_count: int
    unique_cell_count: int
    mean_score: float


class ConditionMetric(BaseModel):
    observation_count: int
    mean_score: float | None


class PairComparison(BaseModel):
    protein_a: str
    protein_b: str
    condition_a: ConditionMetric
    condition_b: ConditionMetric
    count_delta: int
    mean_score_delta: float | None


class NetworkNode(BaseModel):
    protein: str
    degree: int
    observation_count: int
    mean_score: float


class NetworkEdge(BaseModel):
    source: str
    target: str
    observation_count: int
    mean_score: float


class ConditionComparison(BaseModel):
    condition_a: str
    condition_b: str
    pairs: list[PairComparison]


class AnalysisResponse(BaseModel):
    analysis_version: str
    dataset_id: str
    summary: SummaryMetrics
    pair_metrics: list[PairMetric]
    comparison: ConditionComparison | None
    network_nodes: list[NetworkNode]
    network_edges: list[NetworkEdge]


class CellPoint(BaseModel):
    cell_id: str
    condition: str
    x: float
    y: float
    observation_count: int
    mean_score: float


class CellPage(BaseModel):
    items: list[CellPoint]
    total: int
    limit: int
    offset: int


class CellObservation(BaseModel):
    protein_a: str
    protein_b: str
    proximity_score: float


class CellDetail(BaseModel):
    cell_id: str
    condition: str
    x: float
    y: float
    observations: list[CellObservation]


class HealthResponse(BaseModel):
    status: str
    database: str
