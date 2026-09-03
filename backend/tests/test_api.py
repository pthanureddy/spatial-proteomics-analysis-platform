from __future__ import annotations

from fastapi.testclient import TestClient


def upload(client: TestClient, content: bytes, name: str = "Test run"):
    return client.post(
        "/api/v1/datasets",
        params={"name": name},
        content=content,
        headers={"content-type": "text/csv", "x-filename": "edges.csv"},
    )


def test_health_reports_database_reachability(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}
    assert response.headers["x-request-id"]


def test_dataset_upload_list_detail_and_analysis(
    client: TestClient, valid_csv: bytes
) -> None:
    created = upload(client, valid_csv)

    assert created.status_code == 201
    payload = created.json()
    dataset_id = payload["dataset"]["id"]
    assert payload["dataset"]["row_count"] == 3
    assert payload["dataset"]["original_filename"] == "edges.csv"

    listing = client.get("/api/v1/datasets")
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [dataset_id]

    detail = client.get(f"/api/v1/datasets/{dataset_id}")
    assert detail.status_code == 200
    assert detail.json()["name"] == "Test run"

    analysis = client.get(f"/api/v1/datasets/{dataset_id}/analysis")
    assert analysis.status_code == 200
    assert analysis.json()["summary"]["observation_count"] == 3
    assert (
        analysis.json()["comparison"]["pairs"][0]["mean_score_delta"] == 0.4
    )

    cells = client.get(f"/api/v1/datasets/{dataset_id}/cells", params={"limit": 1})
    assert cells.status_code == 200
    assert cells.json()["total"] == 2
    assert cells.json()["items"][0] == {
        "cell_id": "cell-1",
        "condition": "control",
        "x": 1.0,
        "y": 2.0,
        "observation_count": 1,
        "mean_score": 0.4,
    }

    cell = client.get(f"/api/v1/datasets/{dataset_id}/cells/cell-2")
    assert cell.status_code == 200
    assert cell.json()["condition"] == "treated"
    assert len(cell.json()["observations"]) == 2


def test_upload_returns_structured_validation_errors(client: TestClient) -> None:
    response = upload(
        client,
        b"""cell_id,condition,protein_a,protein_b,proximity_score,x,y
cell-1,control,CD3,CD3,not-a-number,-1,2
""",
    )

    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "invalid_csv"
    assert {detail["field"] for detail in body["details"]} == {
        "protein_b",
        "proximity_score",
        "x",
    }


def test_upload_requires_csv_content_type(
    client: TestClient, valid_csv: bytes
) -> None:
    response = client.post(
        "/api/v1/datasets",
        params={"name": "No media type"},
        content=valid_csv,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


def test_upload_size_limit_is_enforced(client: TestClient) -> None:
    response = upload(client, b"x" * 10_001)

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "upload_too_large"


def test_unknown_dataset_returns_structured_404(client: TestClient) -> None:
    response = client.get("/api/v1/datasets/does-not-exist/analysis")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "dataset_not_found"


def test_unknown_cell_returns_structured_404(
    client: TestClient, valid_csv: bytes
) -> None:
    created = upload(client, valid_csv).json()
    dataset_id = created["dataset"]["id"]
    response = client.get(f"/api/v1/datasets/{dataset_id}/cells/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "cell_not_found"


def test_sample_csv_matches_the_ingestion_contract(client: TestClient) -> None:
    sample = client.get("/api/v1/sample.csv")
    assert sample.status_code == 200
    assert sample.headers["content-type"].startswith("text/csv")

    created = upload(client, sample.content, name="Bundled sample")
    assert created.status_code == 201
    assert created.json()["dataset"]["row_count"] == 16
