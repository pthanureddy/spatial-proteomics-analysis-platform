export interface Dataset {
  id: string;
  name: string;
  original_filename: string;
  row_count: number;
  created_at: string;
}

export interface PairMetric {
  protein_a: string;
  protein_b: string;
  observation_count: number;
  unique_cell_count: number;
  mean_score: number;
}

export interface ConditionMetric {
  observation_count: number;
  mean_score: number | null;
}

export interface PairComparison {
  protein_a: string;
  protein_b: string;
  condition_a: ConditionMetric;
  condition_b: ConditionMetric;
  count_delta: number;
  mean_score_delta: number | null;
}

export interface NetworkNode {
  protein: string;
  degree: number;
  observation_count: number;
  mean_score: number;
}

export interface NetworkEdge {
  source: string;
  target: string;
  observation_count: number;
  mean_score: number;
}

export interface Analysis {
  analysis_version: string;
  dataset_id: string;
  summary: {
    observation_count: number;
    unique_cell_count: number;
    unique_protein_count: number;
    conditions: string[];
  };
  pair_metrics: PairMetric[];
  comparison: {
    condition_a: string;
    condition_b: string;
    pairs: PairComparison[];
  } | null;
  network_nodes: NetworkNode[];
  network_edges: NetworkEdge[];
}

export interface CellPoint {
  cell_id: string;
  condition: string;
  x: number;
  y: number;
  observation_count: number;
  mean_score: number;
}

export interface CellPage {
  items: CellPoint[];
  total: number;
  limit: number;
  offset: number;
}

export interface CellDetail {
  cell_id: string;
  condition: string;
  x: number;
  y: number;
  observations: Array<{
    protein_a: string;
    protein_b: string;
    proximity_score: number;
  }>;
}

export interface UploadResult {
  dataset: Dataset;
  warnings: string[];
}
