from __future__ import annotations

from pathlib import PurePath

from fastapi import APIRouter, Query, Request, Response

from app.database import Database
from app.errors import AppError, DatasetNotFoundError
from app.sample_data import SAMPLE_CSV
from app.schemas import (
    AnalysisResponse,
    CellDetail,
    CellPage,
    DatasetSummary,
    HealthResponse,
    UploadResponse,
)
from app.services.analysis import analyse_observations
from app.services.csv_validation import validate_csv

router = APIRouter()


def _database(request: Request) -> Database:
    return request.app.state.database


async def _bounded_body(request: Request) -> bytes:
    chunks: list[bytes] = []
    total = 0
    limit: int = request.app.state.settings.max_upload_bytes
    async for chunk in request.stream():
        total += len(chunk)
        if total > limit:
            raise AppError(
                status_code=413,
                code="upload_too_large",
                message=f"CSV uploads are limited to {limit} bytes.",
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(request: Request) -> HealthResponse:
    _database(request).ping()
    return HealthResponse(status="ok", database="reachable")


@router.get(
    "/sample.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
    tags=["datasets"],
)
def sample_csv() -> Response:
    return Response(
        content=SAMPLE_CSV,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="synthetic-sample.csv"'},
    )


@router.post(
    "/datasets",
    response_model=UploadResponse,
    status_code=201,
    tags=["datasets"],
)
async def create_dataset(
    request: Request,
    name: str = Query(min_length=1, max_length=120),
) -> UploadResponse:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
    if content_type not in {"text/csv", "application/csv", "text/plain"}:
        raise AppError(
            status_code=415,
            code="unsupported_media_type",
            message="Send the CSV as a text/csv request body.",
        )
    body = await _bounded_body(request)
    result = validate_csv(body, max_rows=request.app.state.settings.max_rows)
    supplied_filename = request.headers.get("x-filename", "upload.csv")
    filename = PurePath(supplied_filename.replace("\\", "/")).name[:255] or "upload.csv"
    dataset = _database(request).create_dataset(
        name=name.strip(),
        original_filename=filename,
        records=result.records,
    )
    return UploadResponse(
        dataset=DatasetSummary.model_validate(dataset),
        warnings=list(result.warnings),
    )


@router.get(
    "/datasets",
    response_model=list[DatasetSummary],
    tags=["datasets"],
)
def list_datasets(request: Request) -> list[DatasetSummary]:
    return [
        DatasetSummary.model_validate(item)
        for item in _database(request).list_datasets()
    ]


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetSummary,
    tags=["datasets"],
)
def get_dataset(dataset_id: str, request: Request) -> DatasetSummary:
    dataset = _database(request).get_dataset(dataset_id)
    if dataset is None:
        raise DatasetNotFoundError(dataset_id)
    return DatasetSummary.model_validate(dataset)


@router.get(
    "/datasets/{dataset_id}/analysis",
    response_model=AnalysisResponse,
    tags=["analysis"],
)
def get_analysis(
    dataset_id: str,
    request: Request,
    condition_a: str | None = None,
    condition_b: str | None = None,
) -> AnalysisResponse:
    database = _database(request)
    if database.get_dataset(dataset_id) is None:
        raise DatasetNotFoundError(dataset_id)
    analysis = analyse_observations(
        dataset_id,
        database.get_observations(dataset_id),
        condition_a=condition_a,
        condition_b=condition_b,
    )
    return AnalysisResponse.model_validate(analysis)


@router.get(
    "/datasets/{dataset_id}/cells",
    response_model=CellPage,
    tags=["spatial"],
)
def list_cells(
    dataset_id: str,
    request: Request,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> CellPage:
    database = _database(request)
    if database.get_dataset(dataset_id) is None:
        raise DatasetNotFoundError(dataset_id)
    total, cells = database.list_cells(dataset_id, limit=limit, offset=offset)
    return CellPage.model_validate(
        {"items": cells, "total": total, "limit": limit, "offset": offset}
    )


@router.get(
    "/datasets/{dataset_id}/cells/{cell_id}",
    response_model=CellDetail,
    tags=["spatial"],
)
def get_cell(dataset_id: str, cell_id: str, request: Request) -> CellDetail:
    database = _database(request)
    if database.get_dataset(dataset_id) is None:
        raise DatasetNotFoundError(dataset_id)
    cell = database.get_cell(dataset_id, cell_id)
    if cell is None:
        raise AppError(
            status_code=404,
            code="cell_not_found",
            message=f"Cell '{cell_id}' was not found in this dataset.",
        )
    return CellDetail.model_validate(cell)
