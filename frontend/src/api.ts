import type {
  Analysis,
  CellDetail,
  CellPage,
  Dataset,
  UploadResult,
} from "./types";

interface ErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
    details?: Array<{ row?: number; field?: string; message?: string }>;
  };
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code: string,
  ) {
    super(message);
  }
}

async function jsonRequest<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    let payload: ErrorEnvelope = {};
    try {
      payload = (await response.json()) as ErrorEnvelope;
    } catch {
      // A proxy or network boundary may return a non-JSON error.
    }
    throw new ApiError(
      payload.error?.message || "The request could not be completed.",
      response.status,
      payload.error?.code || "request_failed",
    );
  }
  return (await response.json()) as T;
}

export function listDatasets(): Promise<Dataset[]> {
  return jsonRequest<Dataset[]>("/api/v1/datasets");
}

export function getDataset(datasetId: string): Promise<Dataset> {
  return jsonRequest<Dataset>(
    "/api/v1/datasets/" + encodeURIComponent(datasetId),
  );
}

export function getAnalysis(
  datasetId: string,
  conditionA?: string,
  conditionB?: string,
): Promise<Analysis> {
  const parameters = new URLSearchParams();
  if (conditionA && conditionB) {
    parameters.set("condition_a", conditionA);
    parameters.set("condition_b", conditionB);
  }
  const query = parameters.size ? "?" + parameters.toString() : "";
  return jsonRequest<Analysis>(
    "/api/v1/datasets/" + encodeURIComponent(datasetId) + "/analysis" + query,
  );
}

export function getCells(datasetId: string): Promise<CellPage> {
  return jsonRequest<CellPage>(
    "/api/v1/datasets/" + encodeURIComponent(datasetId) + "/cells?limit=500",
  );
}

export function getCell(
  datasetId: string,
  cellId: string,
): Promise<CellDetail> {
  return jsonRequest<CellDetail>(
    "/api/v1/datasets/" +
      encodeURIComponent(datasetId) +
      "/cells/" +
      encodeURIComponent(cellId),
  );
}

export function uploadDataset(
  name: string,
  filename: string,
  csv: string,
): Promise<UploadResult> {
  return jsonRequest<UploadResult>(
    "/api/v1/datasets?name=" + encodeURIComponent(name),
    {
      method: "POST",
      body: csv,
      headers: {
        "Content-Type": "text/csv",
        "X-Filename": filename,
      },
    },
  );
}

export async function loadBundledSample(): Promise<string> {
  const response = await fetch("/api/v1/sample.csv");
  if (!response.ok) {
    throw new ApiError(
      "The bundled sample could not be loaded.",
      response.status,
      "sample_unavailable",
    );
  }
  return response.text();
}

